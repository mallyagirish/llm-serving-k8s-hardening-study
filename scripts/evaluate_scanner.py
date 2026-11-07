#!/usr/bin/env python3
"""Reproducible bundle-level scanner comparison and descriptive prevalence.

The scanner emits review candidates, not exploitability judgments. A candidate
is aggregated to one binary prediction per (bundle, rule). Reference labels
PRESENT/ABSENT are used for confusion matrices; U and NA are excluded and
reported separately. Outputs are descriptive for this pinned public corpus.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "1.0.0"
SCANNER_RULES = {
    "LLM-NET-01", "LLM-NET-03", "LLM-NET-05", "LLM-SEC-02",
    "LLM-GPU-01", "LLM-GPU-03", "LLM-WL-01", "LLM-WL-02",
    "LLM-WL-03", "LLM-WL-04", "LLM-WL-05", "LLM-RES-01",
    "LLM-RES-03",
}
LABELS = {"PRESENT", "ABSENT", "U", "NA"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def norm_bundle_path(value: str) -> str:
    value = Path(value).as_posix().lstrip("./")
    while value.startswith("corpus/"):
        value = value[len("corpus/"):]
    return value


def safe_div(n: int | float, d: int | float) -> float | None:
    return n / d if d else None


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", required=True, type=Path)
    ap.add_argument("--candidates", required=True, type=Path)
    ap.add_argument("--inventory", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    args = ap.parse_args()

    labels = read_csv(args.labels)
    candidates = read_jsonl(args.candidates)
    inventory = read_jsonl(args.inventory)
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    required = {"bundle_path", "bundle_sha256", "upstream_project", "rule_id", "label"}
    if not labels or not required.issubset(labels[0]):
        raise ValueError(f"labels CSV must contain columns: {sorted(required)}")
    if not inventory:
        raise ValueError("inventory JSONL is empty")

    label_by_key: dict[tuple[str, str], dict[str, str]] = {}
    bundles: dict[str, dict[str, str]] = {}
    projects: dict[str, str] = {}
    for row in labels:
        path = norm_bundle_path(row["bundle_path"])
        rule = row["rule_id"]
        label = row["label"]
        if label not in LABELS:
            raise ValueError(f"invalid label {label!r} for {path} {rule}")
        key = (path, rule)
        if key in label_by_key:
            raise ValueError(f"duplicate bundle-rule label: {key}")
        label_by_key[key] = row
        if path in bundles and bundles[path]["bundle_sha256"] != row["bundle_sha256"]:
            raise ValueError(f"inconsistent bundle hash across labels: {path}")
        bundles[path] = {"bundle_sha256": row["bundle_sha256"]}
        if path in projects and projects[path] != row["upstream_project"]:
            raise ValueError(f"inconsistent project mapping: {path}")
        projects[path] = row["upstream_project"]

    expected_rules = {row["rule_id"] for row in labels}
    if len(bundles) * len(expected_rules) != len(labels):
        raise ValueError("label matrix is not rectangular (bundle count x rule count)")
    for bundle in bundles:
        missing = expected_rules - {r for (p, r) in label_by_key if p == bundle}
        if missing:
            raise ValueError(f"missing rule labels for {bundle}: {sorted(missing)}")
    if not SCANNER_RULES.issubset(expected_rules):
        raise ValueError("one or more scanner rules are absent from the reference label matrix")

    inv_by_path = {}
    for item in inventory:
        path = norm_bundle_path(str(item.get("path", "")))
        if path:
            if path in inv_by_path:
                raise ValueError(f"duplicate inventory path: {path}")
            inv_by_path[path] = item
    missing_inventory = sorted(set(bundles) - set(inv_by_path))
    if missing_inventory:
        raise ValueError(f"{len(missing_inventory)} labeled bundles absent from inventory: {missing_inventory[:5]}")
    for path, info in bundles.items():
        inv_hash = inv_by_path[path].get("sha256")
        if inv_hash != info["bundle_sha256"]:
            raise ValueError(f"inventory/reference hash mismatch for {path}: {inv_hash} != {info['bundle_sha256']}")

    predicted: set[tuple[str, str]] = set()
    candidate_rows_in_primary = 0
    candidate_rows_outside_primary = 0
    candidate_hash_errors = []
    unknown_candidate_rules = Counter()
    for item in candidates:
        rule = str(item.get("rule_id", ""))
        if rule not in SCANNER_RULES:
            unknown_candidate_rules[rule] += 1
            continue
        path = norm_bundle_path(str(item.get("source_file", "")))
        if path not in bundles:
            candidate_rows_outside_primary += 1
            continue
        candidate_rows_in_primary += 1
        observed_hash = item.get("source_sha256")
        expected_hash = bundles[path]["bundle_sha256"]
        if observed_hash != expected_hash:
            candidate_hash_errors.append({"path": path, "observed": observed_hash, "expected": expected_hash})
            continue
        predicted.add((path, rule))
    if candidate_hash_errors:
        raise ValueError(f"candidate source hash mismatch (first 5): {candidate_hash_errors[:5]}")
    if unknown_candidate_rules:
        raise ValueError(f"scanner emitted unknown rule IDs: {dict(unknown_candidate_rules)}")

    per_rule = []
    prevalence = []
    project_rows = []
    project_names = sorted(set(projects.values()))
    all_rule_ids = sorted(expected_rules)
    for rule in all_rule_ids:
        labels_for_rule = [(path, label_by_key[(path, rule)]["label"]) for path in bundles]
        counts = Counter(label for _, label in labels_for_rule)
        p, a, u, na = (counts[x] for x in ("PRESENT", "ABSENT", "U", "NA"))
        assessable = p + a
        uncertainty_base = p + a + u
        rule_pred = {(path, rule) in predicted for path in bundles}
        tp = sum(1 for path, lab in labels_for_rule if lab == "PRESENT" and (path, rule) in predicted)
        fn = p - tp
        fp = sum(1 for path, lab in labels_for_rule if lab == "ABSENT" and (path, rule) in predicted)
        tn = a - fp
        candidate_units = sum(1 for path in bundles if (path, rule) in predicted)
        row = {
            "rule_id": rule, "scanner_implemented": rule in SCANNER_RULES,
            "bundles": len(bundles), "present": p, "absent": a, "uncertain": u, "not_applicable": na,
            "assessable_present_absent": assessable,
            "reference_prevalence_present_over_present_plus_absent": safe_div(p, assessable),
            "uncertainty_rate_over_present_absent_u": safe_div(u, uncertainty_base),
            "na_rate_all_bundles": safe_div(na, len(bundles)),
            "scanner_candidate_bundle_units": candidate_units,
            "scanner_candidate_resource_records": sum(1 for x in candidates
                if norm_bundle_path(str(x.get("source_file", ""))) in bundles and x.get("rule_id") == rule),
            "tp": tp if rule in SCANNER_RULES else "",
            "fp": fp if rule in SCANNER_RULES else "",
            "fn": fn if rule in SCANNER_RULES else "",
            "tn": tn if rule in SCANNER_RULES else "",
            "precision": safe_div(tp, tp + fp) if rule in SCANNER_RULES else None,
            "recall": safe_div(tp, tp + fn) if rule in SCANNER_RULES else None,
            "specificity": safe_div(tn, tn + fp) if rule in SCANNER_RULES else None,
            "f1": safe_div(2 * tp, 2 * tp + fp + fn) if rule in SCANNER_RULES else None,
            "accuracy": safe_div(tp + tn, assessable) if rule in SCANNER_RULES else None,
        }
        per_rule.append(row)
        prevalence.append({
            "rule_id": rule, "bundles": len(bundles), "present": p, "absent": a, "uncertain": u,
            "not_applicable": na, "assessable_n": assessable,
            "prevalence": safe_div(p, assessable),
            "uncertainty_rate": safe_div(u, uncertainty_base),
            "applicability_rate": safe_div(uncertainty_base, len(bundles)),
            "na_rate": safe_div(na, len(bundles)),
        })
        for project in project_names:
            paths = [path for path in bundles if projects[path] == project]
            c = Counter(label_by_key[(path, rule)]["label"] for path in paths)
            pp, aa, uu, nn = (c[x] for x in ("PRESENT", "ABSENT", "U", "NA"))
            project_rows.append({
                "rule_id": rule, "upstream_project": project, "bundles": len(paths),
                "present": pp, "absent": aa, "uncertain": uu, "not_applicable": nn,
                "assessable_n": pp + aa, "prevalence": safe_div(pp, pp + aa),
            })

    implemented = [r for r in per_rule if r["scanner_implemented"]]
    binary = [r for r in implemented if r["present"] + r["absent"] > 0]
    tp = sum(int(r["tp"]) for r in binary)
    fp = sum(int(r["fp"]) for r in binary)
    fn = sum(int(r["fn"]) for r in binary)
    tn = sum(int(r["tn"]) for r in binary)
    # Macro averages include only rules with both positive and negative reference classes.
    two_class = [r for r in binary if r["present"] > 0 and r["absent"] > 0]
    estimable_f1 = [r["f1"] for r in two_class if r["f1"] is not None]
    macro_f1 = sum(estimable_f1) / len(estimable_f1) if estimable_f1 else None
    macro_precision_values = [r["precision"] for r in two_class if r["precision"] is not None]
    macro_recall_values = [r["recall"] for r in two_class if r["recall"] is not None]

    summary = {
        "schema_version": "1.0",
        "analysis": "scanner_candidate_vs_AI1_reference_and_descriptive_bundle_prevalence",
        "interpretation": "Exploratory AI-reference comparison; not human-validated scanner accuracy or real-world deployment prevalence.",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": os.environ.get("GITHUB_SHA", "unknown"),
        "script_version": VERSION,
        "input_paths": {
            "labels": str(args.labels), "candidates": str(args.candidates), "inventory": str(args.inventory)
        },
        "input_counts": {
            "bundles": len(bundles), "rules": len(expected_rules), "label_rows": len(labels),
            "scanner_candidate_records_total": len(candidates),
            "scanner_candidate_records_in_primary_bundles": candidate_rows_in_primary,
            "scanner_candidate_records_outside_primary_bundles": candidate_rows_outside_primary,
            "unique_candidate_bundle_rule_units_in_primary": len(predicted),
            "inventory_bundles": len(inventory),
        },
        "scanner_rule_ids": sorted(SCANNER_RULES),
        "micro_confusion_matrix_scanner_implemented_rules": {
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": safe_div(tp, tp + fp), "recall": safe_div(tp, tp + fn),
            "specificity": safe_div(tn, tn + fp),
            "f1": safe_div(2 * tp, 2 * tp + fp + fn),
            "accuracy": safe_div(tp + tn, tp + fp + fn + tn),
        },
        "macro_f1_over_implemented_rules_with_binary_reference_units": macro_f1,
        "macro_precision_over_rules_with_both_reference_classes": (
            sum(macro_precision_values) / len(macro_precision_values) if macro_precision_values else None
        ),
        "macro_recall_over_rules_with_both_reference_classes": (
            sum(macro_recall_values) / len(macro_recall_values) if macro_recall_values else None
        ),
        "macro_f1_rule_count": len(estimable_f1),
        "macro_metric_rule_ids": [r["rule_id"] for r in two_class],
        "limitations": [
            "Reference labels are AI-1 generated; author verification and independent human reference review remain pending.",
            "A candidate is aggregated to one positive prediction per bundle-rule pair; multiple resource candidates do not increase the unit count.",
            "U and NA are excluded from binary confusion matrices and reported separately.",
            "Rules not implemented by the scanner receive descriptive reference prevalence only, not scanner metrics.",
            "Prevalence describes this pinned public configuration corpus, not deployed clusters or all LLM-serving systems.",
            "Bundles are clustered within only a small number of upstream projects; point estimates are not independent-binomial estimates.",
            "No cluster-bootstrap confidence intervals are produced by this first pass.",
        ],
    }

    write_csv(out / "scanner_metrics.csv", per_rule, list(per_rule[0]))
    write_csv(out / "rule_prevalence.csv", prevalence, list(prevalence[0]))
    write_csv(out / "project_rule_prevalence.csv", project_rows, list(project_rows[0]))
    (out / "evaluation_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
