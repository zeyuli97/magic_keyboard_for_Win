"""Source-contract checks for the opt-in start-at-sign-in option; no AHK runs.

The specification allows start at sign-in only after the user chooses it, with
the first start in Native Mode. These checks keep the option opt-in and limited
to one Startup-folder shortcut. They do not show that Windows starts it.
"""
import unittest

from test_config import ROOT
from ahk_literals import contains, function_tokens, tokens

LABEL = "Start at Windows sign-in (Native Mode)"
LINK = ["A_Startup", "\\MacFlow.lnk"]


def code(path):
    return "\n".join(line.split(";")[0] for line in path.read_text(encoding="utf-8").splitlines())


class StartupOptionSourceTests(unittest.TestCase):
    def setUp(self):
        self.main = (ROOT / "src/ahk/main.ahk").read_text(encoding="utf-8")

    def test_only_the_tray_toggle_writes_and_nothing_else_persists(self):
        sources = sorted((ROOT / "src/ahk").glob("*.ahk"))
        self.assertTrue(sources)
        writes = 0
        for path in sources:
            source = code(path)
            writes += source.count("FileCreateShortcut(")
            for name in ("RegWrite", "RegCreateKey", "RegSetValue", "schtasks", "CreateService"):
                with self.subTest(path=path.name, name=name):
                    self.assertNotIn(name, source)
        self.assertEqual(1, writes)
        toggle = function_tokens(self.main, "MF_ToggleStartup")
        self.assertTrue(contains(toggle, ["link", ":="] + LINK))
        self.assertTrue(contains(toggle, [
            "FileCreateShortcut", "(", "A_AhkPath", ",", "link", ",", "MF", ".", "Root", ",",
            '"', "A_ScriptFullPath", '"', ",",
        ]))
        self.assertTrue(contains(toggle, ["FileDelete", "(", "link", ")"]))

    def test_tray_choice_is_the_only_entry_point(self):
        tray = function_tokens(self.main, "MF_BuildTray")
        self.assertTrue(contains(tray, ["A_TrayMenu", ".", "Add", "(", LABEL, ",", "MF_ToggleStartup", ")"]))
        # Named exactly twice, by its definition and the tray item: nothing calls
        # it or hands it to a timer, and MF_Main never touches it.
        names = [value for kind, value in tokens(self.main) if kind == "name"]
        self.assertEqual(2, names.count("MF_ToggleStartup"))
        self.assertNotIn("MF_ToggleStartup", [value for _, value in function_tokens(self.main, "MF_Main")])
        for path in sorted((ROOT / "src/ahk").glob("*.ahk")):
            if path.name != "main.ahk":
                self.assertNotIn("MF_ToggleStartup", code(path))
        update = function_tokens(self.main, "MF_UpdateTray")
        self.assertTrue(contains(update, ["A_TrayMenu", ".", "Check", "(", LABEL, ")"]))
        # Test modes exit before the tray exists, so they never touch the option.
        main = [item[1] for item in function_tokens(self.main, "MF_Main")]
        tray_at = main.index("MF_BuildTray")
        self.assertLess(main.index("MF_RunRegistrationTest"), tray_at)
        self.assertLess(max(i for i, value in enumerate(main) if value == "selfTest"), tray_at)

    def test_state_names_this_copy_and_replacing_another_asks(self):
        state = function_tokens(self.main, "MF_StartupState")
        self.assertTrue(contains(state, ["link", ":="] + LINK))
        # A failed read leaves the outputs unset (probe, 2026-10-23); it must count
        # as "other" before anything compares them, or the tray fails at start.
        self.assertTrue(contains(state, [
            "try", "FileGetShortcut", "(", "link", ",", "&", "target", ",", ",", "&", "args", ")",
            "catch", "return", "other",
        ]))
        self.assertTrue(contains(state, [
            "target", "=", "A_AhkPath", "&&", "args", "=", '"', "A_ScriptFullPath", '"', "?", "this", ":", "other",
        ]))
        toggle = function_tokens(self.main, "MF_ToggleStartup")
        self.assertTrue(contains(toggle, ["if", "state", "=", "other", "&&", "MsgBox", "("]))
        self.assertTrue(contains(toggle, ["YesNo Default2 Icon?", ")", "!=", "Yes", "return"]))

    def test_a_stale_check_mark_never_turns_the_option_back_on(self):
        # AHK review P2-1: if the shortcut changed outside MacFlow, the click
        # only refreshes the menu; it must not act on what the menu displayed.
        toggle = function_tokens(self.main, "MF_ToggleStartup")
        values = [value for _, value in toggle]
        stale = ["if", "state", "!=", "MF", ".", "StartupState", "{", "MF", ".", "StartupState", ":=", "state",
                 "MF_UpdateTray", "(", ")"]
        self.assertTrue(contains(toggle, stale))
        start = next(i for i in range(len(values)) if values[i:i + len(stale)] == stale)
        end = values.index("return", start)
        self.assertLess(end, values.index("FileDelete"))
        self.assertLess(end, values.index("FileCreateShortcut"))
        status = function_tokens(self.main, "MF_ShowStatus")
        self.assertTrue(contains(status, ["MF", ".", "StartupState", ":=", "startup", "MF_UpdateTray", "(", ")"]))


if __name__ == "__main__":
    unittest.main()
