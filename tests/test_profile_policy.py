"""Policy parity and implemented-handler coverage; no AHK is executed."""
import copy
import json
import unittest

from test_config import ROOT
from macflow_config import (
    ACTIONS, CONTEXTS, PROFILE_CONTRACTS, PROFILE_ACTIONS, BLOCKED_ACTIONS,
    PROTECTED_CHORDS, ALLOWED_HKLS, ConfigError, load_and_validate, validate_bundle,
)
from ahk_literals import (
    function_tokens, return_literal, static_map, contains,
    action_blocks_with_output,
)


class ActualConfigurationCapabilityTests(unittest.TestCase):
    def setUp(self):
        self.bundle = load_and_validate(ROOT)

    def test_actual_configuration_remains_valid(self):
        validate_bundle(self.bundle)

    def test_actual_undo_find_cannot_expand_into_explorer(self):
        for rule_id in ("global_undo", "global_find"):
            for profile_enabled in (True, False):
                with self.subTest(rule=rule_id, profile_enabled=profile_enabled):
                    data = copy.deepcopy(self.bundle)
                    rule = next(row for row in data["mappings"]["mappings"] if row["id"] == rule_id)
                    rule["contexts"].append("explorer")
                    next(row for row in data["apps"]["profiles"] if row["id"] == "explorer")["enabled"] = profile_enabled
                    with self.assertRaisesRegex(ConfigError, "explorer does not implement"):
                        validate_bundle(data)

    def test_actual_browser_action_cannot_expand_into_editor(self):
        for profile_id, context in (("notepad", "edit"), ("vscode", "vscode"), ("explorer", "explorer")):
            with self.subTest(profile=profile_id):
                data = copy.deepcopy(self.bundle)
                rule = next(row for row in data["mappings"]["mappings"] if row["id"] == "browser_new")
                rule["contexts"].append(context)
                with self.assertRaisesRegex(ConfigError, "does not implement"):
                    validate_bundle(data)

    def test_each_implemented_action_is_valid_for_its_profile_even_disabled(self):
        for profile in self.bundle["apps"]["profiles"]:
            for action in PROFILE_ACTIONS[profile["id"]]:
                for enabled in (True, False):
                    with self.subTest(profile=profile["id"], action=action, profile_enabled=enabled):
                        data = copy.deepcopy(self.bundle)
                        isolated = copy.deepcopy(profile)
                        isolated["enabled"] = enabled
                        data["apps"]["profiles"] = [isolated]
                        data["mappings"]["mappings"] = [{
                            "id": "capability_probe", "enabled": True,
                            "physical_chord": "LWin+c", "contexts": list(profile["contexts"]),
                            "action": action, "priority": 10, "on_unmatched": "passthrough",
                            "blocked_reason": "",
                        }]
                        validate_bundle(data)

    def test_every_unimplemented_action_is_rejected_for_each_profile(self):
        for profile in self.bundle["apps"]["profiles"]:
            for action in ACTIONS - PROFILE_ACTIONS[profile["id"]]:
                with self.subTest(profile=profile["id"], action=action):
                    data = copy.deepcopy(self.bundle)
                    isolated = copy.deepcopy(profile)
                    isolated["enabled"] = False
                    data["apps"]["profiles"] = [isolated]
                    data["mappings"]["mappings"] = [{
                        "id": "capability_probe", "enabled": True,
                        "physical_chord": "LWin+c", "contexts": list(profile["contexts"]),
                        "action": action, "priority": 10, "on_unmatched": "passthrough",
                        "blocked_reason": "",
                    }]
                    with self.assertRaises(ConfigError):
                        validate_bundle(data)

    def test_disabled_unsupported_rule_does_not_claim_a_capability(self):
        data = copy.deepcopy(self.bundle)
        rule = next(row for row in data["mappings"]["mappings"] if row["id"] == "global_undo")
        rule["contexts"].append("explorer")
        rule["enabled"] = False
        validate_bundle(data)


class PythonAhkPolicyParityTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / "src/ahk/config.ahk").read_text(encoding="utf-8")
        self.schema = json.loads((ROOT / "config/schema.json").read_text(encoding="utf-8"))

    def test_literal_allowlists_match_python_and_are_consumed_by_loader(self):
        policies = {
            "MF_ConfigActions": ACTIONS,
            "MF_ConfigContexts": CONTEXTS,
            "MF_ConfigBlockedActions": BLOCKED_ACTIONS,
            "MF_ConfigProtectedChords": PROTECTED_CHORDS,
            "MF_ConfigAllowedLayouts": set(ALLOWED_HKLS),
        }
        loader = function_tokens(self.source, "MF_LoadConfig")
        for name, expected in policies.items():
            with self.subTest(policy=name):
                values = return_literal(self.source, name)
                self.assertEqual(len(values), len(set(values)), "Duplicate policy entry")
                self.assertEqual(set(expected), set(values))
                if name == "MF_ConfigContexts":
                    helper = function_tokens(self.source, "MF_ValidateContexts")
                    self.assertTrue(contains(helper, [name, "(", ")"]))
                    for owner in ("rule", "profile"):
                        self.assertTrue(contains(loader, ["MF_ValidateContexts", "(", owner, ".", "Contexts", ")"]))
                else:
                    self.assertTrue(contains(loader, [name, "(", ")"]), f"Loader must use {name}")

    def test_fixed_process_and_context_policies_match(self):
        actual = return_literal(self.source, "MF_ConfigProfilePolicy")
        self.assertTrue(contains(function_tokens(self.source, "MF_LoadConfig"), ["MF_ConfigProfilePolicy", "(", ")"]))
        expected = {
            name: {"Process": process, "Contexts": set(contexts)}
            for name, (process, contexts) in PROFILE_CONTRACTS.items()
        }
        self.assertEqual(set(expected), set(actual))
        for name, policy in actual.items():
            self.assertEqual({"Process", "Contexts"}, set(policy))
            policy["Contexts"] = set(policy["Contexts"])
            self.assertEqual(expected[name], policy)

    def test_implemented_action_policies_match(self):
        actual = return_literal(self.source, "MF_ProfileActionPolicy")
        self.assertEqual(PROFILE_ACTIONS, {name: frozenset(actions) for name, actions in actual.items()})
        self.assertEqual([], actual["windows_terminal"])
        loader = function_tokens(self.source, "MF_LoadConfig")
        self.assertTrue(contains(loader, ["MF_ProfileActionPolicy", "(", ")"]))

    def test_schema_enums_match_shared_policy(self):
        rule = self.schema["mappings"]["properties"]["mappings"]["items"]["properties"]
        app = self.schema["apps"]["properties"]
        profile = app["profiles"]["items"]["properties"]
        self.assertEqual(ACTIONS, set(rule["action"]["enum"]))
        self.assertEqual(CONTEXTS, set(rule["contexts"]["items"]["enum"]))
        self.assertEqual(CONTEXTS, set(profile["contexts"]["items"]["enum"]))
        self.assertEqual(set(PROFILE_CONTRACTS), set(profile["id"]["enum"]))
        self.assertEqual(set(ALLOWED_HKLS), set(app["allowed_hkls"]["items"]["enum"]))


