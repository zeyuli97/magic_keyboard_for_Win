# Review follow-up — 2026-10-22

Status: DEVELOPMENT PREVIEW. This records the engineering fixes prompted by the external review, not new compatibility claims.

## Confirmed defects and changes

- Reproduced: adding Explorer context to enabled undo/find passed Python validation although the runtime handler refuses those actions. Both validators now check each enabled rule against every matching profile's implemented actions, including disabled profiles. Tests also compare policy tables and inspect actual handler maps/guards.
- Configuration self-test did not cover hotkey registration. It remains a useful no-hook check; a separate --registration-test now executes the shared registration path in Native Mode and cleans up without sending input.
- Packaging could include untracked private files. Only Git-indexed regular files in explicit release directories are now selected, and their content is read from the index. A release file with unstaged working-tree changes is refused. Missing/unmerged/symlink entries fail. --check compares a deterministic reconstruction with dist/manifest.json without writing.
- Integration-era skip decorators and missing-generator fallback have been removed. Required files disappearing must fail tests.
- CI now has separate portable and Windows runtime jobs, with Actions pinned to full commits and checkout credentials disabled. AHK 2.0.19 is the pinned minimum-supported regression target; both official archive and extracted 64-bit executable hashes are checked before use. This does not bundle or install AHK for end users.

## Remaining product decisions and experiments

T03 Windows Terminal remains a required P0 blocker. Hardware testing alone cannot make an unimplemented adapter pass. A UI Automation selection adapter is a research candidate: GetSelection may return a degenerate range for no selection, so a nonempty array is insufficient. Provider support/errors, endpoint comparison, focus races and no-selection no-op behavior must be verified. copyOnSelect changes native clipboard behavior even when MacFlow is disabled and is not adopted. [Microsoft API](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomationtextpattern-getselection)

Command+L remains a v1 blocker under the unchanged user-mode/system-policy boundary. Describing third-party drivers as the only possible solution is too broad; Microsoft also offers Keyboard Filter on supported Windows editions. No driver, Keyboard Filter or system-policy change is adopted here. [Protected Win+L behavior](https://learn.microsoft.com/en-us/troubleshoot/azure/virtual-desktop/win-key-remains-held-after-pressing-ctrl-win-l-in-remote-session), [Keyboard Filter combinations](https://learn.microsoft.com/en-us/windows/configuration/keyboard-filter/predefined-key-combinations)

Explorer deletion still needs a separate recycle-only experiment and focused tests. Shell selection and IFileOperation are candidates, not evidence that a path is safely recyclable.

The US-only layout boundary, native passthrough for unmatched chords, allowlisted application switching and restricted VS Code focus contexts are real daily-use limitations. IMM open state alone does not establish absence of composition/TSF candidate UI. Extending IME support, swallowing native Win chords, or broadening focus/app scope requires a deliberate contract update and tests; none are silently changed. [ImmGetDefaultIMEWnd](https://learn.microsoft.com/en-us/windows/win32/api/imm/nf-imm-immgetdefaultimewnd), [ImmGetOpenStatus](https://learn.microsoft.com/en-us/windows/win32/api/imm/nf-imm-immgetopenstatus)

Mode icons/notifications, device-change cleanup and SendEvent timing are deferred improvements. They do not erase the held-key, disconnect, focus and recovery acceptance requirements.

## Windows CI boundary

The module-path cleanup uses `$env:PSModulePath = $null`. In PowerShell 7.5+, the .NET `SetEnvironmentVariable` call with `$null` sets an empty string, so the launcher's subsequent null check would fail before starting the child. The launcher and `tests/test-ci-module-path.ps1` now share a CI-only cleanup script; the behavior test exercises nonempty/empty/missing states and Windows PowerShell core-module autoloading. CI runs it with `pwsh` before AHK setup. This test is not a substitute for the restricted-token AHK smoke or hardware tests. [PowerShell environment-variable semantics](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_environment_variables?view=powershell-7.5#use-the-systemenvironment-methods)

GitHub Windows hosted runners use administrator accounts with UAC disabled. The CI helper must create and verify a restricted medium-integrity process before running the unchanged AHK smoke command; it must fail rather than bypass the runtime's administrator rejection. Because the raw Win32 launch inherits pwsh's PSModulePath, whose PowerShell 7 module paths would break Windows PowerShell core-module autoloading, the helper clears that variable first. [about_PSModulePath](https://learn.microsoft.com/powershell/module/microsoft.powershell.core/about/about_psmodulepath) No UAC, registry, security-policy, autorun or driver change is made. This helper and the Windows workflow have not been executed on the macOS development host. [GitHub runner privileges](https://docs.github.com/en/actions/reference/runners/github-hosted-runners#administrative-privileges), [SAFER token API](https://learn.microsoft.com/en-us/windows/win32/api/winsafer/nf-winsafer-safercomputetokenfromlevel)
