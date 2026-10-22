# Implementation contract v1

Status: frozen for the initial development preview, 2026-10-22. This is an implementation interface, not hardware evidence.

## Backend and scope

AHK v2.0.19+ (64-bit), single user-mode process. No Kanata at runtime. The script starts in Native Mode. Only a user tray action enables mappings. Exact left-side chords only; no physical Ctrl or right Win remap, no unconditional LWin-to-Ctrl conversion. No device attribution: applies to all keyboards when enabled, explicitly disclosed. `device_id=null`, `origin=unknown` (AHK hook lacks trustworthy device/injection metadata). Self-generated hotkeys are excluded with hook hotkeys `$` and input level 1, SendLevel 0.

Only the foreground thread's exact HKL `04090409` (US English) is initially allowed. Other layouts, including Chinese IME even in English mode, bypass the whole app. This deliberately avoids guessing composition state. Physical input remains native; IME safety is still NOT TESTED. Unknown integrity/process/layout => bypass. Elevated runtime is refused; elevated foreground windows bypass.

## Configuration v1

The three `.yaml` files use the JSON-compatible YAML 1.2 subset: standard JSON objects, no YAML-only syntax, comments, aliases or arbitrary tags. Python stdlib only. `tools/macflow_config.py` exposes `load_and_validate(root: pathlib.Path) -> dict` with keys `mappings`, `apps`, `release`; raises `ConfigError` (ValueError subclass). It also exposes `validate_bundle(bundle)` for tests. Root path is repository root.

- mappings: `{schema_version:1, mappings:[{id, enabled:bool, physical_chord, contexts:[str], action, priority:int, on_unmatched:"passthrough", blocked_reason:str}]}`. Blocked entries are disabled. Chord grammar: `LWin[+Shift]+key` or `LAlt[+Shift]+key`; key is a lower-case a-z, Left/Right/Up/Down/Backspace/Tab or bracket. No arbitrary AHK expressions. Unique IDs and unique chord/context at equal priority; reject overlaps across matched profile contexts as well.
- apps: `{schema_version:1, allowed_hkls:["04090409"], bypass_processes:[lowercase exe], profiles:[{id, processes:[lowercase exe], contexts:[str], enabled:bool, requires_integration:bool}]}`. IDs: chrome, notepad, vscode, explorer, windows_terminal. Windows Terminal profile disabled. vscode requires a per-run confirmation that manual bindings are installed. Contexts are `edit`, `text`, `browser`, `explorer`, `vscode`, `terminal`.
- release: `{schema_version:1, delivery_status:"DEVELOPMENT PREVIEW", mode:"ahk-only", baseline:[str], cases:[{id, priority:"P0"|"P1"|"CONDITIONAL", required_prototype:bool, required_v1:bool, status:"NOT TESTED"|"BLOCKED"|"PASS"|"FAIL", reason:str}]}`. Cases correspond to spec T01..T09 subcases. Do not mark hardware PASS.

Allowed actions: copy,paste,cut,select_all,undo,redo,save,find,word_left,word_right,select_word_left,select_word_right,delete_word,line_start,line_end,document_start,document_end,app_next,app_previous,browser_address,browser_new,browser_close,browser_reload,browser_restore,browser_back,browser_forward,explorer_new,explorer_delete,terminal_copy,terminal_paste.

Generator writes deterministic `build/generated/macflow.ini` and `manifest.json`. Runtime loads data, not executable generated AHK, so a missing/malformed artifact can remain Native instead of failing at #Include parse time. This refines the spec's “generated AHK constants” into a safer data format. No hand edits. SHA256 hashes identify source/artifacts; validation is not a security signature. `--check` detects stale artifacts without writing.

## AHK shared interfaces

Global `MF := {Enabled:false, Config:0, ConfigError:"", Root:root, VscodeReady:false, OwnedKeys:Map(), SwitcherActive:false, SwitchingHwnd:0, Registered:[]}`. Main sets it before calling initialization. Config/parse errors leave ConfigError visible and Enabled=false. All source includes are static project code.

