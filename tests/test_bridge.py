"""Bridge data checks do not run VS Code."""
import json
import re
import unittest
from test_config import ROOT
BINDINGS = ROOT / "integrations/vscode/keybindings.macflow.json"

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.bindings = json.loads(BINDINGS.read_text(encoding="utf-8"))
        self.settings = json.loads((BINDINGS.parent / "settings.macflow.json").read_text(encoding="utf-8"))
        self.source = (ROOT / "src/ahk/global.ahk").read_text(encoding="utf-8")

    def test_only_dedicated_triggers_and_nonempty_commands(self):
        for row in self.bindings:
            self.assertRegex(row["key"], r"^ctrl\+alt\+(shift\+)?f(1[3-9]|2[0-4])$")
            self.assertTrue(row["command"])

    def test_noop_default_precedes_every_specialization(self):
        seen = set()
        for row in self.bindings:
            if row["key"] not in seen:
                self.assertEqual("noop", row["command"])
                self.assertNotIn("when", row)
                seen.add(row["key"])
        self.assertEqual(17, len(seen))

    def test_terminal_selection_and_no_selection(self):
        rules = {r.get("when"): r["command"] for r in self.bindings if r["key"] == "ctrl+alt+f13"}
        self.assertEqual("noop", rules["terminalFocus && !terminalTextSelected"])
        self.assertEqual("workbench.action.terminal.copySelection", rules["terminalFocus && terminalTextSelected"])
        self.assertFalse(self.settings["terminal.integrated.sendKeybindingsToShell"])
        for command in ("noop", "workbench.action.terminal.copySelection", "workbench.action.terminal.paste"):
            self.assertIn(command, self.settings["terminal.integrated.commandsToSkipShell"])

    def test_ahk_bridge_matches_binding_data_and_enabled_actions(self):
        pairs = re.findall(r'"([a-z_]+)", "\^!(\+?)\{F(1[3-9]|2[0-4])\}"', self.source)
        triggers = {"ctrl+alt+" + ("shift+" if s else "") + "f" + f for _, s, f in pairs}
        self.assertEqual({r["key"] for r in self.bindings}, triggers)
        rules = json.loads((ROOT / "config/mappings.yaml").read_text(encoding="utf-8"))["mappings"]
        required = {r["action"] for r in rules if r["enabled"] and "vscode" in r["contexts"]}
        self.assertTrue((required - {"app_next", "app_previous"}).issubset({a for a, _, _ in pairs}))
