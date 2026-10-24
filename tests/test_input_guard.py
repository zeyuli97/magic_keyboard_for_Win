"""Source-contract checks for the Alt output guard and send outcome; no AHK runs.

These keep the 2026-10-23 candidate fix from being dropped silently. They do
not show that Windows, WinUI or the input-language hotkey behave as assumed;
only the documented Windows hardware retest can establish that.
"""
import unittest

from test_config import ROOT
from ahk_literals import contains, function_tokens


def positions(body, sequence):
    values = [item[1] for item in body]
    return [index for index in range(len(values) - len(sequence) + 1)
            if values[index:index + len(sequence)] == sequence]


class AltGuardSourceTests(unittest.TestCase):
    def setUp(self):
        self.input = (ROOT / "src/ahk/input.ahk").read_text(encoding="utf-8")
        self.main = (ROOT / "src/ahk/main.ahk").read_text(encoding="utf-8")
        self.global_action = (ROOT / "src/ahk/global.ahk").read_text(encoding="utf-8")

    def test_menu_mask_key_is_unassigned_before_hooks_are_installed(self):
        body = function_tokens(self.main, "MF_Main")
        assignment = positions(body, ["A_MenuMaskKey", ":=", "vkE8"])
        hook = positions(body, ["InstallKeybdHook", "("])
        self.assertEqual(1, len(assignment))
        self.assertTrue(hook)
        self.assertLess(assignment[0], hook[0])

    def test_physical_option_output_is_guarded_before_and_after(self):
        body = function_tokens(self.input, "MF_SendTap")
        self.assertTrue(contains(body, ["altGuard", ":=", "GetKeyState", "(", "LAlt", ",", "P", ")"]))
        guards = positions(body, ["SendEvent", "(", "{Blind}{vkE8}", ")"])
        sends = positions(body, ["SendEvent", "(", "keys", ")"])
        self.assertEqual(1, len(sends))
        self.assertEqual(2, len(guards))
        self.assertLess(guards[0], sends[0])
        self.assertLess(sends[0], guards[1])
        # Codex CR1: the leading guard is a send of its own, so the final checks
        # run again between it and the output, and the trailing guard only goes
        # to the window that received the output.
        checks = positions(body, ["if", "!", "MF_SendTargetSafe", "(", "hwnd", ")", "return", "false"])
        self.assertEqual(2, len(checks))
        self.assertLess(checks[0], guards[0])
        self.assertTrue(guards[0] < checks[1] < sends[0])
        self.assertTrue(contains(body, [
            "if", "WinExist", "(", "A", ")", "=", "hwnd", "&&", "(", "altGuard", "&&", "GetKeyState", "(", "LAlt", ")",
            "||", "shiftGuard", "&&", "GetKeyState", "(", "Shift", ")", ")", "SendEvent", "(", "{Blind}{vkE8}", ")",
        ]))
        # The dispatch window is the target, read once (AHK review P3-2).
        self.assertTrue(contains(body, [
            "hwnd", ":=", "MF", ".", "HasOwnProp", "(", "DispatchHwnd", ")", "&&", "MF", ".", "DispatchHwnd",
            "?", "MF", ".", "DispatchHwnd", ":", "WinExist", "(", "A", ")",
        ]))
        # Only the target read and the trailing-guard check read the foreground.
        self.assertEqual(2, [value for _, value in body].count("WinExist"))

    def test_held_shift_is_guarded_only_when_the_output_drops_it(self):
        # Command+Shift+Z sends Ctrl+Y, so Send releases and restores the held
        # Shift; outputs that include Shift keep it down and need no guard.
        body = function_tokens(self.input, "MF_SendTap")
        self.assertTrue(contains(body, [
            "shiftGuard", ":=", "!", "InStr", "(", "keys", ",", "+", ")", "&&",
            "(", "GetKeyState", "(", "LShift", ",", "P", ")", "||", "GetKeyState", "(", "RShift", ",", "P", ")", ")",
        ]))

    def test_final_send_checks_cover_mode_window_and_safety(self):
        body = function_tokens(self.input, "MF_SendTargetSafe")
        self.assertTrue(contains(body, ["if", "!", "hwnd", "||", "!", "MF_ForegroundSafe", "(", "hwnd", ",", "&", "reason", ")", "{"]))
        self.assertTrue(contains(body, ["MF_ResetInput", "(", ")", "return", "false"]))
        self.assertTrue(contains(body, ["if", "!", "MF", ".", "Enabled", "return", "false"]))
        self.assertTrue(contains(body, ["if", "WinExist", "(", "A", ")", "!=", "hwnd", "{"]))

    def test_send_outcome_drives_switch_cleanup(self):
        body = function_tokens(self.input, "MF_SendTap")
        self.assertTrue(contains(body, ["return", "true"]))
        self.assertTrue(contains(body, ["return", "false"]))
        action = function_tokens(self.global_action, "MF_GlobalAction")
        self.assertTrue(contains(action, ["if", "!", "MF_SendTap", "("]))
        self.assertTrue(contains(action, ["MF_CancelSwitch", "(", "starting", ")"]))
        release = function_tokens(self.input, "MF_ReleaseSynthetic")
        self.assertTrue(contains(release, ["masked", "?", "{Blind}{vkE8}{"]))

    def test_warnings_reach_stdout_and_fail_the_smoke_check(self):
        self.assertRegex(self.main, r"(?m)^#Warn All, StdOut\s*$")
        smoke = (ROOT / "tools/smoke-tests.ps1").read_text(encoding="utf-8")
        self.assertIn("-match '==> Warning:'", smoke)


