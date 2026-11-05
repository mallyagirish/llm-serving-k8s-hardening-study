#!/usr/bin/env python3
"""Validate the pinned corpus and produce a reproducible inventory.

Checks lockfile accounting, file presence, SHA-256, YAML parsing, and resource
kinds. Explicitly allowlisted Helm fragments/non-YAML examples remain in the
corpus inventory but are excluded from static YAML scanning. Parseability does
not establish LLM-serving eligibility or independent deployment status.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--lockfile", default="corpus/SOURCES.lock.json")
    parser.add_argument("--exceptions", default="corpus/parse_exceptions.json")
    parser.add_argument("--out-dir", default="results")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    lock_path = (root / args.lockfile).resolve()
    exceptions_path = (root / args.exceptions).resolve()
    out_dir = (root / args.out_dir).resolve()
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    exceptions_doc = json.loads(exceptions_path.read_text(encoding="utf-8"))
    exceptions = {item["path"]: item for item in exceptions_doc.get("exceptions", [])}
    bundles = lock.get("bundles", [])
    sources = lock.get("sources", [])
    declared = int(lock.get("counts", {}).get("rendered_bundles", -1))
    errors: list[str] = []
    if declared != len(bundles):
        errors.append(f"lockfile declares {declared} bundles but contains {len(bundles)} entries")
    if int(lock.get("counts", {}).get("sources", -1)) != len(sources):
        errors.append("lockfile source count does not match sources array")

    bundle_kind_counts = Counter(str(entry.get("kind")) for entry in bundles)
    for expected_kind, expected_count in {
        "helm-default": 20, "helm-values": 28, "manifest": 154
    }.items():
        actual = bundle_kind_counts.get(expected_kind, 0)
        if actual != expected_count:
            errors.append(f"bundle kind {expected_kind}: expected {expected_count}, found {actual}")

    resource_kind_counts = Counter()
    document_count = 0
    inventory: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    encountered_exceptions: set[str] = set()

    for entry in bundles:
        rel = str(entry.get("path", ""))
        if not rel or rel in seen_paths:
            errors.append(f"missing or duplicate bundle path: {rel!r}")
            continue
        seen_paths.add(rel)
        candidate = (root / "corpus" / rel).resolve()
        if root not in candidate.parents:
            errors.append(f"path escapes repository root: {rel}")
            continue
        if not candidate.is_file():
            errors.append(f"missing bundle file: corpus/{rel}")
            continue

        local_kinds = Counter()
        docs = 0
        parse_error = None
        try:
            with candidate.open("r", encoding="utf-8") as handle:
                for obj in yaml.safe_load_all(handle):
                    if obj is None:
                        continue
                    docs += 1
                    if isinstance(obj, dict) and isinstance(obj.get("kind"), str):
                        local_kinds[obj["kind"]] += 1
                    else:
                        local_kinds["NON_RESOURCE_DOCUMENT"] += 1
        except (yaml.YAMLError, UnicodeDecodeError) as exc:
            parse_error = str(exc)

        documented_exception = exceptions.get(rel)
        if parse_error and documented_exception:
            encountered_exceptions.add(rel)
            parse_status = "documented_exclusion"
        elif parse_error:
            errors.append(f"unclassified YAML parse failure in corpus/{rel}: {parse_error}")
            parse_status = "unexpected_parse_failure"
        elif documented_exception:
            errors.append(f"stale parse exception: corpus/{rel} now parses as YAML")
            parse_status = "stale_exception"
        else:
            parse_status = "parseable"

        if parse_status == "parseable":
            document_count += docs
            resource_kind_counts.update(local_kinds)

        inventory.append({
            "path": rel,
            "source": entry.get("source"),
            "bundle_kind": entry.get("kind"),
            "sha256": file_sha256(candidate),
            "bytes": candidate.stat().st_size,
            "yaml_documents": docs,
            "resource_kinds": dict(sorted(local_kinds.items())),
            "parse_status": parse_status,
            "parse_error": parse_error,
            "parseable_for_static_scan": parse_status == "parseable",
            "llm_serving_eligibility": "requires_separate_review",
        })

    for rel in sorted(set(exceptions) - encountered_exceptions):
        errors.append(f"allowlisted parse exception was not encountered: corpus/{rel}")

    out_dir.mkdir(parents=True, exist_ok=True)
    inventory_path = out_dir / "corpus_inventory.jsonl"
    with inventory_path.open("w", encoding="utf-8") as handle:
        for row in inventory:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    parseable_count = sum(row["parse_status"] == "parseable" for row in inventory)
    excluded_count = sum(row["parse_status"] == "documented_exclusion" for row in inventory)
    hashes: dict[str, list[str]] = defaultdict(list)
    for row in inventory:
        hashes[row["sha256"]].append(row["path"])
    exact_duplicate_groups = [paths for paths in hashes.values() if len(paths) > 1]
    summary = {
        "lockfile": str(Path(args.lockfile)),
        "lockfile_sha256": file_sha256(lock_path),
        "collected_at": lock.get("collected_at"),
        "sources": len(sources),
        "declared_bundles": declared,
        "bundle_entries": len(bundles),
        "validated_bundle_files": len(inventory),
        "parseable_bundle_files": parseable_count,
        "documented_non_yaml_exclusions": excluded_count,
        "yaml_documents_in_parseable_bundles": document_count,
        "bundle_kind_counts": dict(sorted(bundle_kind_counts.items())),
        "exact_duplicate_hash_groups": len(exact_duplicate_groups),
        "exact_duplicate_bundle_files": sum(len(paths) for paths in exact_duplicate_groups),
        "exact_duplicate_paths": exact_duplicate_groups,
        "resource_kind_counts": dict(sorted(resource_kind_counts.items())),
        "llm_serving_eligibility": "not_assessed_by_this_validator",
        "errors": errors,
        "validation_passed": not errors,
    }
    (out_dir / "corpus_validation.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
