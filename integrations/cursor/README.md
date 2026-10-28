# Cursor keybinding bridge

This DEVELOPMENT PREVIEW maps left Command and Option in the Windows desktop Cursor editor (`Cursor.exe`). Editor commands and terminal commands use Cursor's native focus conditions. Physical Control and right Command stay native. Hardware and IME acceptance remain **NOT TESTED**.

## Setup

1. Keep MacFlow in Native Mode. In the intended Cursor profile, open **Preferences: Open Keyboard Shortcuts (JSON)** and **Preferences: Open User Settings (JSON)**. Back up both files. The default Windows profile usually stores them in `%APPDATA%\Cursor\User`; named or portable profiles can use other locations.
2. Check the reserved Ctrl+Alt+F13–F24 triggers and Ctrl+Alt+Shift+F13–F17 triggers for collisions, including user, extension and multi-key bindings. Do not replace existing personal shortcuts. These triggers must be unused.
3. Merge the contents of [keybindings.macflow.json](keybindings.macflow.json) into the existing array, preserving their order and surrounding them with `// MacFlow begin` / `// MacFlow end` comments. Keep the broad `noop` entries before the guarded commands. Do not replace the file or nest the array.
4. Check effective profile, User and Workspace settings: `terminal.integrated.sendKeybindingsToShell` must already be false, and native terminal copy/paste must already skip the shell. If existing settings differ, leave the bridge unconfirmed. [settings.macflow.json](settings.macflow.json) describes the required state. Add `noop` to `terminal.integrated.commandsToSkipShell`, keeping unrelated entries and defaults; copy/paste entries may restate their existing behavior. Do not add negative entries for these commands. Record original values, including absent keys, for rollback. Check Settings Sync scope before merging.
5. Check for JSON or unknown-command errors. Use a disposable editor buffer and terminal to verify the behavior below. In the MacFlow tray, choose **Confirm Cursor setup for this run...**, then **Enable mappings**. Repeat confirmation each MacFlow launch, and recheck configuration after switching Cursor profiles or changing extensions/settings.

Cursor confirmation is separate from VS Code confirmation. Confirming or revoking either returns MacFlow to Native Mode without confirming or revoking the other editor. MacFlow itself never writes Cursor settings.

## Mappings and focus

The snippets use the same 17 dedicated triggers as the [VS Code trigger table](../vscode/README.md#trigger-contract); the existing VS Code files are unchanged.

- **Editable editor:** copy/paste/cut/select all, undo/redo, save/find, word movement/selection/deletion and line/document movement. Mutating commands require `!editorReadonly`.
- **Integrated terminal:** ⌘C copies selected terminal text. With no selection, it is a no-op and does not emit Ctrl+C. ⌘V calls native terminal paste. All other bridge triggers are no-ops.
- **Chat, search, quick-open, debug console, webviews and other non-editor focus:** bridge editing triggers are no-ops. Use native shortcuts there.
- **Application switching:** ⌘Tab / ⌘⇧Tab use MacFlow's existing app-switch handling. ⌥↑/↓ remain native. ⌘L is still blocked and may lock Windows natively.

An empty command does not reliably consume a key, so the fallback is the registered `noop` command, included in the terminal skip list. The bridge makes no shell calls and never inspects clipboard contents. Behavior depends on the installed Cursor version and focus implementation; configuration checks alone cannot verify it.

## Verification and removal

Test editor actions, read-only files, terminal selected/unselected copy and paste, other terminal triggers, chat/search no-ops, focus changes, native Control, right Command, both input layouts, release order, Native Mode and emergency Disable. Keep copies unsent and terminal commands harmless. Repeat each case at least ten times; record application version and results without recording input or clipboard contents. Stop and revoke confirmation on unexpected output or shell leakage.

To remove the bridge, select Native Mode and revoke Cursor confirmation. Remove only the inserted keybinding block and added skip-list entries, restoring original settings (remove keys that were originally absent). Preserve later personal edits. Reload Cursor if needed and check its native shortcuts. Quitting MacFlow alone does not remove these settings.