- `MF_LoadConfig(root)` returns `{SchemaVersion, Hash, Rules:[], Profiles:[], BypassProcesses:[], AllowedLayouts:[]}`. Rule properties `Id,Enabled,Chord,Contexts,Action,Priority,BlockedReason`; profile `Id,Processes,Contexts,Enabled,RequiresIntegration`. Invalid artifact throws Error.
- `MF_RegisterMappings()` installs dynamic hook hotkeys using `HotIf(callback)` with per-chord selection; default context predicate is false when disabled. `MF_ResetInput()` releases only owned synthetic keys and clears switcher state; `MF_PollInput()` handles switcher LWin release/Esc/timeout and layout/focus safety. Never log actual key contents.
- `MF_CurrentProfile()` returns profile object or 0 after enabled/process/integrity/layout checks. Native VS Code dispatch is allowed only with `MF.VscodeReady=true` and profile integration requirement.
- `MF_SelectRule(chord, profile)` returns highest-priority enabled matching rule or 0; config rejects ambiguous matches. Priority: Native/bypass -> app context -> generic allowed profile -> native passthrough.
- `MF_RunAction(action, profile)` dispatches into profiles. Handlers `MF_GlobalAction(action, profile)`, `MF_BrowserAction(action, profile)`, `MF_ExplorerAction(action, profile)`, `MF_TerminalAction(action, profile)` return true if handled, false if unknown. No blind terminal generic fallback.
- `MF_SendTap(keys)` sends a complete bounded chord (SendEvent, SendLevel 0), no held outputs. `MF_HoldSynthetic(key)`/`MF_ReleaseSynthetic(key)` manage MF.OwnedKeys. `MF_CancelSwitch()` releases owned Alt and clears switcher. Only `LAlt` may be held across app-switch repetitions. `MF_GlobalAction` owns switcher action, using these helpers.
- `MF_SetEnabled(enabled, *)`, `MF_Disable(*)`, `MF_Quit(*)`, `MF_UpdateTray()` are lifecycle functions. Disable resets input before displaying Native. Timers/exit call shared reset. Whole-process crash recovery is a hardware test, not claimed verified.

## VS Code bridge and terminal limits

Native VS Code keybindings are manual opt-in, backed up by the user before merging. No runtime config writes. Use reserved Ctrl+Alt+F13..F24 and shifted variants; exact trigger/action mapping belongs in integrations/vscode/README.md and matches MF_GlobalAction's vscode branch. Include a lowest-priority empty-command binding for each dedicated trigger, then higher-priority editor/terminal bindings with `when`. No selection copy in terminal must consume/no-op. Never bind native Ctrl+C/D/Z or Win+L. `terminal.integrated.sendKeybindingsToShell=false` is a prerequisite. Installed fragments must not alter ordinary native inputs while MacFlow is disabled; collision check and original settings restoration are manual documented steps. VS Code integration remains NOT TESTED and disabled by default per run until user confirms setup.

Windows Terminal copy is BLOCKED because selection/no-op behavior is not reliably available through this backend. Entire host bypasses. Explorer deletion and Command+L are BLOCKED and never registered. Physical LWin+L may still lock Windows; Ctrl+L is the documented fallback. Other registered mappings are IMPLEMENTED / NOT TESTED, not compatibility claims.

## Lifecycle boundaries

Native Mode clears Enabled and releases only owned synthetic keys. Do not blindly release physical modifiers. On orderly exit/suspend/session change reset. App switching captures state at down, ends on LWin release, Esc, timeout, or explicit disable; no orphaned held Alt. UI Enable action refuses while modifiers are physically held. Emergency keyboard option Ctrl+Alt+F12 disables only; mouse tray remains primary. No autorun, elevation, driver, clipboard reads/writes, or network.

## Verification

Static tests verify config semantics, deterministic generation, invalid configuration fail-closed policy and release gate logic. They do not parse or run AHK. Windows smoke script runs AHK `/validate` and optional `--self-test` (init Native then exit, no mappings enabled), when a user supplies an installed runtime. Genuine keyboard test statuses remain NOT TESTED even after syntax/smoke pass.
