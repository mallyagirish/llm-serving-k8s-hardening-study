#!/usr/bin/env python3
"""Create a scanner-blind bundle × rule labeling sheet from reviewed eligibility.

Reads the frozen nine-column eligibility CSV (see FROZEN_ELIGIBILITY_COLUMNS).
Upstream project is derived from the pinned corpus mapping
(``upstream_project_for_bundle`` in scripts/build_workload_inventory.py) and the
bundle SHA-256 is computed from the bundle file on disk at generation time.
Missing files, duplicate bundle paths, pending/unrecognized final decisions,
and unmapped projects are hard errors: the generator never silently defaults
project to "unmapped" or hash to "".

Reviewer labels are reference classifications of rule conditions, not scanner
confusion-matrix outcomes: PRESENT / ABSENT / U / NA (see docs/LABELING_GUIDE.md).
Reviewers never see scanner predictions. Scanner candidate output is
deliberately not read. This is scanner-blinding, not source-blinding: reviewers
need bundle paths to inspect the source artifacts.

Each run also writes a provenance sidecar (``<output>.meta.json``) recording
input file hashes, seed, reviewer ID, and the exact selected bundle list.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import random
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

GENERATOR_VERSION = "2.0.0"

LABEL_VALUES = ("PRESENT", "ABSENT", "U", "NA")

FROZEN_ELIGIBILITY_COLUMNS = (
    "bundle_path",
    "source",
    "bundle_kind",
    "preliminary_stratum",
    "preliminary_reason",
    "final_decision",
    "reviewer",
    "review_status",
    "review_notes",
)

KNOWN_FINAL_DECISIONS = frozenset({
    "include_primary",
    "include_supporting",
    "exclude_non_llm",
    "exclude_unparseable",
})

_HEX = set("0123456789abcdef")


def _load_upstream_project_fn() -> Callable[[str], str]:
    """Reuse the pinned corpus mapping from build_workload_inventory.py."""
    sibling = Path(__file__).resolve().parent / "build_workload_inventory.py"
    spec = importlib.util.spec_from_file_location("build_workload_inventory", sibling)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load corpus project mapping from {sibling}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.upstream_project_for_bundle


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_eligibility_csv(path: Path) -> list[dict[str, str]]:
    """Read the eligibility CSV and require the frozen nine-column schema."""
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = tuple(reader.fieldnames or ())
        rows = list(reader)
    missing = [c for c in FROZEN_ELIGIBILITY_COLUMNS if c not in fieldnames]
    if missing:
        raise ValueError(
            f"Eligibility CSV {path} does not match the frozen schema; "
            f"missing column(s): {', '.join(missing)}. "
            f"Expected columns: {', '.join(FROZEN_ELIGIBILITY_COLUMNS)}."
        )
    return rows


def validate_eligibility_rows(rows: list[dict[str, str]]) -> None:
    """Fail loudly on duplicate paths or pending/unrecognized decisions."""
    problems: list[str] = []
    seen: dict[str, int] = {}
    for index, row in enumerate(rows, start=2):  # line 1 is the header
        bundle_path = (row.get("bundle_path") or "").strip()
        if not bundle_path:
            problems.append(f"row {index}: empty bundle_path")
            continue
        if bundle_path in seen:
            problems.append(
                f"duplicate bundle_path {bundle_path!r} (rows {seen[bundle_path]} and {index})"
            )
        else:
            seen[bundle_path] = index
        decision = (row.get("final_decision") or "").strip()
        if not decision:
            problems.append(f"{bundle_path}: final_decision is empty (decision still pending)")
        elif decision not in KNOWN_FINAL_DECISIONS:
            problems.append(
                f"{bundle_path}: final_decision {decision!r} is not a frozen decision "
                f"(expected one of: {', '.join(sorted(KNOWN_FINAL_DECISIONS))})"
            )
    if problems:
        raise ValueError("Eligibility CSV failed validation:\n- " + "\n- ".join(problems))


def prepare_bundles(rows: list[dict[str, str]], corpus_root: Path,
                    project_for: Callable[[str], str] | None = None) -> list[dict[str, str]]:
    """Validate rows and enrich each include_primary bundle with its upstream
    project (pinned corpus mapping) and SHA-256 computed from disk.

    Raises ValueError on unmapped projects, missing bundle files, or paths
    escaping the corpus directory. Returns enriched copies; inputs unchanged.
    """
    validate_eligibility_rows(rows)
    if project_for is None:
        project_for = _load_upstream_project_fn()
    corpus_dir = (corpus_root / "corpus").resolve()
    enriched: list[dict[str, str]] = []
    for row in rows:
        if (row.get("final_decision") or "").strip() != "include_primary":
            continue
        bundle_path = (row.get("bundle_path") or "").strip()
        project = project_for(bundle_path)
        if not project or project == "unmapped":
            raise ValueError(
                f"Bundle {bundle_path!r} cannot be mapped to an upstream project "
                "by the pinned corpus mapping; refusing to default to 'unmapped'."
            )
        candidate = (corpus_dir / bundle_path).resolve()
        if corpus_dir not in candidate.parents:
            raise ValueError(f"Bundle path escapes the corpus directory: {bundle_path!r}")
        if not candidate.is_file():
            raise ValueError(
                f"Bundle file missing on disk: corpus/{bundle_path} "
                f"(resolved under corpus root {corpus_root})"
            )
        out = dict(row)
        out["upstream_project"] = project
        out["bundle_sha256"] = file_sha256(candidate)
        enriched.append(out)
    if not enriched:
        raise ValueError("No bundles have final_decision=include_primary in the eligibility CSV.")
    return enriched


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
                  sample_size: int | None, seed: int, reviewer_id: str = "R1") -> list[dict[str, str]]:
    """Build the labeling sheet from *prepared* eligibility rows.

    Rows must already carry ``upstream_project`` and ``bundle_sha256`` (see
    prepare_bundles). Unprepared rows are rejected rather than defaulted.
    """
    eligible = [r for r in eligibility_rows if r.get("final_decision", "").strip() == "include_primary"]
    if not eligible:
        raise ValueError("No bundles have final_decision=include_primary in the eligibility CSV.")
    if len({r.get("bundle_path", "") for r in eligible}) != len(eligible):
        raise ValueError("Eligibility CSV contains duplicate bundle_path values marked include_primary.")
    for row in eligible:
        bundle_path = row.get("bundle_path", "")
        project = (row.get("upstream_project") or "").strip()
        if not project or project == "unmapped":
            raise ValueError(
                f"Bundle {bundle_path!r} has no mapped upstream_project; "
                "run prepare_bundles (or the CLI) so project comes from the pinned corpus mapping."
            )
        digest = (row.get("bundle_sha256") or "").strip().lower()
        if len(digest) != 64 or any(c not in _HEX for c in digest):
            raise ValueError(
                f"Bundle {bundle_path!r} has no valid bundle_sha256; "
                "run prepare_bundles (or the CLI) so the hash is computed from the bundle file on disk."
            )
    n = len(eligible) if sample_size is None else sample_size
    if n < 1 or n > len(eligible):
        raise ValueError(f"sample_size must be between 1 and {len(eligible)}.")

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in eligible:
        groups[row["upstream_project"]].append(row)

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
                "upstream_project": bundle.get("upstream_project", ""),
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


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    commit = result.stdout.strip()
    return commit if result.returncode == 0 and commit else None


def build_metadata(*, eligibility_csv: Path, eligibility_rows: list[dict[str, str]],
                   rules_path: Path, lockfile_path: Path | None,
                   corpus_root: Path, sample_size: int | None, seed: int,
                   reviewer_id: str, selected: list[dict[str, str]],
                   eligible_count: int,
                   label_row_count: int, rule_count: int) -> dict[str, Any]:
    script_path = Path(__file__).resolve()
    selected_bundles = [
        {
            "bundle_path": b["bundle_path"],
            "upstream_project": b["upstream_project"],
            "bundle_sha256": b["bundle_sha256"],
        }
        for b in sorted(selected, key=lambda r: (r["upstream_project"], r["bundle_path"]))
    ]
    return {
        "artifact": "blinded_labeling_sample_metadata",
        "generator": {
            "script": "scripts/create_blinded_labeling_sample.py",
            "version": GENERATOR_VERSION,
            "commit": _git_commit(),
            "script_sha256": file_sha256(script_path),
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "eligibility_csv": {
                "path": str(eligibility_csv),
                "sha256": file_sha256(eligibility_csv),
            },
            "rules_catalog": {
                "path": str(rules_path),
                "sha256": file_sha256(rules_path),
            },
            "corpus_lockfile": (
                {"path": str(lockfile_path), "sha256": file_sha256(lockfile_path)}
                if lockfile_path is not None and lockfile_path.is_file() else None
            ),
            "project_mapping": {
                "source": "scripts/build_workload_inventory.py:upstream_project_for_bundle "
                          "(pinned corpus/SOURCES.lock.json bundle mapping)",
                "script_sha256": file_sha256(
                    Path(__file__).resolve().parent / "build_workload_inventory.py"
                ),
            },
            "corpus_root": str(corpus_root),
        },
        "eligibility_reviewers": sorted(
            {(r.get("reviewer") or "").strip() for r in eligibility_rows} - {""}
        ),
        "seed": seed,
        "sample_size": sample_size,
        "reviewer_id": reviewer_id,
        "label_values": list(LABEL_VALUES),
        "label_semantics": (
            "Reference classifications of rule conditions assigned by scanner-blind "
            "reviewers. PRESENT = rule condition present in the bundle; ABSENT = rule "
            "applies and the condition is absent; U = cannot determine from the bundle; "
            "NA = rule not applicable. PRESENT/ABSENT are not scanner TP/FP."
        ),
        "eligible_primary_bundles": eligible_count,
        "selected_bundles": selected_bundles,
        "selected_bundle_count": len(selected_bundles),
        "rules": rule_count,
        "label_rows": label_row_count,
        "scanner_output_used": False,
        "scanner_blind": True,
        "source_blind": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a reproducible scanner-blind labeling sheet; source metadata remains visible."
    )
    parser.add_argument("--eligibility-csv", required=True)
    parser.add_argument("--rules", default="rules/catalog.json")
    parser.add_argument("--corpus-root", default=".",
                        help="Repository root; bundle files resolve under <root>/corpus/.")
    parser.add_argument("--lockfile", default="corpus/SOURCES.lock.json",
                        help="Pinned corpus lockfile, hashed into the provenance sidecar when present.")
    parser.add_argument("--sample-size", type=int, default=None)
    parser.add_argument("--seed", type=int, default=20261105)
    parser.add_argument("--reviewer-id", required=True, help="Distinct identifier, e.g. R1 or R2.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--metadata-output", default=None,
                        help="Provenance sidecar path (default: <output>.meta.json).")
    args = parser.parse_args(argv)

    corpus_root = Path(args.corpus_root)
    eligibility_path = Path(args.eligibility_csv)
    eligibility = read_eligibility_csv(eligibility_path)
    prepared = prepare_bundles(eligibility, corpus_root)
    rules_path = Path(args.rules)
    catalog = json.loads(rules_path.read_text(encoding="utf-8"))
    rows = create_sample(prepared, catalog["rules"], args.sample_size, args.seed, args.reviewer_id)

    selected_by_path = {r["bundle_path"]: r for r in prepared}
    selected = [selected_by_path[p] for p in sorted({r["bundle_path"] for r in rows})]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    lockfile_path = corpus_root / args.lockfile if args.lockfile else None
    metadata = build_metadata(
        eligibility_csv=eligibility_path,
        eligibility_rows=eligibility,
        rules_path=rules_path,
        lockfile_path=lockfile_path,
        corpus_root=corpus_root,
        sample_size=args.sample_size,
        seed=args.seed,
        reviewer_id=args.reviewer_id,
        selected=selected,
        eligible_count=len(prepared),
        label_row_count=len(rows),
        rule_count=len(catalog["rules"]),
    )
    metadata_path = Path(args.metadata_output) if args.metadata_output else Path(
        str(output) + ".meta.json"
    )
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "eligible_bundles": len(prepared),
        "selected_bundles": len(selected),
        "rules": len(catalog["rules"]),
        "label_rows": len(rows),
        "seed": args.seed,
        "reviewer_id": args.reviewer_id,
        "output": str(output),
        "metadata_output": str(metadata_path),
        "scanner_output_used": False,
        "scanner_blind": True,
        "source_blind": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
