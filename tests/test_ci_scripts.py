"""Check CI test wiring; the PowerShell script supplies the behavioral proof."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def without_comments(source):
    return "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("#"))


class CiLauncherTests(unittest.TestCase):
    def test_launcher_and_regression_use_same_helper_before_raw_launch(self):
        helper = ROOT / "tools/ci-clear-module-path.ps1"
        self.assertTrue(helper.is_file(), "The shared helper is a required source file")
        launcher = without_comments((ROOT / "tools/ci-run-ahk.ps1").read_text(encoding="utf-8"))
        regression = without_comments((ROOT / "tests/test-ci-module-path.ps1").read_text(encoding="utf-8"))
        include = ". (Join-Path $PSScriptRoot 'ci-clear-module-path.ps1')"
        run = "[MacFlowCiRestrictedRunner]::Run("
        self.assertEqual(1, launcher.count(include))
        self.assertEqual(1, launcher.count(run))
        self.assertLess(launcher.index(include), launcher.index(run))
        self.assertIn(r"'..\tools\ci-clear-module-path.ps1'", regression)
        self.assertRegex(regression, r"(?m)^\s*\. \$ModulePathHelper\s*$")
        self.assertLess(regression.index(". $ModulePathHelper"), regression.rindex("Test-RawWindowsPowerShellAutoload"))
        # The regression executes shared production code, not a duplicate fix.
        self.assertNotIn("SetEnvironmentVariable", regression)

    def test_windows_ci_runs_behavior_regression_before_ahk_setup(self):
        workflow = (ROOT / ".github/workflows/static-checks.yml").read_text(encoding="utf-8")
        windows = workflow[workflow.index("  windows-runtime:"):]
        steps = re.split(r"(?m)^      - ", windows)
        matched = [step for step in steps if "run: ./tests/test-ci-module-path.ps1" in step]
        self.assertEqual(1, len(matched))
        self.assertRegex(matched[0], r"(?m)^        shell: pwsh\s*$")
        self.assertLess(windows.index("./tests/test-ci-module-path.ps1"), windows.index("./tools/prepare-ci-ahk.ps1"))

    def test_behavior_test_distinguishes_states_and_uses_bounded_raw_process(self):
        source = (ROOT / "tests/test-ci-module-path.ps1").read_text(encoding="utf-8")
        code = without_comments(source)
        self.assertRegex(source, r"(?mi)^#Requires -Version 7\.5\s*$")
        for case in ("nonempty", "empty", "missing"):
            self.assertIn("Name = '" + case + "'", code)
        self.assertIn("[object]::Equals($Case.Value,", code)
        self.assertIn("[object]::Equals($OriginalModulePath,", code)
        self.assertIn("$env:PSModulePath = $OriginalModulePath", code)
        self.assertIn("[Diagnostics.ProcessStartInfo]::new()", code)
        self.assertIn("$StartInfo.UseShellExecute = $false", code)
        self.assertIn("$Child.Start()", code)
        self.assertIn("StandardOutput.ReadToEndAsync()", code)
        self.assertIn("StandardError.ReadToEndAsync()", code)
        self.assertIn("WaitForExit(15000)", code)
        self.assertNotRegex(code, r"WaitForExit\(\s*\)")
        self.assertNotRegex(code, r"(?mi)^\s*&\s+.*powershell")
        self.assertNotRegex(code, r"\$StartInfo\.Environment(?:Variables)?\s*(?:\[|\.|=)")
        self.assertNotRegex(code, r"(?mi)^\s*Import-Module\b")
        self.assertIn("Get-Item -LiteralPath $PSHOME", code)
        self.assertIn("ConvertTo-Json -InputObject", code)
        self.assertIn("exit $ExitCode", code)


if __name__ == "__main__":
    unittest.main()