class InputLayoutSourceTests(unittest.TestCase):
    """The input thread's layout alone decides; Pinyin maps in either IME mode."""

    def setUp(self):
        self.router = (ROOT / "src/ahk/router.ahk").read_text(encoding="utf-8")

    def test_layout_gate_uses_the_input_thread(self):
        body = function_tokens(self.router, "MF_ForegroundSafe")
        # Codex CR2: a failed focus query bypasses; only a successful query that
        # reports no focus window falls back to the foreground thread.
        self.assertTrue(contains(body, [
            "if", "!", "MF_FocusWindow", "(", "threadId", ",", "&", "focus", ")", "{",
            "reason", ":=", "focus window unavailable", "return", "false", "}",
        ]))
        self.assertTrue(contains(body, ["inputThread", ":=", "focus", "?"]))
        query = function_tokens(self.router, "MF_FocusWindow")
        self.assertTrue(contains(query, ["focus", ":=", "0"]))
        self.assertTrue(contains(query, ["Ptr", ",", "info", ")", "return", "false"]))
        self.assertTrue(contains(query, ["focus", ":=", "NumGet"]))
        self.assertTrue(contains(query, ["return", "true"]))
        self.assertTrue(contains(body, ["layout", ":=", "MF_ThreadLayout", "(", "inputThread", ")"]))
        # The top-level thread can keep a stale layout (Notepad 2026-10-23), so it
        # must not decide when a focus window exists.
        self.assertFalse(contains(body, ["MF_ThreadLayout", "(", "threadId", ")"]))
        self.assertTrue(contains(body, [
            "if", "!", "MF_Contains", "(", "MF", ".", "Config", ".", "AllowedLayouts", ",", "layout", ")", "{",
            "reason", ":=", "keyboard layout ",
        ]))
        # A focus window without a thread must not fall back to this script's layout.
        self.assertTrue(contains(body, ["if", "!", "inputThread", "{"]))

    def test_no_ime_state_query_anywhere(self):
        # The stage-1 conversion-mode query is gone on purpose (decision 12); a new
        # IME or composition query needs a contract change, not a silent return.
        for path in sorted((ROOT / "src/ahk").glob("*.ahk")):
            source = "\n".join(line.split(";")[0] for line in path.read_text(encoding="utf-8").splitlines())
            for name in ("imm32", "ImmGet", "0x0283", "0x283", "SendMessage", "ImeEnglish",
                         "UIAutomation", "TextEditPattern", "GetActiveComposition"):
                with self.subTest(path=path.name, name=name):
                    self.assertNotIn(name.lower(), source.lower())


if __name__ == "__main__":
    unittest.main()
