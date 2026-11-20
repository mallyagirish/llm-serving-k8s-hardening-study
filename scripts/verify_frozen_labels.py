#!/usr/bin/env python3
"""Read-only verification of the frozen v2 reference-label matrix and sidecar."""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path

EXPECTED = {'PRESENT': 647, 'ABSENT': 738, 'U': 697, 'NA': 858}
REQUIRED = {'bundle_path', 'bundle_sha256', 'upstream_project', 'rule_id', 'label'}

def verify(root: Path):
    csv_path = root / 'results/labels/reference_labels_author_validated_v2.csv'
    meta_path = root / 'results/labels/reference_labels_author_validated_v2.csv.meta.json'
    metadata = json.loads(meta_path.read_text(encoding='utf-8'))
    digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    assert digest == metadata['frozen_sha256'], f'v2 SHA-256 mismatch: {digest}'
    with csv_path.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames and REQUIRED <= set(reader.fieldnames), 'Missing required columns'
        rows = list(reader)
    assert len(rows) == 2940, f'Expected 2940 rows, got {len(rows)}'
    labels = collections.Counter(row['label'] for row in rows)
    assert labels == EXPECTED, f'Label counts mismatch: {labels}'
    assert labels == metadata['frozen_counts'], 'Counts differ from frozen sidecar'
    keys = [(r['bundle_path'].removeprefix('corpus/'), r['rule_id']) for r in rows]
    assert len(set(keys)) == len(keys), 'Duplicate bundle-rule keys'
    bundles = {p for p, _ in keys}
    rules = {rule for _, rule in keys}
    assert len(bundles) == 105 and len(rules) == 28, f'Matrix shape {len(bundles)} x {len(rules)}'
    assert len(keys) == len(bundles) * len(rules), 'Incomplete matrix'
    bundle_hashes = collections.defaultdict(set)
    projects = collections.defaultdict(set)
    for row in rows:
        path = row['bundle_path'].removeprefix('corpus/')
        bundle_hashes[path].add(row['bundle_sha256'])
        projects[path].add(row['upstream_project'])
    assert all(len(v) == 1 for v in bundle_hashes.values()), 'Conflicting bundle hashes'
    assert all(len(v) == 1 for v in projects.values()), 'Conflicting project assignments'
    assert len({next(iter(v)) for v in projects.values()}) == 10, 'Expected 10 upstream projects'
    return {'status': 'PASS', 'sha256': digest, 'rows': len(rows), 'bundles': len(bundles), 'rules': len(rules), 'projects': 10, 'counts': dict(labels)}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', type=Path, default=Path('.'))
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.repo_root), indent=2, sort_keys=True))
    except (AssertionError, OSError, ValueError, KeyError) as exc:
        parser.exit(1, f'FAIL: {exc}\n')
