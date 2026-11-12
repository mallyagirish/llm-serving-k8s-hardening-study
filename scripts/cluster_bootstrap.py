#!/usr/bin/env python3
"""Project-cluster bootstrap and influence analysis for Phase 3 outputs.

Consumes the evaluator's project-stratified sufficient statistics. Resampling
projects (not bundles) preserves within-project dependence. Percentile intervals
are descriptive with only a small number of clusters; they are not a cure for
limited external validity.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

VERSION = "1.0.0"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def number(row: dict[str, str], key: str) -> int:
    return int(float(row.get(key) or 0))


def ratio(n: float, d: float) -> float | None:
    return n / d if d else None


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * p
    lo = int(position)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (position - lo)


def ci(values: list[float]) -> tuple[float | None, float | None]:
    return percentile(values, 0.025), percentile(values, 0.975)


def load_project_tables(prevalence_path: Path, metrics_path: Path):
    prevalence = defaultdict(dict)
    metrics = defaultdict(dict)
    for row in read_csv(prevalence_path):
        prevalence[row["upstream_project"]][row["rule_id"]] = {
            k: number(row, k) for k in ("present", "absent", "uncertain", "not_applicable", "bundles")
        }
    for row in read_csv(metrics_path):
        metrics[row["upstream_project"]][row["rule_id"]] = {
            k: number(row, k) for k in ("tp", "fp", "fn", "tn", "present", "absent", "uncertain", "not_applicable", "bundles")
        }
    projects = sorted(set(prevalence) | set(metrics))
    if len(projects) < 2:
        raise ValueError(f"need at least 2 upstream projects; found {len(projects)}")
    rules = sorted({r for p in projects for r in prevalence[p]})
    scanner_rules = sorted({r for p in projects for r in metrics[p]})
    for project in projects:
        missing = set(rules) - set(prevalence[project])
        if missing:
            raise ValueError(f"missing prevalence rows for {project}: {sorted(missing)}")
        missing_scanner = set(scanner_rules) - set(metrics[project])
        if missing_scanner:
            raise ValueError(f"missing scanner rows for {project}: {sorted(missing_scanner)}")
    return projects, rules, scanner_rules, prevalence, metrics


def prevalence_estimate(sample, project_rows, rule, equal_project=False):
    rows = [project_rows[p][rule] for p in sample]
    if equal_project:
        estimates = [ratio(x["present"], x["present"] + x["absent"]) for x in rows]
        estimates = [x for x in estimates if x is not None]
        return statistics.mean(estimates) if estimates else None
    present = sum(x["present"] for x in rows)
    absent = sum(x["absent"] for x in rows)
    return ratio(present, present + absent)


def scanner_estimates(sample, metric_rows, scanner_rules):
    totals = {k: 0 for k in ("tp", "fp", "fn", "tn")}
    per_rule = {}
    for rule in scanner_rules:
        c = {k: sum(metric_rows[p][rule][k] for p in sample) for k in ("tp", "fp", "fn", "tn")}
        per_rule[rule] = c
        for key in totals:
            totals[key] += c[key]
    tp, fp, fn, tn = (totals[k] for k in ("tp", "fp", "fn", "tn"))
    pooled = {
        "precision": ratio(tp, tp + fp),
        "recall": ratio(tp, tp + fn),
        "specificity": ratio(tn, tn + fp),
        "f1": ratio(2 * tp, 2 * tp + fp + fn),
        "accuracy": ratio(tp + tn, tp + fp + fn + tn),
    }
    f1s = [ratio(2*c["tp"], 2*c["tp"]+c["fp"]+c["fn"])
           for c in per_rule.values() if c["tp"] + c["fp"] + c["fn"] + c["tn"] > 0
           and c["tp"] + c["fn"] > 0 and c["tn"] + c["fp"] > 0]
    pooled["macro_f1"] = statistics.mean(f1s) if f1s else None
    per_rule_metrics = {}
    for rule, c in per_rule.items():
        per_rule_metrics[rule] = {
            "precision": ratio(c["tp"], c["tp"] + c["fp"]),
            "recall": ratio(c["tp"], c["tp"] + c["fn"]),
            "specificity": ratio(c["tn"], c["tn"] + c["fp"]),
            "f1": ratio(2*c["tp"], 2*c["tp"]+c["fp"]+c["fn"]),
        }
    return pooled, per_rule_metrics, totals


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-prevalence", required=True, type=Path)
    parser.add_argument("--project-metrics", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--replicates", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20261111)
    args = parser.parse_args()
    if args.replicates < 1000:
        raise ValueError("--replicates must be >= 1000")
    projects, rules, scanner_rules, prev, metrics = load_project_tables(
        args.project_prevalence, args.project_metrics
    )
    n = len(projects)
    rng = random.Random(args.seed)
    samples = [[rng.choice(projects) for _ in range(n)] for _ in range(args.replicates)]
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    prevalence_rows = []
    for rule in rules:
        pooled_draws, equal_draws = [], []
        for sample in samples:
            p = prevalence_estimate(sample, prev, rule, False)
            e = prevalence_estimate(sample, prev, rule, True)
            if p is not None:
                pooled_draws.append(p)
            if e is not None:
                equal_draws.append(e)
        point = prevalence_estimate(projects, prev, rule, False)
        equal = prevalence_estimate(projects, prev, rule, True)
        lo, hi = ci(pooled_draws)
        elo, ehi = ci(equal_draws)
        project_values = [ratio(prev[p][rule]["present"],
                                prev[p][rule]["present"] + prev[p][rule]["absent"])
                          for p in projects]
        valid = [x for x in project_values if x is not None]
        prevalence_rows.append({
            "rule_id": rule, "project_clusters": n,
            "assessable_projects": len(valid),
            "bundle_weighted_prevalence": point,
            "bundle_weighted_bootstrap_95ci_low": lo,
            "bundle_weighted_bootstrap_95ci_high": hi,
            "equal_project_prevalence": equal,
            "equal_project_bootstrap_95ci_low": elo,
            "equal_project_bootstrap_95ci_high": ehi,
            "project_prevalence_min": min(valid) if valid else None,
            "project_prevalence_max": max(valid) if valid else None,
            "bootstrap_replicates_with_estimable_value": len(pooled_draws),
        })

    scanner_rows = []
    pooled_draws = defaultdict(list)
    rule_draws = {r: defaultdict(list) for r in scanner_rules}
    for sample in samples:
        pooled, per_rule, _ = scanner_estimates(sample, metrics, scanner_rules)
        for key, value in pooled.items():
            if value is not None:
                pooled_draws[key].append(value)
        for rule, values in per_rule.items():
            for key, value in values.items():
                if value is not None:
                    rule_draws[rule][key].append(value)
    pooled_point, _, totals = scanner_estimates(projects, metrics, scanner_rules)
    for metric, estimate in pooled_point.items():
        lo, hi = ci(pooled_draws[metric])
        scanner_rows.append({
            "scope": "pooled_micro", "rule_id": "ALL_IMPLEMENTED",
            "metric": metric, "point_estimate": estimate,
            "bootstrap_95ci_low": lo, "bootstrap_95ci_high": hi,
            "clusters": n, "replicates_with_estimable_value": len(pooled_draws[metric]),
        })
    for rule in scanner_rules:
        _, point_by_rule, _ = scanner_estimates(projects, metrics, [rule])
        for metric, estimate in point_by_rule[rule].items():
            lo, hi = ci(rule_draws[rule][metric])
            scanner_rows.append({
                "scope": "per_rule", "rule_id": rule, "metric": metric,
                "point_estimate": estimate, "bootstrap_95ci_low": lo,
                "bootstrap_95ci_high": hi, "clusters": n,
                "replicates_with_estimable_value": len(rule_draws[rule][metric]),
            })

    sensitivity = []
    for project in projects:
        remaining = [p for p in projects if p != project]
        p_est = {r: prevalence_estimate(remaining, prev, r, False) for r in rules}
        s_est, _, counts = scanner_estimates(remaining, metrics, scanner_rules)
        sensitivity.append({
            "omitted_project": project,
            "remaining_clusters": len(remaining),
            "pooled_scanner_tp": counts["tp"], "pooled_scanner_fp": counts["fp"],
            "pooled_scanner_fn": counts["fn"], "pooled_scanner_tn": counts["tn"],
            **{f"scanner_{k}": v for k, v in s_est.items()},
            "rule_prevalence_json": json.dumps(p_est, sort_keys=True),
        })

    def write_csv(path, rows):
        if not rows:
            return
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    write_csv(out / "cluster_bootstrap_prevalence.csv", prevalence_rows)
    write_csv(out / "cluster_bootstrap_scanner_metrics.csv", scanner_rows)
    write_csv(out / "leave_one_project_out.csv", sensitivity)
    summary = {
        "analysis_version": VERSION, "seed": args.seed, "replicates": args.replicates,
        "resampling_unit": "upstream_project", "project_clusters": n,
        "projects": projects, "prevalence_rules": len(rules),
        "scanner_rules": len(scanner_rules), "pooled_scanner_confusion": totals,
        "pooled_scanner_point_estimates": pooled_point,
        "interpretation": [
            "Percentile intervals resample upstream projects with replacement, retaining each sampled project's complete aggregate counts.",
            "Bundles within a project are not resampled independently.",
            "Only a small number of project clusters are available; intervals are exploratory and may be unstable.",
            "Bundle-weighted estimates are pooled assessable bundle counts; equal-project estimates weight each estimable project equally.",
            "A rule with sparse or absent classes may have undefined metrics or degenerate intervals; this is a data limitation, not evidence of certainty.",
            "The post-adjudication analysis is sensitivity-only because the four adjudications were selected from scanner disagreements with scanner predictions visible.",
        ],
    }
    (out / "cluster_bootstrap_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}")
