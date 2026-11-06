import csv
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "create_blinded_labeling_sample.py"
spec = importlib.util.spec_from_file_location("create_blinded_labeling_sample", SCRIPT)
sampling = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sampling)

RULES = [
    {"id": "R1", "title": "Rule one", "category": "Network", "severity": "High"},
    {"id": "R2", "title": "Rule two", "category": "Auth", "severity": "Critical"},
]

FROZEN_COLUMNS = list(sampling.FROZEN_ELIGIBILITY_COLUMNS)


def frozen_row(bundle_path, final_decision="include_primary", **overrides):
    row = {
        "bundle_path": bundle_path,
        "source": bundle_path.split("/")[1] if "/" in bundle_path else "src",
        "bundle_kind": "manifest",
        "preliminary_stratum": "primary_candidate",
        "preliminary_reason": "fixture",
        "final_decision": final_decision,
        "reviewer": "claude-ai-assist",
        "review_status": "reviewed_ai_assisted",
        "review_notes": "fixture",
    }
    row.update(overrides)
    return row


def write_csv(path, rows, fieldnames=None):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames or FROZEN_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


class BlindedSampleTests(unittest.TestCase):
    """Synthetic prepared-row tests (rows already carry project + hash)."""

    def setUp(self):
        self.eligibility = [
            {"bundle_path": "a.yaml", "upstream_project": "project-a", "bundle_sha256": "a" * 64, "bundle_kind": "manifest", "final_decision": "include_primary"},
            {"bundle_path": "b.yaml", "upstream_project": "project-a", "bundle_sha256": "b" * 64, "bundle_kind": "manifest", "final_decision": "include_primary"},
            {"bundle_path": "c.yaml", "upstream_project": "project-b", "bundle_sha256": "c" * 64, "bundle_kind": "helm-default", "final_decision": "include_primary"},
            {"bundle_path": "d.yaml", "upstream_project": "project-c", "bundle_sha256": "d" * 64, "bundle_kind": "manifest", "final_decision": "include_supporting"},
        ]
        self.rules = RULES

    def test_sample_is_reproducible_and_stratified(self):
        first = sampling.create_sample(self.eligibility, self.rules, 2, 123)
        second = sampling.create_sample(self.eligibility, self.rules, 2, 123)
        self.assertEqual(first, second)
        self.assertEqual(len({r["bundle_path"] for r in first}), 2)
        self.assertEqual(len(first), 4)

    def test_scanner_data_is_not_in_label_template(self):
        rows = sampling.create_sample(self.eligibility, self.rules, None, 123)
        self.assertNotIn("candidate_status", rows[0])
        self.assertEqual(rows[0]["label"], "")
        self.assertEqual(rows[0]["rationale"], "")

    def test_no_eligible_bundles_fails(self):
        with self.assertRaises(ValueError):
            sampling.create_sample(self.eligibility[3:], self.rules, None, 123)

    def test_unprepared_rows_are_rejected_not_defaulted(self):
        unprepared = [
            {"bundle_path": "a.yaml", "bundle_kind": "manifest", "final_decision": "include_primary"},
        ]
        with self.assertRaises(ValueError):
            sampling.create_sample(unprepared, self.rules, None, 123)
        unmapped = [
            {"bundle_path": "a.yaml", "upstream_project": "unmapped", "bundle_sha256": "a" * 64,
             "bundle_kind": "manifest", "final_decision": "include_primary"},
        ]
        with self.assertRaises(ValueError):
            sampling.create_sample(unmapped, self.rules, None, 123)
        empty_hash = [
            {"bundle_path": "a.yaml", "upstream_project": "project-a", "bundle_sha256": "",
             "bundle_kind": "manifest", "final_decision": "include_primary"},
        ]
        with self.assertRaises(ValueError):
            sampling.create_sample(empty_hash, self.rules, None, 123)