class ActualHandlerCoverageTests(unittest.TestCase):
    def test_capabilities_are_backed_by_real_dispatch_maps_and_profile_guards(self):
        global_body = function_tokens((ROOT / "src/ahk/global.ahk").read_text(encoding="utf-8"), "MF_GlobalAction")
        browser_body = function_tokens((ROOT / "src/ahk/browser.ahk").read_text(encoding="utf-8"), "MF_BrowserAction")
        explorer_body = function_tokens((ROOT / "src/ahk/explorer.ahk").read_text(encoding="utf-8"), "MF_ExplorerAction")
        terminal_body = function_tokens((ROOT / "src/ahk/terminal.ahk").read_text(encoding="utf-8"), "MF_TerminalAction")
        router_source = (ROOT / "src/ahk/router.ahk").read_text(encoding="utf-8")
        router = function_tokens(router_source, "MF_CurrentProfile")
        dispatch = function_tokens(router_source, "MF_RunAction")

        generic = set(static_map(global_body, "keys"))
        bridge = set(static_map(global_body, "bridge"))
        browser = set(static_map(browser_body, "keys"))
        explorer_specific = action_blocks_with_output(explorer_body)
        for body, variable in ((global_body, "keys"), (global_body, "bridge"), (browser_body, "keys")):
            self.assertTrue(contains(body, ["if", "!", variable, ".", "Has", "(", "action", ")", "return", "false"]))
            self.assertTrue(contains(body, ["MF_SendTap", "(", variable, "[", "action", "]", ")", "return", "true"]))
        self.assertTrue(contains(global_body, [
            "if", "profile", ".", "Id", "!=", "chrome", "&&", "profile", ".", "Id", "!=", "notepad",
            "&&", "profile", ".", "Id", "!=", "explorer", "return", "false",
        ]))
        self.assertTrue(contains(global_body, ["if", "profile", ".", "Id", "=", "vscode", "{", "if", "!", "MF", ".", "VscodeReady", "return", "false"]))
        self.assertTrue(contains(browser_body, ["profile", ".", "Id", "!=", "chrome", "return", "false"]))
        self.assertTrue(contains(explorer_body, ["profile", ".", "Id", "!=", "explorer", "return", "false"]))
        self.assertTrue(contains(terminal_body, ["profile", ".", "Id", "!=", "vscode", "||", "!", "MF", ".", "VscodeReady", "return", "false"]))

        # Derive Explorer's limited generic subset from its actual rejecting guard.
        values = [token[1] for token in global_body]
        prefix = ["if", "profile", ".", "Id", "=", "explorer", "&&"]
        start = next(index for index in range(len(values)) if values[index:index + len(prefix)] == prefix)
        index = start + len(prefix)
        explorer_generic = set()
        while values[index:index + 2] == ["action", "!="]:
            explorer_generic.add(values[index + 2])
            index += 3
            if values[index] != "&&":
                break
            index += 1
        self.assertEqual(["return", "false"], values[index:index + 2])
        self.assertTrue(explorer_generic <= generic)

        switches = {"app_next", "app_previous"}
        self.assertTrue(contains(global_body, ["if", "action", "=", "app_next", "||", "action", "=", "app_previous", "{"]))
        self.assertTrue(contains(global_body, ["MF_HoldSynthetic", "(", "LAlt", ")"]))
        self.assertTrue(contains(global_body, ["MF_SendTap", "(", "action", "=", "app_previous"]))

        actual = {
            "chrome": generic | browser | switches,
            "notepad": generic | switches,
            "vscode": bridge | switches,
            "explorer": explorer_generic | explorer_specific | switches,
            "windows_terminal": set(),
        }
        # The standalone host is unreachable; terminal aliases are globally blocked.
        self.assertTrue(contains(router, ["if", "!", "profile", ".", "Enabled", "||"]))
        config = load_and_validate(ROOT)
        terminal = next(p for p in config["apps"]["profiles"] if p["id"] == "windows_terminal")
        self.assertFalse(terminal["enabled"])
        self.assertTrue({"terminal_copy", "terminal_paste"} <= BLOCKED_ACTIONS)
        self.assertEqual(PROFILE_ACTIONS, actual)
        for handler in ("MF_GlobalAction", "MF_BrowserAction", "MF_ExplorerAction", "MF_TerminalAction"):
            self.assertTrue(contains(dispatch, ["if", handler, "(", "action", ",", "profile", ")", "return"]))


if __name__ == "__main__":
    unittest.main()
