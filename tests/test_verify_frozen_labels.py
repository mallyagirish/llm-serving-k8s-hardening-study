"""Synthetic contract tests for frozen-reference integrity verifier.

Uses temporary CSV fixtures only; never changes study data.
"""
import csv
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_frozen_labels.py"
spec = importlib.util.spec_from_file_location("verify_frozen_labels", SCRIPT)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class FrozenLabelVerifierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / "results" / "labels"
        self.folder.mkdir(parents=True)
        self.csv_path = self.folder / "reference_labels_author_validated_v2.csv"
        self.meta_path = self.folder / "reference_labels_author_validated_v2.csv.meta.json"
        outcomes = sum(([k] * n for k, n in verifier.EXPECTED.items()), [])
        self.rows = [
            {"bundle_path": f"corpus/rendered/bundle-{i // 28:03d}/manifest.yaml",
             "bundle_sha256": f"hash-{i // 28:03d}",
             "upstream_project": f"project-{(i // 28) % 10}",
             "rule_id": f"LLM-TEST-{i % 28:02d}",
             "label": outcomes[i]}
            for i in range(2940)
        ]
        self.write_fixture()

    def write_fixture(self):
        with self.csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(self.rows[0]))
            writer.writeheader()
            writer.writerows(self.rows)
        digest = hashlib.sha256(self.csv_path.read_bytes()).hexdigest()
        self.meta_path.write_text(json.dumps({
            "frozen_sha256": digest, "frozen_counts": verifier.EXPECTED
        }), encoding="utf-8")

    def test_valid_complete_matrix_passes(self):
        result = verifier.verify(self.root)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual((result["rows"], result["bundles"], result["rules"]), (2940, 105, 28))

    def test_tampered_bytes_fail_sha256(self):
        self.csv_path.write_bytes(self.csv_path.read_bytes() + b"\n")
        with self.assertRaisesRegex(AssertionError, "SHA-256 mismatch"):
            verifier.verify(self.root)

    def test_duplicate_pair_fails_even_when_counts_and_hash_match(self):
        self.rows[1]["rule_id"] = self.rows[0]["rule_id"]
        self.write_fixture()
        with self.assertRaisesRegex(AssertionError, "Duplicate bundle-rule keys"):
            verifier.verify(self.root)

    def test_conflicting_project_mapping_fails(self):
        self.rows[1]["upstream_project"] = "project-9"
        self.write_fixture()
        with self.assertRaisesRegex(AssertionError, "Conflicting project assignments"):
            verifier.verify(self.root)

    def test_changed_outcome_fails_even_with_updated_hash(self):
        self.rows[0]["label"] = "ABSENT"
        self.write_fixture()
        with self.assertRaisesRegex(AssertionError, "Label counts mismatch"):
            verifier.verify(self.root)

    def test_missing_column_fails(self):
        with self.csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["bundle_path", "rule_id", "label"], extrasaction="ignore")
            writer.writeheader()
            writer.writerows(self.rows)
        meta = json.loads(self.meta_path.read_text())
        meta["frozen_sha256"] = hashlib.sha256(self.csv_path.read_bytes()).hexdigest()
        self.meta_path.write_text(json.dumps(meta))
        with self.assertRaisesRegex(AssertionError, "Missing required columns"):
            verifier.verify(self.root)


if __name__ == "__main__":
    unittest.main()
