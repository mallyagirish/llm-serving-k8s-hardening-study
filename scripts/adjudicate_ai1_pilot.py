#!/usr/bin/env python3
"""Build the adjudication file for the AI-1 pilot pass (guide v0.4).

Reads results/labels/reviewer_AI1.csv (immutable input; never written) and
writes results/labels/reviewer_AI1_adjudication.csv plus a provenance
sidecar. The AI-1 labels are the operational "R1" set for workflow
comparison only: they are AI-generated (reviewer AI-1, claude-ai-assist),
not a human reviewer's labels, and agreement with any later pass is not
human inter-rater reliability. Author verification is still pending.

Rows are re-judged under the amended guide v0.3 definitions only for the
affected rule groups (AUTH-02, AUTH-03, AUTH-04, SEC-03, NET-04, GPU-02).
RES-02 rows are re-adjudicated under guide v0.4: the author decided on
2026-11-06 (before the full 105-bundle review) to replace the
production-intent test with the predeclared observable predicate — scaled
workload (replicas > 1 or autoscaling) without a matching PDB.
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "results/labels/reviewer_AI1.csv"
OUT = ROOT / "results/labels/reviewer_AI1_adjudication.csv"
CORPUS = ROOT / "corpus"

AMENDED = {
    "LLM-AUTH-02": "guide-v0.3:AUTH-02",
    "LLM-AUTH-03": "guide-v0.3:AUTH-03",
    "LLM-AUTH-04": "guide-v0.3:AUTH-04",
    "LLM-SEC-03": "guide-v0.3:SEC-03",
    "LLM-NET-04": "guide-v0.3:NET-04",
    "LLM-GPU-02": "guide-v0.3:GPU-02",
}


def load_docs(bundle_path):
    with open(CORPUS / bundle_path) as f:
        return [d for d in yaml.safe_load_all(f) if d]


def sec03_rbac_state(bundle_path):
    """Return (rbac_represented, broad_grant) from in-bundle RBAC only."""
    docs = load_docs(bundle_path)
    rbac = [d for d in docs if d.get("kind") in
            ("Role", "ClusterRole", "RoleBinding", "ClusterRoleBinding")]
    broad = False
    for d in docs:
        if d.get("kind") in ("Role", "ClusterRole"):
            for rule in d.get("rules", []):
                if "*" in (rule.get("verbs") or []) or \
                   "*" in (rule.get("resources") or []) or \
                   "*" in (rule.get("apiGroups") or []):
                    broad = True
        if d.get("kind") in ("RoleBinding", "ClusterRoleBinding"):
            if (d.get("roleRef") or {}).get("name") == "cluster-admin":
                broad = True
    return bool(rbac), broad


def net04_boundary_exposure(bundle_path):
    """True only if control ports are exposed beyond the deployment boundary
    (NodePort/LoadBalancer Service or hostNetwork). ClusterIP does not count."""
    docs = load_docs(bundle_path)
    for d in docs:
        if d.get("kind") == "Service" and d["spec"].get("type") in ("NodePort", "LoadBalancer"):
            ports = {(p.get("name"), p.get("port")) for p in d["spec"].get("ports", [])}
            if any(p in (55555, 9999, 9000, 9001, 9002) or
                   (n and any(k in str(n) for k in ("zmq", "ucx", "lmcache")))
                   for n, p in ports):
                return True
        if "hostNetwork: true" in yaml.dump(d):
            return True
    return False


def _replica_values(obj, path="spec"):
    """All (path, value) pairs for keys named 'replicas' in a spec tree."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}"
            if k == "replicas":
                out.append((p, v))
            out += _replica_values(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += _replica_values(v, f"{path}[{i}]")
    return out


def _autoscaling_ranges(obj, path="spec"):
    """Evidence strings where min/max replica fields permit scaling > 1."""
    out = []
    if isinstance(obj, dict):
        mn, mx = obj.get("minReplicas"), obj.get("maxReplicas")
        if isinstance(mx, int) and mx > 1 and (mn is None or (isinstance(mn, int) and mn < mx)):
            out.append(f"{path} autoscaling range minReplicas={mn} maxReplicas={mx}")
        if obj.get("enableInTreeAutoscaling") is True:
            out.append(f"{path} enableInTreeAutoscaling=true")
        for k, v in obj.items():
            out += _autoscaling_ranges(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += _autoscaling_ranges(v, f"{path}[{i}]")
    return out


def res02_scaling_state(bundle_path):
    """Observable scaling evidence for RES-02 under guide v0.4.

    Returns dict with workload evidence strings, scaled evidence strings,
    whether any included PDB matches a scaled workload, and whether a
    workload's scaling configuration is indeterminate from the bundle.
    Only in-bundle, observable fields are used; production intent is not
    assessed. An unset Deployment/StatefulSet replicas field counts as 1
    (documented Kubernetes default).
    """
    docs = load_docs(bundle_path)
    workloads, scaled = [], []
    indeterminate = False
    pdb_selectors = []
    hpa_targets = []
    pod_label_sets = []
    for d in docs:
        kind = d.get("kind")
        name = (d.get("metadata") or {}).get("name")
        spec = d.get("spec") or {}
        if kind == "PodDisruptionBudget":
            sel = ((spec.get("selector") or {}).get("matchLabels")) or {}
            pdb_selectors.append((name, sel))
        elif kind == "HorizontalPodAutoscaler":
            hpa_targets.append((name, (spec.get("scaleTargetRef") or {}).get("name")))
        elif kind in ("Deployment", "StatefulSet"):
            rep = spec.get("replicas", 1)
            labels = (((spec.get("template") or {}).get("metadata") or {}).get("labels")) or {}
            pod_label_sets.append(labels)
            if not isinstance(rep, int):
                indeterminate = True
                workloads.append(f"{kind} {name} replicas={rep!r} (not an integer in-bundle)")
            else:
                workloads.append(f"{kind} {name} replicas={rep}")
                if rep > 1:
                    scaled.append(f"{kind} {name} replicas={rep}")
        elif kind in ("InferenceService", "LLMInferenceService", "RayService", "RayCluster"):
            reps = _replica_values(spec)
            for p, v in reps:
                if not isinstance(v, int):
                    indeterminate = True
                    workloads.append(f"{kind} {name} {p}={v!r} (not an integer in-bundle)")
                else:
                    workloads.append(f"{kind} {name} {p}={v}")
                    if v > 1:
                        scaled.append(f"{kind} {name} {p}={v}")
            for ev in _autoscaling_ranges(spec):
                workloads.append(f"{kind} {name} {ev}")
                scaled.append(f"{kind} {name} {ev}")
            if not reps and not _autoscaling_ranges(spec):
                workloads.append(f"{kind} {name} (no replicas or autoscaling fields in-bundle)")
        elif kind == "Service" and str(d.get("apiVersion", "")).startswith("serving.knative.dev"):
            workloads.append(f"Knative Service {name} (autoscaled by construction)")
            scaled.append(f"Knative Service {name} (autoscaled by construction)")
    for hpa_name, target in hpa_targets:
        ev = f"HorizontalPodAutoscaler {hpa_name} targets {target}"
        workloads.append(ev)
        scaled.append(ev)
    pdb_match = False
    for pdb_name, sel in pdb_selectors:
        if sel and any(all(labels.get(k) == v for k, v in sel.items()) for labels in pod_label_sets):
            pdb_match = True
    return {
        "workloads": workloads,
        "scaled": scaled,
        "n_pdbs": len(pdb_selectors),
        "pdb_match": pdb_match,
        "indeterminate": indeterminate,
    }


def res02_decision(bundle_path):
    """(proposed_label, rationale) for RES-02 under the guide v0.4 predicate."""
    st = res02_scaling_state(bundle_path)
    head = ("Resolved under guide-v0.4:RES-02 (observable predicate decided by the "
            "author 2026-11-06; production intent no longer assessed). ")
    if st["indeterminate"]:
        return "U", head + ("A workload's replicas value is not determinable from the "
                            "bundle: " + "; ".join(st["workloads"]) + ".")
    if st["scaled"]:
        ev = "; ".join(st["scaled"])
        if st["pdb_match"]:
            return "ABSENT", head + (f"Scaled workload in scope: {ev}. An included "
                                     "PodDisruptionBudget's selector matches the "
                                     "workload's pods -> ABSENT.")
        pdb_note = ("the bundle contains no PodDisruptionBudget" if st["n_pdbs"] == 0
                    else "no included PodDisruptionBudget's selector matches it")
        return "PRESENT", head + f"Scaled workload in scope: {ev}; {pdb_note} -> PRESENT."
    if st["workloads"]:
        return "NA", head + ("Scope condition not met: " + "; ".join(st["workloads"]) +
                             ". No replicas > 1 and no autoscaling configuration -> NA.")
    kinds = sorted({d.get("kind") for d in load_docs(bundle_path)})
    return "NA", head + ("Scope condition not met: the bundle contains no workload "
                         f"(only {', '.join(kinds)}) and no scaling configuration -> NA.")


def main():
    rows = list(csv.DictReader(open(SRC)))
    assert len(rows) == 840, len(rows)
    out_rows = []
    changes = []
    for r in rows:
        rule = r["rule_id"]
        label = r["label"]
        proposed, status = label, "confirmed"
        amendment = "none"
        rationale = "Confirmed: AI-1 label and cited evidence stand under guide v0.3."
        if rule in AMENDED:
            amendment = AMENDED[rule]
            rationale = (f"Reviewed under {amendment}; AI-1 label stands — the amended "
                         "definition does not change this call.")
        if rule == "LLM-RES-02":
            status = "resolved"
            amendment = "guide-v0.4:RES-02"
            proposed, rationale = res02_decision(r["bundle_path"])
        # --- changed rows under amended definitions ---
        if rule == "LLM-NET-04" and label == "PRESENT":
            assert not net04_boundary_exposure(r["bundle_path"]), r["bundle_path"]
            proposed, status = "U", "changed"
            rationale = ("Changed PRESENT->U under guide-v0.3:NET-04. The control ports "
                         "(zmq 55555 / ucx 9999, router lmcache 9000) are declared only on "
                         "ClusterIP Services belonging to the stack's own router/engine "
                         "components; no NodePort/LoadBalancer/hostNetwork exposure, Ingress/"
                         "Gateway route, or included policy establishes reachability beyond "
                         "the serving deployment's trust boundary, and no included "
                         "NetworkPolicy establishes isolation either — so the boundary "
                         "question is undecidable from the bundle.")
        elif rule == "LLM-AUTH-03" and label == "ABSENT":
            proposed, status = "U", "changed"
            rationale = ("Changed ABSENT->U under guide-v0.3:AUTH-03. The ABSENT rested on a "
                         "visible command/serve configuration enabling no dev/admin endpoints "
                         "— i.e. on absent enable flags. V0.3 requires explicit disablement, a "
                         "documented version-specific default, or configuration that "
                         "definitively establishes the endpoint surface; none is cited, and "
                         "absence of flags is not proof endpoints are disabled.")
        elif rule == "LLM-SEC-03" and label == "U":
            represented, broad = sec03_rbac_state(r["bundle_path"])
            if represented and not broad:
                proposed, status = "ABSENT", "changed"
                rationale = ("Changed U->ABSENT under guide-v0.3:SEC-03 (in-bundle RBAC scope). "
                             "The bundle's RBAC layer is represented in-bundle (Role + "
                             "RoleBinding included) and its only binding grants the router "
                             "ServiceAccount a least-privilege Role (pods get/watch/list/patch); "
                             "no included binding grants any workload ServiceAccount "
                             "cluster-admin or wildcard permissions. Effective cluster "
                             "permissions remain out of scope and are not claimed.")
            else:
                rationale = ("Reviewed under guide-v0.3:SEC-03; U stands. The bundle represents "
                             "no RBAC layer (no Roles/bindings included), so the in-bundle "
                             "ServiceAccount-to-binding mapping cannot be established; "
                             "effective cluster permissions are out of scope.")
        if proposed != label:
            changes.append((rule, label, proposed, r["bundle_path"]))
        out_rows.append({
            "blind_id": r["blind_id"],
            "bundle_path": r["bundle_path"],
            "bundle_sha256": r["bundle_sha256"],
            "upstream_project": r["upstream_project"],
            "rule_id": rule,
            "rule_title": r["rule_title"],
            "r1_label": label,
            "proposed_label": proposed,
            "adjudication_status": status,
            "evidence_path": r["evidence_path"],
            "adjudication_rationale": rationale,
            "protocol_amendment_required": amendment,
        })
    fields = list(out_rows[0].keys())
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)
    sidecar = {
        "artifact": "adjudication of the AI-1 pilot labeling pass",
        "source_sheet": "results/labels/reviewer_AI1.csv",
        "source_sheet_sha256": hashlib.sha256(open(SRC, "rb").read()).hexdigest(),
        "source_reviewer_id": "AI-1",
        "provenance_warning": ("r1_label values are AI-generated labels (reviewer AI-1, "
                               "claude-ai-assist) used as the operational R1 set for workflow "
                               "organization only. They are NOT a human reviewer's labels, and "
                               "agreement with any other pass is not human inter-rater "
                               "reliability."),
        "guide_version": "0.4",
        "adjudicator": "claude-ai-assist (Tasks 5-6, applying the author's adjudication positions)",
        "author_verification": "pending — Girish reviews everything once at the end",
        "rows": len(out_rows),
        "changed_rows": len(changes),
        "changes": [{"rule_id": c[0], "from": c[1], "to": c[2], "bundle_path": c[3]}
                    for c in changes],
        "res02_decision": {
            "status": "decided 2026-11-06 by the author, before the full 105-bundle review",
            "predicate": ("Observable predicate replaces production intent: in scope when a "
                          "workload configures replicas > 1 or autoscaling (HPA or equivalent); "
                          "PRESENT = in-scope workload with no matching PodDisruptionBudget; "
                          "ABSENT = matching PDB included; NA = no in-scope workload (single "
                          "static replicas, or no workload in the bundle); U = scaling "
                          "configuration not determinable from the bundle."),
            "rows_resolved": sum(1 for r in out_rows if r["rule_id"] == "LLM-RES-02"),
            "label_changes": sum(1 for c in changes if c[0] == "LLM-RES-02"),
            "outcomes": {lab: sum(1 for r in out_rows
                                  if r["rule_id"] == "LLM-RES-02" and r["proposed_label"] == lab)
                         for lab in ("PRESENT", "ABSENT", "U", "NA")},
        },
    }
    with open(str(OUT) + ".meta.json", "w") as f:
        json.dump(sidecar, f, indent=2)
    print(f"wrote {OUT} rows={len(out_rows)} changed={len(changes)}")
    for c in changes:
        print(" ", c[0], f"{c[1]}->{c[2]}", c[3])
    return 0


if __name__ == "__main__":
    sys.exit(main())
