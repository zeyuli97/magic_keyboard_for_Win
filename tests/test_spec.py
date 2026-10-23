"""Manual-case traceability, not hardware verification."""
import json
import unittest
from test_config import ROOT
from macflow_config import CASE_PRIORITIES

class TraceabilityTests(unittest.TestCase):
    def test_inventory_matches_release_contract(self):
        rows = json.loads((ROOT / "tests/mapping-spec.yaml").read_text())["cases"]
        self.assertEqual(len(CASE_PRIORITIES), len(rows))
        self.assertEqual(set(CASE_PRIORITIES), {r["id"] for r in rows})
        for row in rows:
            self.assertEqual(CASE_PRIORITIES[row["id"]], row["priority"])
            self.assertTrue(row["acceptance"])

    def test_each_actual_rule_has_a_manual_case(self):
        rows = json.loads((ROOT / "tests/mapping-spec.yaml").read_text())["cases"]
        covered = {rule for row in rows for rule in row["rules"]}
        rules = json.loads((ROOT / "config/mappings.yaml").read_text())["mappings"]
        self.assertEqual({r["id"] for r in rules}, covered)
