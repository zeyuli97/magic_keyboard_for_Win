"""Manual-case traceability, not hardware verification."""
import json
import unittest
from test_config import ROOT
from macflow_config import CASE_PRIORITIES, PROFILE_IDS, load_and_validate, load_coverage

class TraceabilityTests(unittest.TestCase):
    def test_inventory_matches_release_contract(self):
        rows = json.loads((ROOT / "tests/mapping-spec.yaml").read_text(encoding="utf-8"))["cases"]
        self.assertEqual(len(CASE_PRIORITIES), len(rows))
        self.assertEqual(set(CASE_PRIORITIES), {r["id"] for r in rows})
        for row in rows:
            self.assertEqual(CASE_PRIORITIES[row["id"]], row["priority"])
            self.assertTrue(row["acceptance"])

    def test_each_actual_rule_has_a_manual_case(self):
        rows = json.loads((ROOT / "tests/mapping-spec.yaml").read_text(encoding="utf-8"))["cases"]
        covered = {rule for row in rows for rule in row["rules"]}
        rules = json.loads((ROOT / "config/mappings.yaml").read_text(encoding="utf-8"))["mappings"]
        self.assertEqual({r["id"] for r in rules}, covered)

    def test_coverage_map_names_where_each_case_exercises_its_rules(self):
        coverage = load_coverage(ROOT, load_and_validate(ROOT))
        self.assertEqual(set(CASE_PRIORITIES), set(coverage))
        for case_id, (rules, profiles) in coverage.items():
            with self.subTest(case=case_id):
                self.assertTrue(profiles <= PROFILE_IDS)
                self.assertTrue(profiles or not rules)
