"""The AHK source helper must find live definitions only; no AHK runs."""
import unittest

from ahk_literals import function_tokens

SOURCE = '''/*
Old(x) {
    return "commented out"
}
*/
Caller() {
    if !Old(1) {
        return 0
    }
}
Old(x) {
    return "live"
}
'''


class FunctionTokensTests(unittest.TestCase):
    def test_comments_and_call_sites_are_not_definitions(self):
        self.assertEqual([("name", "return"), ("string", "live")], function_tokens(SOURCE, "Old"))

    def test_missing_or_duplicate_definitions_fail(self):
        with self.assertRaisesRegex(AssertionError, "Missing"):
            function_tokens(SOURCE, "Absent")
        with self.assertRaisesRegex(AssertionError, "Duplicate"):
            function_tokens(SOURCE + "Old(y) {\n}\n", "Old")


if __name__ == "__main__":
    unittest.main()