class FrozenSchemaPipelineTests(unittest.TestCase):
    """Pipeline tests against the actual frozen nine-column CSV schema."""

    BUNDLES = {
        "rendered/kserve-v0.15.0/default.yaml": "kserve/kserve",
        "rendered/vllm-stack-0.1.13/default.yaml": "vllm-project/production-stack",
        "rendered/hami-example-nvidia_default_use/manifest.yaml": "Project-HAMi/HAMi",
    }

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for bundle_path in self.BUNDLES:
            target = self.root / "corpus" / bundle_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"# fixture bundle {bundle_path}\n", encoding="utf-8")
        self.csv_path = self.root / "eligibility.csv"

    def tearDown(self):
        self.tmp.cleanup()

    def _rows(self):
        rows = [frozen_row(p) for p in self.BUNDLES]
        rows.append(frozen_row("rendered/litellm-helm-1.107.0-rc.2/default.yaml",
                               final_decision="include_supporting"))
        return rows

    def test_frozen_schema_accepted_projects_and_hashes_populated(self):
        write_csv(self.csv_path, self._rows())
        rows = sampling.read_eligibility_csv(self.csv_path)
        prepared = sampling.prepare_bundles(rows, self.root)
        self.assertEqual(len(prepared), 3)
        for row in prepared:
            self.assertEqual(row["upstream_project"], self.BUNDLES[row["bundle_path"]])
            expected = hashlib.sha256(
                (self.root / "corpus" / row["bundle_path"]).read_bytes()
            ).hexdigest()
            self.assertEqual(row["bundle_sha256"], expected)
        sheet = sampling.create_sample(prepared, RULES, None, 42, "R1")
        self.assertEqual(len(sheet), 3 * len(RULES))
        self.assertTrue(all(r["bundle_sha256"] for r in sheet))
        self.assertNotIn("unmapped", {r["upstream_project"] for r in sheet})

    def test_missing_schema_column_rejected(self):
        rows = [{k: v for k, v in r.items() if k != "review_notes"} for r in self._rows()]
        reduced = [c for c in FROZEN_COLUMNS if c != "review_notes"]
        write_csv(self.csv_path, rows, fieldnames=reduced)
        with self.assertRaises(ValueError):
            sampling.read_eligibility_csv(self.csv_path)

    def test_unmapped_project_rejected(self):
        rows = [frozen_row("rendered/unknown-thing-1.0/default.yaml")]
        target = self.root / "corpus" / "rendered/unknown-thing-1.0/default.yaml"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# exists but unmapped\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            sampling.prepare_bundles(rows, self.root)

    def test_missing_bundle_file_rejected(self):
        rows = [frozen_row("rendered/kserve-v0.15.0/not-on-disk.yaml")]
        with self.assertRaises(ValueError):
            sampling.prepare_bundles(rows, self.root)

    def test_duplicate_bundle_path_rejected(self):
        rows = self._rows()
        rows.append(frozen_row("rendered/kserve-v0.15.0/default.yaml",
                               final_decision="include_supporting"))
        with self.assertRaises(ValueError):
            sampling.prepare_bundles(rows, self.root)

    def test_pending_decision_rejected(self):
        for bad in ("", "uncertain", "pending"):
            rows = self._rows()
            rows[0]["final_decision"] = bad
            with self.assertRaises(ValueError, msg=f"final_decision={bad!r}"):
                sampling.prepare_bundles(rows, self.root)

    def test_main_writes_sheet_and_provenance_sidecar(self):
        write_csv(self.csv_path, self._rows())
        rules_path = self.root / "rules.json"
        rules_path.write_text(json.dumps({"rules": RULES}), encoding="utf-8")
        output = self.root / "out" / "reviewer_R1.csv"
        rc = sampling.main([
            "--eligibility-csv", str(self.csv_path),
            "--rules", str(rules_path),
            "--corpus-root", str(self.root),
            "--seed", "7",
            "--reviewer-id", "R1",
            "--output", str(output),
        ])
        self.assertEqual(rc, 0)
        with output.open(newline="", encoding="utf-8") as f:
            sheet = list(csv.DictReader(f))
        self.assertEqual(len(sheet), 3 * len(RULES))

        sidecar = json.loads(Path(str(output) + ".meta.json").read_text(encoding="utf-8"))
        self.assertEqual(sidecar["seed"], 7)
        self.assertEqual(sidecar["reviewer_id"], "R1")
        self.assertEqual(sidecar["label_values"], ["PRESENT", "ABSENT", "U", "NA"])
        self.assertEqual(sidecar["eligible_primary_bundles"], 3)
        self.assertEqual(sidecar["inputs"]["eligibility_csv"]["sha256"],
                         hashlib.sha256(self.csv_path.read_bytes()).hexdigest())
        selected = {b["bundle_path"]: b for b in sidecar["selected_bundles"]}
        self.assertEqual(set(selected), set(self.BUNDLES))
        for bundle_path, entry in selected.items():
            self.assertEqual(entry["upstream_project"], self.BUNDLES[bundle_path])
            self.assertEqual(
                entry["bundle_sha256"],
                hashlib.sha256((self.root / "corpus" / bundle_path).read_bytes()).hexdigest(),
            )
        self.assertEqual({r["bundle_path"] for r in sheet}, set(selected))


class RealFrozenCsvTests(unittest.TestCase):
    """The committed frozen CSV + pinned corpus must pass the hardened pipeline."""

    def test_real_frozen_csv_prepares_cleanly(self):
        csv_path = REPO_ROOT / "results" / "bundle_eligibility_review.csv"
        rows = sampling.read_eligibility_csv(csv_path)
        prepared = sampling.prepare_bundles(rows, REPO_ROOT)
        self.assertEqual(len(prepared), 105)
        projects = {r["upstream_project"] for r in prepared}
        self.assertNotIn("unmapped", projects)
        self.assertTrue(all(len(r["bundle_sha256"]) == 64 for r in prepared))
        # Stratification survives: every frozen primary maps to a real project.
        self.assertGreaterEqual(len(projects), 10)

    def test_corpus_and_results_copies_agree(self):
        corpus_rows = sampling.read_eligibility_csv(REPO_ROOT / "corpus" / "eligibility_review.csv")
        results_rows = sampling.read_eligibility_csv(REPO_ROOT / "results" / "bundle_eligibility_review.csv")
        self.assertEqual(corpus_rows, results_rows)


if __name__ == "__main__":
    unittest.main()
