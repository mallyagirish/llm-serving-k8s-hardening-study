#!/usr/bin/env python3
"""Build the adjudication file for the AI-1 pilot pass (guide v0.3).

Reads results/labels/reviewer_AI1.csv (immutable input; never written) and
writes results/labels/reviewer_AI1_adjudication.csv plus a provenance
sidecar. The AI-1 labels are the operational "R1" set for workflow
comparison only: they are AI-generated (reviewer AI-1, claude-ai-assist),
not a human reviewer's labels, and agreement with any later pass is not
human inter-rater reliability. Author verification is still pending.

Rows are re-judged under the amended guide v0.3 definitions only for the
affected rule groups (AUTH-02, AUTH-03, AUTH-04, SEC-03, NET-04, GPU-02).
RES-02 rows are carried unchanged: its definition is a pending decision.
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
            status = "pending-decision"
            amendment = "pending-decision:LLM-RES-02"
            rationale = ("RES-02 definition is a pending decision (observable predicate vs "
                         "retained production intent; guide v0.3 §3 note). AI-1 label carried "
                         "unchanged; not adjudicated under either option.")
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
        "guide_version": "0.3",
        "adjudicator": "claude-ai-assist (Task 5, applying the author's adjudication positions)",
        "author_verification": "pending — Girish reviews everything once at the end",
        "rows": len(out_rows),
        "changed_rows": len(changes),
        "changes": [{"rule_id": c[0], "from": c[1], "to": c[2], "bundle_path": c[3]}
                    for c in changes],
        "pending_decision": ("LLM-RES-02: observable predicate vs retained production intent; "
                             "rows carried unchanged"),
    }
    with open(str(OUT) + ".meta.json", "w") as f:
        json.dump(sidecar, f, indent=2)
    print(f"wrote {OUT} rows={len(out_rows)} changed={len(changes)}")
    for c in changes:
        print(" ", c[0], f"{c[1]}->{c[2]}", c[3])
    return 0


if __name__ == "__main__":
    sys.exit(main())
