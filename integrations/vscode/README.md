# VS Code bridge — manual opt-in, NOT TESTED

This is an experimental Windows desktop VS Code integration for the AHK development preview. The AHK runtime cannot determine whether the editor, integrated terminal, search box or another control has focus. It emits reserved shortcut triggers; VS Code's native `when` clauses select the action. No extension, automatic settings writer, shell escape sequence or clipboard inspection is used.

The profile is configured but bypassed on every MacFlow launch until the user confirms that this setup is installed for the active VS Code profile. Runtime starts in Native Mode independently of this confirmation. Confirmation is not test evidence. The entire window bypasses unless its focus window's layout is US English HKL `04090409` or Simplified Chinese `08040804`. Microsoft Pinyin maps in Chinese and English mode alike (candidate, not hardware-verified for VS Code).

## Setup and collision checks

1. Keep MacFlow in Native Mode. In the intended VS Code profile, run **Preferences: Open Keyboard Shortcuts (JSON)** and **Preferences: Open User Settings (JSON)**. Make timestamped backup copies of both files outside the repository. Record whether each settings key below was absent, and its exact original value if present. For named or portable profiles, use the files opened by VS Code rather than assuming an `%APPDATA%` path. Review Settings Sync scope before editing so the experiment does not unintentionally follow you to another machine.
2. In Keyboard Shortcuts, search each dedicated trigger in the table below, including extension/user bindings and chords that start with that trigger. Each must be unused. Resolve existing collisions deliberately; do not silently overwrite them or remap physical Ctrl+C/D/Z. Inspect the existing user JSON as well, since later entries win.
3. Merge the array **contents** of `keybindings.macflow.json` into the existing array, keeping their order. Do not replace the whole file or create nested arrays. Keep the broad `noop` entries first and the guarded actions later. Add start/end comments around the inserted block in your user JSONC so it can be removed precisely.
4. Check effective User, Workspace and profile settings **before** merging `settings.macflow.json`. The baseline must already have `terminal.integrated.sendKeybindingsToShell=false`, and native terminal copy/paste must already skip the shell. Do not change these existing native behaviors to force compatibility: if customized differently, leave this integration disabled. The snippet describes the required state, not a replacement for the user's settings. Add `noop` to `commandsToSkipShell` if necessary and preserve unrelated entries and defaults; copy/paste entries may only restate their existing effective behavior. No negative entry may remove one of these commands. Record absent versus explicit values for later restoration.
5. Confirm there are no JSON or unknown-command errors. Test only in a disposable editor buffer and terminal session. Once these prerequisites are satisfied, use MacFlow's per-run VS Code confirmation and then Enable action. Recheck setup after switching VS Code profiles or changing relevant settings/extensions. MacFlow cannot automatically verify the effective native configuration.

No native Win, Ctrl+C, Ctrl+D or Ctrl+Z binding is installed. Preserving ordinary keyboard input while disabled is a required baseline test, not an already verified result. The reserved Ctrl+Alt+F13..F24 and listed shifted triggers remain bound until the snippet is removed; they must be unused in the user's environment. Native Mode stops synthetic emission, not manual VS Code settings. If the setup changes any ordinary native behavior, revoke confirmation and restore the original settings before proceeding.

## Trigger contract

All physical Command chords mean **left Command/LWin only**. Option means **left Option/LAlt only**. Right Command and physical Control remain native. Standard editor command semantics are preserved, including VS Code's native copy-line behavior when no editor text is selected.

| Action / physical chord | Dedicated trigger | Editor command | Terminal result |
| --- | --- | --- | --- |
| Copy / Cmd+C | Ctrl+Alt+F13 | `editor.action.clipboardCopyAction` | `copySelection` with selection; `noop` without selection |
| Paste / Cmd+V | Ctrl+Alt+F14 | `editor.action.clipboardPasteAction` | `workbench.action.terminal.paste` |
| Cut / Cmd+X | Ctrl+Alt+F15 | `editor.action.clipboardCutAction` | `noop` |
| Select all / Cmd+A | Ctrl+Alt+F16 | `editor.action.selectAll` | `noop` |
| Undo / Cmd+Z | Ctrl+Alt+F17 | `undo` | `noop` |
| Redo / Cmd+Shift+Z | Ctrl+Alt+F18 | `redo` | `noop` |
| Save / Cmd+S | Ctrl+Alt+F19 | `workbench.action.files.save` | `noop` |
| Find / Cmd+F | Ctrl+Alt+F20 | `actions.find` | `noop` |
| Previous word / Option+Left | Ctrl+Alt+F21 | `cursorWordLeft` | `noop` |
| Next word / Option+Right | Ctrl+Alt+F22 | `cursorWordRight` | `noop` |
| Select previous word / Option+Shift+Left | Ctrl+Alt+F23 | `cursorWordLeftSelect` | `noop` |
| Select next word / Option+Shift+Right | Ctrl+Alt+F24 | `cursorWordRightSelect` | `noop` |
| Delete previous word / Option+Backspace | Ctrl+Alt+Shift+F13 | `deleteWordLeft` | `noop` |
| Home / Cmd+Left | Ctrl+Alt+Shift+F14 | `cursorHome` | `noop` |
| End / Cmd+Right | Ctrl+Alt+Shift+F15 | `cursorEnd` | `noop` |
| Document start / Cmd+Up | Ctrl+Alt+Shift+F16 | `cursorTop` | `noop` |
| Document end / Cmd+Down | Ctrl+Alt+Shift+F17 | `cursorBottom` | `noop` |

