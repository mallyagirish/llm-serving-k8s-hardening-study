import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_scanner.py"
spec = importlib.util.spec_from_file_location("evaluate_scanner", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class EvaluationTests(unittest.TestCase):
    def test_normalizes_scanner_and_label_paths(self):
        self.assertEqual(module.norm_bundle_path("corpus/rendered/a/manifest.yaml"), "rendered/a/manifest.yaml")
        self.assertEqual(module.norm_bundle_path("rendered/a/manifest.yaml"), "rendered/a/manifest.yaml")

    def test_safe_division(self):
        self.assertEqual(module.safe_div(2, 4), 0.5)
        self.assertIsNone(module.safe_div(0, 0))

    def test_end_to_end_bundle_rule_aggregation_and_metrics(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            labels_path = root / "labels.csv"
            candidates_path = root / "candidates.jsonl"
            inventory_path = root / "inventory.jsonl"
            out = root / "out"
            rules = sorted(module.SCANNER_RULES)
            bundles = [
                ("rendered/a.yaml", "ha", "project-a", "PRESENT"),
                ("rendered/b.yaml", "hb", "project-b", "ABSENT"),
            ]
            with labels_path.open("w", newline="", encoding="utf-8") as f:
                fields = ["bundle_path", "bundle_sha256", "upstream_project", "rule_id", "label"]
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                for path, digest, project, label in bundles:
                    for rule in rules:
                        writer.writerow({
                            "bundle_path": path, "bundle_sha256": digest,
                            "upstream_project": project, "rule_id": rule, "label": label,
                        })
            inventory = [
                {"path": path, "sha256": digest}
                for path, digest, _, _ in bundles
            ]
            inventory_path.write_text(
                "".join(json.dumps(x) + "\n" for x in inventory), encoding="utf-8"
            )
            candidate = {
                "rule_id": "LLM-WL-01", "source_file": "corpus/rendered/a.yaml",
                "source_sha256": "ha", "status": "candidate_for_human_review",
            }
            candidates_path.write_text(json.dumps(candidate) + "\n", encoding="utf-8")
            argv = [
                "evaluate_scanner.py", "--labels", str(labels_path),
                "--candidates", str(candidates_path), "--inventory", str(inventory_path),
                "--output-dir", str(out),
            ]
            with patch.object(sys, "argv", argv):
                with self.assertRaises(SystemExit) as exit_code:
                    module.main()
            self.assertEqual(exit_code.exception.code, 0)
            metrics = list(csv.DictReader((out / "scanner_metrics.csv").open(encoding="utf-8")))
            wl01 = next(row for row in metrics if row["rule_id"] == "LLM-WL-01")
            self.assertEqual((wl01["tp"], wl01["fp"], wl01["fn"], wl01["tn"]), ("1", "0", "0", "1"))
            wl02 = next(row for row in metrics if row["rule_id"] == "LLM-WL-02")
            self.assertEqual((wl02["tp"], wl02["fp"], wl02["fn"], wl02["tn"]), ("0", "0", "1", "1"))
            summary = json.loads((out / "evaluation_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["input_counts"]["bundles"], 2)
            self.assertEqual(summary["input_counts"]["label_rows"], 2 * len(rules))


if __name__ == "__main__":
    unittest.main()
