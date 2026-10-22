# Windows Terminal — BLOCKED / native bypass

The development preview does not enable any mappings in `windowsterminal.exe`. `cmd.exe`, `powershell.exe`, `pwsh.exe`, `conhost.exe`, `openconsole.exe` and WSL launcher processes are also bypassed. Unknown terminal applications are outside the application allowlist. Do not remove these protections to infer support from a shortcut that appears to work once.

A generic Ctrl+Shift+C send does not establish selection-aware copy with a guaranteed no-op when no text is selected. AHK's foreground process checks also cannot determine the selection state of each terminal host. Consequently both standalone terminal copy and paste rules are disabled, and the profile is disabled as a whole. This is a release blocker where standalone terminal support is required, not a PASS or an accepted workaround for the prototype.

No Windows Terminal settings fragment is installed or supplied. Keep the existing terminal configuration and physical Control behavior. Use the host's existing copy/paste controls. The native Ctrl+C behavior depends on the host, selection and shell; MacFlow does not redefine it.

Any future backend experiment must establish and record at least:

- Cmd+C copies selection and sends no shell bytes.
- Cmd+C with no selection is a no-op, including while a harmless long-running process is active; the clipboard remains unchanged.
- Physical Ctrl+C/D/Z retain the recorded native baseline.
- Focus changes, shell changes, elevated panes, USB/Bluetooth reconnect and modifier-held Disable cannot produce an interrupt, orphaned modifier or input leak.
- All changes can be restored from a concrete settings backup; no keyboard/security registry changes, elevated runtime or drivers are allowed by this preview.

All Windows Terminal hardware and runtime outcomes remain **NOT TESTED**, while the unimplemented selection-aware copy route is **BLOCKED**. The separate manually installed VS Code native bridge does not establish Windows Terminal compatibility.
