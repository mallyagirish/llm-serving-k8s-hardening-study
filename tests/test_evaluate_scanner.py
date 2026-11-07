import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_scanner.py"
spec = importlib.util.spec_from_file_location("evaluate_scanner", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class EvaluationHelpersTests(unittest.TestCase):
    def test_normalizes_scanner_and_label_paths(self):
        self.assertEqual(module.norm_bundle_path("corpus/rendered/a/manifest.yaml"), "rendered/a/manifest.yaml")
        self.assertEqual(module.norm_bundle_path("rendered/a/manifest.yaml"), "rendered/a/manifest.yaml")

    def test_safe_division(self):
        self.assertEqual(module.safe_div(2, 4), 0.5)
        self.assertIsNone(module.safe_div(0, 0))


if __name__ == "__main__":
    unittest.main()
