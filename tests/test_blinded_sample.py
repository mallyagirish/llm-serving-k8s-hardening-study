import importlib.util
import unittest

SCRIPT = __import__("pathlib").Path(__file__).resolve().parents[1] / "scripts" / "create_blinded_labeling_sample.py"
spec = importlib.util.spec_from_file_location("create_blinded_labeling_sample", SCRIPT)
sampling = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sampling)


class BlindedSampleTests(unittest.TestCase):
    def setUp(self):
        self.eligibility = [
            {"bundle_path": "a.yaml", "upstream_project": "project-a", "bundle_kind": "manifest", "final_decision": "include_primary"},
            {"bundle_path": "b.yaml", "upstream_project": "project-a", "bundle_kind": "manifest", "final_decision": "include_primary"},
            {"bundle_path": "c.yaml", "upstream_project": "project-b", "bundle_kind": "helm-default", "final_decision": "include_primary"},
            {"bundle_path": "d.yaml", "upstream_project": "project-c", "bundle_kind": "manifest", "final_decision": "include_supporting"},
        ]
        self.rules = [
            {"id": "R1", "title": "Rule one", "category": "Network", "severity": "High"},
            {"id": "R2", "title": "Rule two", "category": "Auth", "severity": "Critical"},
        ]

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


if __name__ == "__main__":
    unittest.main()
