#!/usr/bin/env python3
"""Create a scanner-blind bundle × rule labeling sheet from reviewed eligibility.

The eligibility CSV must contain final_decision=include_primary. Scanner
candidate output is deliberately not read. This is scanner-blinding, not
source-blinding: reviewers need bundle paths to inspect the source artifacts.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


def proportional_quotas(groups: dict[str, list[dict[str, str]]], sample_size: int) -> dict[str, int]:
    total = sum(len(items) for items in groups.values())
    if sample_size >= total:
        return {key: len(items) for key, items in groups.items()}
    exact = {key: sample_size * len(items) / total for key, items in groups.items()}
    quotas = {key: int(value) for key, value in exact.items()}
    remaining = sample_size - sum(quotas.values())
    for key in sorted(groups, key=lambda k: (exact[k] - quotas[k], len(groups[k])), reverse=True)[:remaining]:
        quotas[key] += 1
    return quotas


def create_sample(eligibility_rows: list[dict[str, str]], rules: list[dict[str, Any]],
                  sample_size: int | None, seed: int, reviewer_id: str) -> list[dict[str, str]]:
    eligible = [r for r in eligibility_rows if r.get("final_decision", "").strip() == "include_primary"]
    if not eligible:
        raise ValueError("No bundles have final_decision=include_primary in the eligibility CSV.")
    if len({r.get("bundle_path", "") for r in eligible}) != len(eligible):
        raise ValueError("Eligibility CSV contains duplicate bundle_path values marked include_primary.")
    n = len(eligible) if sample_size is None else sample_size
    if n < 1 or n > len(eligible):
        raise ValueError(f"sample_size must be between 1 and {len(eligible)}.")

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in eligible:
        groups[row.get("upstream_project", "unmapped") or "unmapped"].append(row)

    rng = random.Random(seed)
    quotas = proportional_quotas(groups, n)
    selected = []
    for project in sorted(groups):
        selected.extend(rng.sample(groups[project], quotas[project]))
    selected.sort(key=lambda r: (r.get("upstream_project", ""), r.get("bundle_path", "")))

    output = []
    for bundle in selected:
        for rule in rules:
            rule_id = rule["id"]
            blind_id = hashlib.sha256(
                f"{seed}|{bundle['bundle_path']}|{rule_id}".encode("utf-8")
            ).hexdigest()[:12]
            output.append({
                "blind_id": blind_id,
                "bundle_path": bundle.get("bundle_path", ""),
                "bundle_sha256": bundle.get("bundle_sha256", ""),
                "upstream_project": bundle.get("upstream_project", "unmapped"),
                "bundle_kind": bundle.get("bundle_kind", ""),
                "rule_id": rule_id,
                "rule_title": rule.get("title", ""),
                "category": rule.get("category", ""),
                "severity": rule.get("severity", ""),
                "label": "",
                "evidence_path": "",
                "rationale": "",
                "reviewer_id": reviewer_id,
                "review_timestamp": "",
            })
    return output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a reproducible scanner-blind labeling sheet; source metadata remains visible."
    )
    parser.add_argument("--eligibility-csv", required=True)
    parser.add_argument("--rules", default="rules/catalog.json")
    parser.add_argument("--sample-size", type=int, default=None)
    parser.add_argument("--seed", type=int, default=20261105)
    parser.add_argument("--reviewer-id", required=True, help="Distinct identifier, e.g. R1 or R2.")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with Path(args.eligibility_csv).open(newline="", encoding="utf-8") as f:
        eligibility = list(csv.DictReader(f))
    catalog = json.loads(Path(args.rules).read_text(encoding="utf-8"))
    rows = create_sample(eligibility, catalog["rules"], args.sample_size, args.seed, args.reviewer_id)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({
        "eligible_bundles": len({r["bundle_path"] for r in rows}),
        "rules": len(catalog["rules"]),
        "label_rows": len(rows),
        "seed": args.seed,
        "reviewer_id": args.reviewer_id,
        "output": str(output),
        "scanner_output_used": False,
        "scanner_blind": True,
        "source_blind": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
