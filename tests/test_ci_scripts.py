"""Source checks for the CI-only Windows launcher; nothing is executed."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CiLauncherTests(unittest.TestCase):
    def test_windows_powershell_child_does_not_inherit_pwsh_module_path(self):
        # Windows PowerShell started by a raw Win32 call would otherwise resolve
        # core modules to the PowerShell 7 copies first and fail to autoload them.
        source = (ROOT / "tools/ci-run-ahk.ps1").read_text(encoding="utf-8")
        clear = source.index("[Environment]::SetEnvironmentVariable('PSModulePath', $null, 'Process')")
        launch = source.index("[MacFlowCiRestrictedRunner]::Run(")
        self.assertLess(clear, launch)
        self.assertEqual(1, source.count("[MacFlowCiRestrictedRunner]::Run("))


if __name__ == "__main__":
    unittest.main()
