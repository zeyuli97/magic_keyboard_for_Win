# Implementation decisions

2026-10-22, initial development preview. Source: [execution specification](https://docs.google.com/document/d/1GlBcn8PpgCiUHCXzl3kUaBjWpS909ThDqEknYTjjow4).

1. **Single AHK process.** No Kanata, driver, elevation or startup integration. This does not prove recovery on Windows; tests remain NOT TESTED.
2. **Generated data instead of executable constants.** UTF-16LE INI (the encoding supported by Windows IniRead), SHA256 sidecar and manifest avoid executing generated code. Missing or corrupt data leaves the tray in Native Mode. Hashes detect corruption, not a malicious local editor who can replace both files. Only allowlisted actions/chords can load.
3. **Portable build without dependencies.** `.yaml` files use the JSON subset of YAML 1.2. Python 3.9+ stdlib validates and compiles them; packaged Windows runtime needs only AHK, not Python.
4. **IME fail-closed policy.** Only foreground HKL 04090409 is mapped. Selecting Chinese IME or an unknown layout bypasses the entire window. Full Chinese-IME mapping is not implemented; native input safety still requires real tests.
5. **Context handling.** Process allowlist and non-elevated token check; unknown errors bypass. Explorer restricted to folder window classes. VS Code requires explicit per-run acknowledgment of a manually installed bridge. Dedicated chords use VS Code's built-in `noop` as the fallback, because an empty command does not reliably consume a key. No native Ctrl shortcuts are overwritten.
6. **Known blockers stay disabled.** Windows Terminal copy/no-selection contract cannot be proven using this backend, so its entire host bypasses. Cmd+L and recycle-bin-only Explorer deletion are not registered. Native LWin+L can still lock Windows.
7. **No hardware attribution.** Left Win vs physical Ctrl are distinguished, but multiple keyboards are not. Mapping applies to all keyboards while enabled. This does not satisfy device-specific isolation.
8. **Input state.** Complete bounded sends minimize held outputs; only app switching owns synthetic LAlt. Hotkey predicates use physical modifier state, snapshot rule/foreground, and recheck before sending. Focus races consume instead of replaying into another app. These mitigations are not atomic OS delivery guarantees; adversarial focus/hold testing remains required.

Implementation references: [AHK HotIf](https://raw.githubusercontent.com/AutoHotkey/AutoHotkeyDocs/v2/docs/lib/HotIf.htm), [AHK Hotkey](https://raw.githubusercontent.com/AutoHotkey/AutoHotkeyDocs/v2/docs/lib/Hotkey.htm), [AHK Send](https://raw.githubusercontent.com/AutoHotkey/AutoHotkeyDocs/v2/docs/lib/Send.htm), [VS Code commands](https://github.com/microsoft/vscode/blob/main/src/vs/platform/commands/common/commands.ts).
