import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "cluster_bootstrap.py"
spec = importlib.util.spec_from_file_location("cluster_bootstrap", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ClusterBootstrapTests(unittest.TestCase):
    def test_project_cluster_resampling_preserves_cluster_counts(self):
        prevalence = {
            "A": {"R": {"present": 8, "absent": 2}},
            "B": {"R": {"present": 0, "absent": 10}},
        }
        self.assertEqual(module.prevalence_estimate(["A", "A"], prevalence, "R"), 0.8)
        self.assertEqual(module.prevalence_estimate(["A", "B"], prevalence, "R"), 0.4)
        self.assertEqual(module.prevalence_estimate(["A", "B"], prevalence, "R", True), 0.5)

    def test_percentile_and_undefined_ratio(self):
        self.assertEqual(module.percentile([0.0, 1.0], 0.5), 0.5)
        self.assertIsNone(module.ratio(0, 0))

    def test_end_to_end_writes_all_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            prev = root / "prev.csv"
            mets = root / "metrics.csv"
            fields_prev = ["upstream_project", "rule_id", "present", "absent", "uncertain", "not_applicable", "bundles"]
            fields_met = ["upstream_project", "rule_id", "tp", "fp", "fn", "tn", "present", "absent", "uncertain", "not_applicable", "bundles"]
            with prev.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fields_prev); w.writeheader()
                for project, p, a in [("A", 8, 2), ("B", 0, 10), ("C", 4, 6)]:
                    w.writerow(dict(upstream_project=project, rule_id="R", present=p, absent=a, uncertain=0, not_applicable=0, bundles=p+a))
            with mets.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fields_met); w.writeheader()
                for project in ("A", "B", "C"):
                    w.writerow(dict(upstream_project=project, rule_id="R", tp=1, fp=0, fn=0, tn=1, present=1, absent=1, uncertain=0, not_applicable=0, bundles=2))
            out = root / "out"
            module.main = module.main
            import sys
            old = sys.argv
            try:
                sys.argv = ["cluster_bootstrap.py", "--project-prevalence", str(prev), "--project-metrics", str(mets), "--output-dir", str(out), "--replicates", "1000"]
                self.assertEqual(module.main(), 0)
            finally:
                sys.argv = old
            self.assertTrue((out / "cluster_bootstrap_prevalence.csv").exists())
            self.assertTrue((out / "cluster_bootstrap_scanner_metrics.csv").exists())
            self.assertTrue((out / "leave_one_project_out.csv").exists())


if __name__ == "__main__":
    unittest.main()
