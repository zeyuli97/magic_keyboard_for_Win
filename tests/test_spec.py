"""Manual-case traceability, not hardware verification."""
import json
from pathlib import Path
import tempfile
import unittest
from test_config import ROOT
from macflow_config import CASE_PRIORITIES, PROFILE_IDS, ConfigError, load_and_validate, load_coverage

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

    def test_common_app_profiles_have_required_edit_text_and_switch_cases(self):
        coverage = load_coverage(ROOT, load_and_validate(ROOT))
        added = {"edge", "wechat", "word", "excel", "powerpoint", "onenote", "outlook_classic",
                 "discord", "teams", "whatsapp", "github_desktop", "cursor"}
        for case_id in ("T01", "T02", "T07d"):
            with self.subTest(case=case_id):
                self.assertTrue(added <= coverage[case_id][1])
        self.assertIn("edge", coverage["T01b"][1])
        self.assertEqual({"vscode", "cursor"}, coverage["T04"][1])

    def coverage_with(self, edit):
        data = json.loads((ROOT / "tests/mapping-spec.yaml").read_text(encoding="utf-8"))
        edit({row["id"]: row for row in data["cases"]})
        with tempfile.TemporaryDirectory(prefix="macflow-coverage-test-") as temp:
            (Path(temp) / "tests").mkdir()
            (Path(temp) / "tests" / "mapping-spec.yaml").write_text(json.dumps(data), encoding="utf-8")
            return load_coverage(Path(temp), load_and_validate(ROOT))

    def test_map_cannot_claim_a_pass_or_an_unknown_status(self):
        for status in ("PASS", "passed", 123):
            with self.subTest(status=status):
                with self.assertRaisesRegex(ConfigError, "hardware_status"):
                    self.coverage_with(lambda rows: rows["T01"].update(hardware_status=status))

    def test_listed_profiles_and_rules_must_meet(self):
        with self.assertRaisesRegex(ConfigError, "explorer reaches none"):
            self.coverage_with(lambda rows: rows["T02"]["profiles"].append("explorer"))
        with self.assertRaisesRegex(ConfigError, "browser_new is reached by none"):
            self.coverage_with(lambda rows: rows["T09"]["rules"].append("browser_new"))
