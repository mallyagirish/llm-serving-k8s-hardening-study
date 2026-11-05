#!/usr/bin/env python3
"""Validate the pinned corpus and produce a reproducible inventory.

This checks file presence, lockfile accounting, SHA-256, YAML parseability,
document counts, and Kubernetes resource-kind counts. It does not assess
security or establish that each bundle represents an independent deployment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    raise SystemExit("Missing dependency: install PyYAML with 'python -m pip install PyYAML'")


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
    parser.add_argument("--out-dir", default="results")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    lock_path = (root / args.lockfile).resolve()
    out_dir = (root / args.out_dir).resolve()
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    bundles = lock.get("bundles", [])
    sources = lock.get("sources", [])
    declared = int(lock.get("counts", {}).get("rendered_bundles", -1))
    errors: list[str] = []
    if declared != len(bundles):
        errors.append(f"lockfile declares {declared} bundles but contains {len(bundles)} entries")
    if int(lock.get("counts", {}).get("sources", -1)) != len(sources):
        errors.append("lockfile source count does not match sources array")

    kind_counts = Counter()
    document_count = 0
    inventory: list[dict[str, Any]] = []
    seen_paths: set[str] = set()

    for entry in bundles:
        rel = str(entry.get("path", ""))
        if not rel or rel in seen_paths:
            errors.append(f"missing or duplicate bundle path: {rel!r}")
            continue
        seen_paths.add(rel)
        candidate = (root / "corpus" / rel).resolve()
        if root not in candidate.parents:
            errors.append(f"path escapes corpus root: {rel}")
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
            errors.append(f"YAML parse failure in corpus/{rel}: {exc}")

        document_count += docs
        kind_counts.update(local_kinds)
        inventory.append({
            "path": rel,
            "source": entry.get("source"),
            "bundle_kind": entry.get("kind"),
            "sha256": file_sha256(candidate),
            "bytes": candidate.stat().st_size,
            "yaml_documents": docs,
            "resource_kinds": dict(sorted(local_kinds.items())),
            "parse_error": parse_error,
        })

    expected_kind_counts = lock.get("counts", {}).get("breakdown", {})
    actual_bundle_kinds = Counter(str(entry.get("kind")) for entry in bundles)
    for key, expected in {
        "helm_default": 20,
        "helm_values_overlays": 28,
        "manifests": 154,
    }.items():
        # These are historical lockfile accounting fields; validate against
        # actual bundle kind counts without inferring source independence.
        actual_key = {"helm_default": "helm-default",
                      "helm_values_overlays": "helm-values",
                      "manifests": "manifest"}[key]
        actual = actual_bundle_kinds.get(actual_key, 0)
        if actual != expected:
            errors.append(f"bundle kind {actual_key}: expected {expected}, found {actual}")

    out_dir.mkdir(parents=True, exist_ok=True)
    inventory_path = out_dir / "corpus_inventory.jsonl"
    with inventory_path.open("w", encoding="utf-8") as handle:
        for row in inventory:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    summary = {
        "lockfile": str(Path(args.lockfile)),
        "lockfile_sha256": file_sha256(lock_path),
        "collected_at": lock.get("collected_at"),
        "sources": len(sources),
        "declared_bundles": declared,
        "bundle_entries": len(bundles),
        "validated_bundle_files": len(inventory),
        "yaml_documents": document_count,
        "bundle_kind_counts": dict(sorted(actual_bundle_kinds.items())),
        "resource_kind_counts": dict(sorted(kind_counts.items())),
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
