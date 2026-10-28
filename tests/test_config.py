"""Configuration and release-gate tests use synthetic data, never hardware."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from macflow_config import ConfigError, assess_release, load_and_validate, validate_bundle

FIXTURES = Path(__file__).parent / "fixtures"


def fixture():
    return json.loads((FIXTURES / "minimal_bundle.json").read_text(encoding="utf-8"))


def make_root(path, bundle=None):
    bundle = fixture() if bundle is None else bundle
    config = path / "config"
    config.mkdir(parents=True, exist_ok=True)
    for name, data in bundle.items():
        (config / (name + ".yaml")).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    (config / "schema.json").write_bytes((FIXTURES / "schema.json").read_bytes())
    return path


class ConfigSemanticsTests(unittest.TestCase):
    def setUp(self):
        self.data = fixture()

    def reject(self):
        with self.assertRaises(ConfigError):
            validate_bundle(self.data)

    def test_valid_fixture_is_not_mutated(self):
        before = copy.deepcopy(self.data)
        self.assertIs(validate_bundle(self.data), self.data)
        self.assertEqual(before, self.data)

    def test_unknown_fields_fail_closed(self):
        self.data["mappings"]["mappings"][0]["send"] = "^c"
        self.reject()

    def test_boolean_is_not_integer_version_or_priority(self):
        for target, key in ((self.data["mappings"], "schema_version"), (self.data["mappings"]["mappings"][0], "priority")):
            original = target[key]
            target[key] = True
            self.reject()
            target[key] = original

    def test_unsafe_chords_and_extra_modifiers_rejected(self):
        for chord in ("RWin+c", "LControl+c", "LWin+Ctrl+c", "LWin+Alt+c", "LWin+Shift+Shift+c",
                      "LWin+F12", "*LWin+c", "LWin+C", "LWin+c\nLWin+x", "LAlt+RAlt+c"):
            with self.subTest(chord=chord):
                self.data["mappings"]["mappings"][0]["physical_chord"] = chord
                self.reject()

    def test_grammar_accepts_shift_brackets_and_navigation(self):
        for chord in ("LWin+[", "LWin+]", "LAlt+Shift+Left", "LWin+Shift+Tab", "LAlt+Backspace"):
            with self.subTest(chord=chord):
                self.data["mappings"]["mappings"][0]["physical_chord"] = chord
                validate_bundle(self.data)

    def test_unknown_action_rejected(self):
        self.data["mappings"]["mappings"][0]["action"] = "run_shell"
        self.reject()

    def test_unknown_context_rejected(self):
        self.data["mappings"]["mappings"][0]["contexts"] = ["everywhere"]
        self.reject()

    def test_duplicate_mapping_id_rejected(self):
        other = copy.deepcopy(self.data["mappings"]["mappings"][0])
        other["physical_chord"] = "LWin+v"
        self.data["mappings"]["mappings"].append(other)
        self.reject()

    def test_same_chord_context_priority_is_ambiguous(self):
        other = copy.deepcopy(self.data["mappings"]["mappings"][0])
        other["id"] = "conflicting_copy"
        self.data["mappings"]["mappings"].append(other)
        self.reject()

    def test_distinct_contexts_can_still_overlap_in_one_profile(self):
        other = copy.deepcopy(self.data["mappings"]["mappings"][0])
        other.update(id="text_copy", contexts=["text"])
        self.data["mappings"]["mappings"].append(other)
        self.reject()

    def test_explicit_different_priority_is_unambiguous(self):
        other = copy.deepcopy(self.data["mappings"]["mappings"][0])
        other.update(id="text_copy", contexts=["text"], priority=20)
        self.data["mappings"]["mappings"].append(other)
        validate_bundle(self.data)

    def test_blocked_rule_cannot_be_enabled(self):
        self.data["mappings"]["mappings"][0]["blocked_reason"] = "Implementation unavailable"
        self.reject()

    def test_backend_blocked_actions_cannot_be_enabled_without_reason(self):
        for action in ("browser_address", "explorer_delete", "terminal_copy", "terminal_paste"):
            with self.subTest(action=action):
                self.data["mappings"]["mappings"][0]["action"] = action
                self.reject()

    def test_disabled_blocked_rule_is_valid(self):
        self.data["mappings"]["mappings"][0].update(enabled=False, blocked_reason="待验证")
        validate_bundle(self.data)

    def test_unsafe_chord_cannot_be_enabled_using_an_action_alias(self):
        for chord in ("LWin+l", "LWin+Backspace"):
            self.data["mappings"]["mappings"][0]["physical_chord"] = chord
            self.reject()

    def test_known_profile_cannot_be_reassigned_to_terminal_process(self):
        self.data["apps"]["profiles"][0]["processes"] = ["windowsterminal.exe"]
        self.data["apps"]["bypass_processes"] = []
        self.reject()

    def test_profile_cannot_acquire_unapproved_context(self):
        self.data["apps"]["profiles"][0]["contexts"] = ["terminal"]
        self.reject()

    def test_non_vscode_profile_cannot_claim_integration(self):
        self.data["apps"]["profiles"][0]["requires_integration"] = True
        self.reject()

    def test_terminal_context_never_receives_generic_copy(self):
        self.data["mappings"]["mappings"][0]["contexts"] = ["terminal"]
        self.reject()

    def test_non_native_fallback_rejected(self):
        self.data["mappings"]["mappings"][0]["on_unmatched"] = "copy"
        self.reject()

    def test_enabled_process_profiles_must_not_overlap(self):
        other = copy.deepcopy(self.data["apps"]["profiles"][0])
        other["id"] = "notepad"
        self.data["apps"]["profiles"].append(other)
        self.reject()

    def test_enabled_profile_cannot_override_bypass(self):
        self.data["apps"]["bypass_processes"].append("chrome.exe")
        self.reject()

    def test_process_names_are_canonical_executables(self):
        for process in ("Chrome.exe", r"C:\Chrome.exe", "chrome", "chrome.exe|other.exe"):
            with self.subTest(process=process):
                self.data["apps"]["profiles"][0]["processes"] = [process]
                self.reject()

    def test_layouts_are_limited_to_us_and_simplified_chinese(self):
        for layouts in (["E0200804"], ["04090409", "00000409"], ["08040804", "08040804"], []):
            with self.subTest(layouts=layouts):
                self.data["apps"]["allowed_hkls"] = layouts
                self.reject()
        # Removing 08040804 is the configuration rollback to Chinese-input bypass.
        for layouts in (["04090409"], ["04090409", "08040804"]):
            with self.subTest(layouts=layouts):
                self.data["apps"]["allowed_hkls"] = layouts
                validate_bundle(self.data)

    def test_removed_ime_english_mode_field_is_rejected(self):
        self.data["apps"]["ime_english_mode_hkls"] = ["08040804"]
        self.reject()

    def test_rule_count_is_capped_at_the_runtime_limit(self):
        # The AHK loader accepts rule_count 1..256; Python must not pass more.
        template = self.data["mappings"]["mappings"][0]
        self.data["mappings"]["mappings"] = [dict(template, id=f"rule{n}", priority=n) for n in range(257)]
        with self.assertRaisesRegex(ConfigError, "256"):
            validate_bundle(self.data)
        self.data["mappings"]["mappings"].pop()
        validate_bundle(self.data)

    def test_unpaired_surrogate_is_rejected_before_generation(self):
        # Valid JSON, but the generator could not write it as UTF-16.
        self.data["mappings"]["mappings"][0].update(enabled=False, blocked_reason="\ud800")
        self.reject()

    def test_fixture_schema_matches_the_real_schema(self):
        self.assertEqual((ROOT / "config" / "schema.json").read_bytes(), (FIXTURES / "schema.json").read_bytes())

    def test_windows_terminal_profile_stays_disabled(self):
        self.data["apps"]["profiles"].append({
            "id": "windows_terminal", "processes": ["windowsterminal.exe"],
            "contexts": ["terminal"], "enabled": True, "requires_integration": False,
        })
        self.reject()

    def test_bridged_editors_cannot_skip_manual_integration_guard(self):
        for name, process in (("vscode", "code.exe"), ("cursor", "cursor.exe")):
            with self.subTest(profile=name):
                self.data = fixture()
                self.data["apps"]["profiles"].append({
                    "id": name, "processes": [process], "contexts": ["vscode"],
                    "enabled": True, "requires_integration": False,
                })
                self.reject()


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.data = fixture()

    def all_pass(self):
        for case in self.data["release"]["cases"]:
            if case["id"] != "T07c":
                case["status"] = "PASS"
                case["reason"] = "Synthetic unit-test evidence; not a hardware result."

    def test_unexecuted_cases_cannot_pass_any_gate(self):
        gates = assess_release(self.data)
        self.assertFalse(gates["prototype"]["accepted"])
        self.assertFalse(gates["v1"]["accepted"])

    def test_blocked_p0_blocks_both_gates_even_when_other_claims_pass(self):
        self.all_pass()
        case = next(c for c in self.data["release"]["cases"] if c["id"] == "T03")
        case.update(status="BLOCKED", reason="No terminal selection adapter")
        gates = assess_release(self.data)
        self.assertEqual(["T03"], [c["id"] for c in gates["prototype"]["blocking"]])
        self.assertFalse(gates["prototype"]["accepted"])
        self.assertFalse(gates["v1"]["accepted"])

    def test_p1_may_block_v1_without_blocking_prototype(self):
        self.all_pass()
        case = next(c for c in self.data["release"]["cases"] if c["id"] == "T01b")
        case.update(status="BLOCKED", reason="Command+L unresolved")
        gates = assess_release(self.data)
        self.assertTrue(gates["prototype"]["accepted"])
        self.assertFalse(gates["v1"]["accepted"])

    def test_pass_claims_do_not_upgrade_development_preview(self):
        self.all_pass()
        before = copy.deepcopy(self.data)
        gates = assess_release(self.data)
        self.assertTrue(gates["v1"]["accepted"])
        self.assertEqual(before, self.data)
        self.assertEqual("DEVELOPMENT PREVIEW", self.data["release"]["delivery_status"])

    def test_p0_cannot_be_silently_removed_or_waived(self):
        for mutation in ("remove", "waive", "relabel"):
            data = fixture()
            case = next(c for c in data["release"]["cases"] if c["id"] == "T03")
            if mutation == "remove":
                data["release"]["cases"].remove(case)
            elif mutation == "waive":
                case["required_prototype"] = False
            else:
                case["priority"] = "P1"
            with self.subTest(mutation=mutation), self.assertRaises(ConfigError):
                assess_release(data)

    def test_empty_or_duplicate_inventory_cannot_pass(self):
        for cases in ([], [self.data["release"]["cases"][0]] * 14):
            self.data["release"]["cases"] = cases
            with self.assertRaises(ConfigError):
                assess_release(self.data)

    def test_failed_and_untested_required_results_never_pass(self):
        for status in ("FAIL", "NOT TESTED"):
            self.all_pass()
            self.data["release"]["cases"][0].update(status=status, reason="Synthetic negative scenario")
            self.assertFalse(assess_release(self.data)["prototype"]["accepted"])

    def test_blocked_or_failed_cases_need_reason(self):
        for status in ("FAIL", "BLOCKED"):
            self.data["release"]["cases"][0].update(status=status, reason="")
            with self.assertRaises(ConfigError):
                assess_release(self.data)

    def coverage(self, **cases):
        result = {case["id"]: (frozenset(), frozenset()) for case in self.data["release"]["cases"]}
        for case_id, (rules, profiles) in cases.items():
            result[case_id] = (frozenset(rules), frozenset(profiles))
        return result

    def test_p1_only_mapping_must_pass_or_close_for_prototype(self):
        self.all_pass()
        case = next(c for c in self.data["release"]["cases"] if c["id"] == "T01b")
        case.update(status="BLOCKED", reason="Synthetic deferred P1 case")
        coverage = self.coverage(T01b=({"copy"}, {"chrome"}))
        gates = assess_release(self.data, coverage)
        self.assertFalse(gates["prototype"]["accepted"])
        self.assertEqual(["UNVERIFIED-MAPPINGS"], [row["id"] for row in gates["prototype"]["blocking"]])
        self.assertIn("T01b BLOCKED", gates["prototype"]["blocking"][0]["reason"])
        # Closing the mapping is the specification's alternative to a P1 PASS.
        self.data["mappings"]["mappings"][0]["enabled"] = False
        self.assertTrue(assess_release(self.data, coverage)["prototype"]["accepted"])

    def test_mapping_without_any_case_blocks_both_gates(self):
        self.all_pass()
        gates = assess_release(self.data, self.coverage())
        for name in ("prototype", "v1"):
            with self.subTest(gate=name):
                self.assertFalse(gates[name]["accepted"])
                self.assertEqual(["UNCOVERED-MAPPINGS"], [row["id"] for row in gates[name]["blocking"]])

    def test_case_for_another_profile_does_not_cover_a_mapping(self):
        self.all_pass()
        gates = assess_release(self.data, self.coverage(T01=({"copy"}, {"notepad"})))
        self.assertFalse(gates["prototype"]["accepted"])

    def test_required_case_coverage_adds_no_extra_gap(self):
        self.all_pass()
        gates = assess_release(self.data, self.coverage(T01=({"copy"}, {"chrome"})))
        self.assertTrue(gates["prototype"]["accepted"])
        self.assertTrue(gates["v1"]["accepted"])


class FileValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="macflow-config-test-")
        self.root = make_root(Path(self.temp.name))

    def tearDown(self):
        self.temp.cleanup()

    def test_schema_and_data_load_together(self):
        self.assertEqual(fixture(), load_and_validate(self.root))

    def test_missing_file_fails_closed(self):
        (self.root / "config" / "apps.yaml").unlink()
        with self.assertRaises(ConfigError):
            load_and_validate(self.root)

    def test_yaml_only_syntax_duplicate_keys_and_nonfinite_numbers_rejected(self):
        for raw in ("schema_version: 1\nmappings: []", '{"schema_version":1,"schema_version":1}', '{"schema_version":NaN}'):
            (self.root / "config" / "mappings.yaml").write_text(raw, encoding="utf-8")
            with self.subTest(raw=raw), self.assertRaises(ConfigError):
                load_and_validate(self.root)

    def test_schema_specific_bound_is_enforced(self):
        path = self.root / "config" / "schema.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema["mappings"]["properties"]["mappings"]["items"]["properties"]["priority"]["maximum"] = 9
        path.write_text(json.dumps(schema))
        with self.assertRaisesRegex(ConfigError, "maximum"):
            load_and_validate(self.root)

    def test_unsupported_schema_keyword_is_not_ignored(self):
        path = self.root / "config" / "schema.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema["mappings"]["oneOf"] = []
        path.write_text(json.dumps(schema))
        with self.assertRaisesRegex(ConfigError, "unsupported schema"):
            load_and_validate(self.root)

    def test_oversized_integer_is_a_config_error(self):
        # Beyond Python's digit limit json raises a plain ValueError.
        (self.root / "config" / "apps.yaml").write_text('{"schema_version": ' + "9" * 5000 + "}", encoding="utf-8")
        with self.assertRaises(ConfigError):
            load_and_validate(self.root)

    def test_schema_boolean_does_not_count_as_integer_enum(self):
        path = self.root / "config" / "apps.yaml"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["schema_version"] = True
        path.write_text(json.dumps(data))
        with self.assertRaises(ConfigError):
            load_and_validate(self.root)

    def test_cli_distinguishes_valid_config_from_accepted_gate(self):
        command = [sys.executable, str(ROOT / "tools" / "validate-config.py"), "--root", str(self.root), "--json"]
        valid = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(0, valid.returncode, valid.stderr)
        self.assertFalse(json.loads(valid.stdout)["gates"]["prototype"]["accepted"])
        gated = subprocess.run(command + ["--gate", "prototype"], text=True, capture_output=True)
        self.assertEqual(2, gated.returncode, gated.stderr)

    def test_cli_without_coverage_map_keeps_config_valid_but_rejects_gates(self):
        command = [sys.executable, str(ROOT / "tools" / "validate-config.py"), "--root", str(self.root), "--json"]
        valid = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(0, valid.returncode, valid.stderr)
        for gate in json.loads(valid.stdout)["gates"].values():
            self.assertFalse(gate["accepted"])
            self.assertIn("COVERAGE", [row["id"] for row in gate["blocking"]])

    def test_cli_escapes_unencodable_reasons_instead_of_crashing(self):
        bundle = fixture()
        bundle["release"]["cases"][0]["reason"] = "等待真机测试"
        make_root(self.root, bundle)
        # A redirected stream on the Windows test host uses the cp1252 code page.
        environment = dict(os.environ, PYTHONIOENCODING="cp1252")
        command = [sys.executable, str(ROOT / "tools" / "validate-config.py"), "--root", str(self.root)]
        text = subprocess.run(command, capture_output=True, env=environment)
        self.assertEqual(0, text.returncode, text.stderr)
        self.assertIn(b"\\u7b49", text.stdout)
        report = subprocess.run(command + ["--json"], capture_output=True, env=environment)
        self.assertEqual(0, report.returncode, report.stderr)
        reasons = [row["reason"] for row in json.loads(report.stdout)["gates"]["prototype"]["blocking"]]
        self.assertIn("等待真机测试", reasons)


if __name__ == "__main__":
    unittest.main()
