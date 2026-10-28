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
    function_tokens, return_literal, static_map, static_list, contains,
    action_blocks_with_output,
)

# Additional edit/text profiles; Outlook overrides find with mail search.
ADDED_APPS = {
    "claude": "claude.exe", "codex": "chatgpt.exe",
    "visual_studio": "devenv.exe", "unreal": "unrealeditor.exe",
    "outlook": "olk.exe",
    "wechat": "wechat.exe", "word": "winword.exe", "excel": "excel.exe",
    "powerpoint": "powerpnt.exe", "onenote": "onenote.exe",
    "outlook_classic": "outlook.exe",
}
BROWSER_APPS = {"chrome": "chrome.exe", "edge": "msedge.exe"}
# Option+Up/Down send Ctrl+Up/Down only where that moves by paragraph
# (2026-10-24, decisions.md #15).
PARAGRAPH_ACTIONS = frozenset(("paragraph_up", "paragraph_down", "select_paragraph_up", "select_paragraph_down"))
PARAGRAPH_PROFILES = frozenset(("chrome", "edge", "notepad", "claude", "codex", "word", "onenote"))


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

    def test_added_apps_map_like_notepad_without_browser_or_terminal_contexts(self):
        profiles = {row["id"]: row for row in self.bundle["apps"]["profiles"]}
        for profile_id, process in ADDED_APPS.items():
            with self.subTest(profile=profile_id):
                paragraph = profile_id in PARAGRAPH_PROFILES
                contexts = {"edit", "text"} | ({"paragraph"} if paragraph else set())
                self.assertEqual((process, contexts), PROFILE_CONTRACTS[profile_id])
                self.assertEqual(PROFILE_ACTIONS["notepad"] - (set() if paragraph else PARAGRAPH_ACTIONS),
                                 PROFILE_ACTIONS[profile_id])
                row = profiles[profile_id]
                self.assertEqual([process], row["processes"])
                self.assertEqual(contexts, set(row["contexts"]))
                self.assertTrue(row["enabled"])
                self.assertFalse(row["requires_integration"])
                for context in ("browser", "terminal", "vscode") + (() if paragraph else ("paragraph",)):
                    data = copy.deepcopy(self.bundle)
                    next(p for p in data["apps"]["profiles"] if p["id"] == profile_id)["contexts"].append(context)
                    with self.assertRaisesRegex(ConfigError, "fixed safety boundary"):
                        validate_bundle(data)

    def test_option_up_down_reach_only_paragraph_profiles(self):
        rules = [row for row in self.bundle["mappings"]["mappings"] if row["action"] in PARAGRAPH_ACTIONS]
        self.assertEqual({"LAlt+Up", "LAlt+Down", "LAlt+Shift+Up", "LAlt+Shift+Down"},
                         {row["physical_chord"] for row in rules})
        self.assertEqual(PARAGRAPH_ACTIONS, {row["action"] for row in rules})
        for row in rules:
            self.assertEqual(["paragraph"], row["contexts"])
            self.assertTrue(row["enabled"])
        reached = {p["id"] for p in self.bundle["apps"]["profiles"] if "paragraph" in p["contexts"]}
        self.assertEqual(PARAGRAPH_PROFILES, reached)
        self.assertEqual(PARAGRAPH_PROFILES, {name for name, (_, contexts) in PROFILE_CONTRACTS.items()
                                              if "paragraph" in contexts})
        for profile_id in ("vscode", "visual_studio", "unreal", "outlook", "explorer", "windows_terminal",
                           "wechat", "excel", "powerpoint", "outlook_classic"):
            with self.subTest(profile=profile_id):
                self.assertFalse(PARAGRAPH_ACTIONS & PROFILE_ACTIONS[profile_id])
                data = copy.deepcopy(self.bundle)
                next(p for p in data["apps"]["profiles"] if p["id"] == profile_id)["contexts"].append("paragraph")
                with self.assertRaisesRegex(ConfigError, "fixed safety boundary"):
                    validate_bundle(data)

    def test_edge_has_browser_capabilities_without_shared_webview_access(self):
        profiles = {row["id"]: row for row in self.bundle["apps"]["profiles"]}
        self.assertEqual(PROFILE_ACTIONS["chrome"], PROFILE_ACTIONS["edge"])
        for name, process in BROWSER_APPS.items():
            with self.subTest(profile=name):
                profile = profiles[name]
                self.assertEqual([process], profile["processes"])
                self.assertEqual({"edit", "text", "paragraph", "browser"}, set(profile["contexts"]))
                self.assertTrue(profile["enabled"])
                self.assertFalse(profile["requires_integration"])
                data = copy.deepcopy(self.bundle)
                next(p for p in data["apps"]["profiles"] if p["id"] == name)["processes"] = ["msedgewebview2.exe"]
                with self.assertRaisesRegex(ConfigError, "fixed safety boundary"):
                    validate_bundle(data)

    def test_common_apps_cannot_take_over_other_processes(self):
        for name in ("wechat", "word", "excel", "powerpoint", "onenote", "outlook_classic"):
            for process in ("cmd.exe", "msedgewebview2.exe", "unlisted.exe"):
                for enabled in (True, False):
                    with self.subTest(profile=name, process=process, enabled=enabled):
                        data = copy.deepcopy(self.bundle)
                        profile = next(p for p in data["apps"]["profiles"] if p["id"] == name)
                        profile.update(processes=[process], enabled=enabled)
                        with self.assertRaisesRegex(ConfigError, "fixed safety boundary"):
                            validate_bundle(data)

    def test_outlook_cannot_expand_to_classic_mail_or_shared_webview_host(self):
        for process in ("outlook.exe", "hxoutlook.exe", "msedgewebview2.exe"):
            for replace in (True, False):
                with self.subTest(process=process, replace=replace):
                    data = copy.deepcopy(self.bundle)
                    profile = next(p for p in data["apps"]["profiles"] if p["id"] == "outlook")
                    profile["processes"] = [process] if replace else ["olk.exe", process]
                    with self.assertRaisesRegex(ConfigError, "fixed safety boundary"):
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

    def test_loader_capacity_tracks_fixed_profile_inventory(self):
        # The expanded config exceeds the old hard-coded 16-profile ceiling.
        loader = function_tokens(self.source, "MF_LoadConfig")
        self.assertTrue(contains(loader, [
            "profilePolicy", ":=", "MF_ConfigProfilePolicy", "(", ")",
            "profileCount", ":=", "MF_IniInteger", "(", "path", ",", "meta", ",",
            "profile_count", ",", "1", ",", "profilePolicy", ".", "Count", ")",
        ]))

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
    def test_outlook_variants_keep_their_distinct_find_outputs(self):
        body = function_tokens((ROOT / "src/ahk/global.ahk").read_text(encoding="utf-8"), "MF_GlobalAction")
        # The Outlook-only override must return before the generic Ctrl+F send.
        self.assertTrue(contains(body, [
            "if", "profile", ".", "Id", "=", "outlook", "&&", "action", "=", "find", "{",
            "MF_SendTap", "(", "^e", ")", "return", "true", "}",
            "if", "profile", ".", "Id", "=", "outlook_classic", "&&", "action", "=", "find", "{",
            "MF_SendTap", "(", "{F4}", ")", "return", "true", "}",
            "MF_SendTap", "(", "keys", "[", "action", "]", ")",
        ]))
        self.assertEqual("^f", static_map(body, "keys")["find"])

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
        paragraph = set(static_map(global_body, "paragraph"))
        self.assertEqual(PARAGRAPH_ACTIONS, paragraph)
        self.assertFalse(paragraph & generic)
        # Paragraph keys are sent only to a profile that has the paragraph context.
        self.assertTrue(contains(global_body, [
            "if", "paragraph", ".", "Has", "(", "action", ")", "{",
            "if", "!", "MF_Contains", "(", "profile", ".", "Contexts", ",", "paragraph", ")", "return", "false",
            "MF_SendTap", "(", "paragraph", "[", "action", "]", ")", "return", "true", "}",
        ]))
        explorer_specific = action_blocks_with_output(explorer_body)
        for body, variable in ((global_body, "keys"), (global_body, "bridge"), (browser_body, "keys")):
            self.assertTrue(contains(body, ["if", "!", variable, ".", "Has", "(", "action", ")", "return", "false"]))
            self.assertTrue(contains(body, ["MF_SendTap", "(", variable, "[", "action", "]", ")", "return", "true"]))
        direct = static_list(global_body, "direct")
        self.assertEqual(len(direct), len(set(direct)), "Duplicate direct profile")
        self.assertEqual({*BROWSER_APPS, "notepad", "explorer", *ADDED_APPS}, set(direct))
        self.assertTrue(contains(global_body, [
            "if", "!", "MF_Contains", "(", "direct", ",", "profile", ".", "Id", ")", "return", "false",
        ]))
        self.assertTrue(contains(global_body, ["if", "profile", ".", "Id", "=", "vscode", "{", "if", "!", "MF", ".", "VscodeReady", "return", "false"]))
        self.assertTrue(contains(browser_body, [
            "if", "!", "IsObject", "(", "profile", ")", "||", "(",
            "profile", ".", "Id", "!=", "chrome", "&&", "profile", ".", "Id", "!=", "edge", ")", "return", "false",
        ]))
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
            **{name: generic | browser | paragraph | switches for name in BROWSER_APPS},
            "notepad": generic | paragraph | switches,
            **{profile_id: generic | switches | (paragraph if profile_id in PARAGRAPH_PROFILES else set())
               for profile_id in ADDED_APPS},
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