Only `editorTextFocus && !terminalFocus` receives editor commands; modifying editor commands additionally require `!editorReadonly`. Only `terminalFocus` receives terminal paste, and terminal copy additionally requires `terminalTextSelected`. Search, quick-open, terminal tab lists, debug consoles, webviews, notebook non-text surfaces and other focus states deliberately consume these reserved triggers with `noop`. They are not claimed to support the editing mappings. There is no generic terminal fallback.

Cmd+Tab uses the AHK app-switch implementation and does not use this bridge. Cmd+L remains BLOCKED; Windows may lock on physical LWin+L. Use physical Ctrl+L where supported.

## Why the fallback is nonempty `noop`

An empty-command binding disables a command mapping but does **not** reliably consume the single key event. It is insufficient for preventing a reserved key from reaching a terminal shell. The supplied bindings therefore use VS Code's registered, nonempty `noop` command and explicitly include it in `commandsToSkipShell`. Copy with no terminal selection resolves to `noop`; it never emits Ctrl+C. With selection, the later `copySelection` binding takes priority. All other unhandled dedicated triggers also resolve to `noop`.

This design is based on the following official source, inspected on 2026-10-22. It is an inference from code, not proof about the user's installed version; record that version and verify on Windows before claiming success:

- [`commands.ts`](https://github.com/microsoft/vscode/blob/main/src/vs/platform/commands/common/commands.ts), `CommandsRegistry.registerCommand('noop', ...)`: built-in no-op command.
- [`abstractKeybindingService.ts`](https://github.com/microsoft/vscode/blob/main/src/vs/platform/keybinding/common/abstractKeybindingService.ts), `_doDispatch`, `ResultKind.KbFound`: a nonempty non-bubbling command sets `shouldPreventDefault`; an empty command alone does not.
- [`terminalInstance.ts`](https://github.com/microsoft/vscode/blob/main/src/vs/workbench/contrib/terminal/browser/terminalInstance.ts), `_open`, `attachCustomKeyEventHandler`: shell exclusion requires `sendKeybindingsToShell=false`, a nonempty resolved command and inclusion in the skip list.
- [`terminalContextKey.ts`](https://github.com/microsoft/vscode/blob/main/src/vs/workbench/contrib/terminal/common/terminalContextKey.ts), `TerminalContextKeyStrings.TextSelected`: the actual selection condition is `terminalTextSelected`.
- [`terminal.clipboard.contribution.ts`](https://github.com/microsoft/vscode/blob/main/src/vs/workbench/contrib/terminalContrib/clipboard/browser/terminal.clipboard.contribution.ts), `TerminalCommandId.CopySelection` and `Paste`: native terminal clipboard actions.
- [VS Code keybinding documentation](https://code.visualstudio.com/docs/configure/keybindings): JSON merging, rule ordering and troubleshooting; [terminal advanced documentation](https://code.visualstudio.com/docs/terminal/advanced): terminal shortcut routing.

## Required Windows verification (all NOT TESTED)

Use a non-sensitive, disposable file and terminal session; record only case, application/version, shell, connection mode and result, never input or clipboard contents.

- Test every editor action, read-only editors, editor/terminal focus changes, held/repeated chords and switching profiles. Verify no action escapes into other controls or webviews.
- In the integrated terminal, test both selection states and no selection while a harmless long-running operation is active. Cmd+C must copy selected text; without selection it must leave the operation running, send no shell bytes, leave the clipboard unchanged and produce no warning. Inspect content manually; do not enable input or clipboard logging.
- Test Cmd+V with a harmless single-line clipboard value, without Enter. Preserve VS Code's normal paste safeguards. Test all other reserved triggers as no-ops both with and without selection.
- Independently check physical Ctrl+C/D/Z using the shell's baseline behavior. Do not assume every shell uses the same semantics or that Ctrl+C always interrupts with a selection. Right Command, Native Mode and emergency Disable must preserve the baseline.
- Test both USB and Bluetooth Magic Keyboard operation, Microsoft Pinyin in Chinese and English mode (including a mapped chord pressed while pinyin is still uncommitted), disconnect/reconnect, wake, and runtime disable while a modifier is held. AHK cannot attribute input to one keyboard, so repeat with another keyboard attached.
- If any reserved trigger is unknown, leaks to the shell, shows a warning, invokes the wrong action or changes native Control behavior, disable this integration immediately, record FAIL and roll back. A static check or AHK `/validate` cannot establish these outcomes.

## Rollback

1. Use the MacFlow tray to select Native Mode or quit; remove the per-run VS Code confirmation. This stops emitting bridge triggers immediately.
2. Remove only the inserted keybinding block, or restore the backup if no later personal edits need preserving. Restore `terminal.integrated.sendKeybindingsToShell` to its original value or remove it if originally absent.
3. Remove only the skip-list entries added by this setup. Restore the original list exactly where appropriate, including any original negative entries. Reconcile later user changes instead of replacing them blindly. Check Workspace/profile overrides and Settings Sync again.
4. Reload VS Code if needed and manually confirm original shortcuts, clipboard actions and terminal Control semantics. Record the restoration result. MacFlow never writes these files, so quitting alone does not remove manually merged snippets.
