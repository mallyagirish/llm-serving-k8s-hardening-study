import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RuleCatalogTests(unittest.TestCase):
    def test_catalog_has_28_unique_rules_with_required_metadata(self):
        catalog = json.loads((ROOT / "rules" / "catalog.json").read_text(encoding="utf-8"))
        rules = catalog["rules"]
        ids = [rule["id"] for rule in rules]
        self.assertEqual(len(rules), 28)
        self.assertEqual(len(ids), len(set(ids)))
        for rule in rules:
            for key in ("id", "title", "category", "severity", "automation", "assessment_semantics"):
                self.assertIn(key, rule)
            self.assertIn(rule["automation"], {"candidate_only", "manual_review"})

    def test_parse_exceptions_are_unique_and_exclude_only_documented_paths(self):
        data = json.loads((ROOT / "corpus" / "parse_exceptions.json").read_text(encoding="utf-8"))
        paths = [item["path"] for item in data["exceptions"]]
        self.assertEqual(len(paths), 7)
        self.assertEqual(len(paths), len(set(paths)))
        for item in data["exceptions"]:
            self.assertTrue(item["reason"])
            self.assertEqual(item["decision"], "exclude_from_primary_static_yaml_scan")


if __name__ == "__main__":
    unittest.main()
