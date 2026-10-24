# MacFlow

[简体中文](README.md) | English

Use familiar macOS shortcuts with a Magic Keyboard on Windows. MacFlow uses AutoHotkey v2 to map combinations of left Command (⌘) and left Option (⌥) to their Windows equivalents.

**This is a DEVELOPMENT PREVIEW.** The mappings below are implemented, but full Windows, keyboard and input-method compatibility validation is not complete. Read the [known limitations](#known-limitations) before use.

Physical Control and right Command retain their native Windows behavior. When enabled, mappings affect all connected keyboards; they cannot be limited to a Magic Keyboard.

## Shortcuts

⌘ and ⌥ below refer to the left-side keys. ⇧ means Shift. Mappings apply only in the applications listed in the next section.

| Shortcut | Action |
| --- | --- |
| ⌘C / ⌘V / ⌘X / ⌘A | Copy, paste, cut, select all |
| ⌘Z / ⌘⇧Z | Undo, redo; redo has a known input-method issue described below |
| ⌘S / ⌘F | Save, find |
| ⌥← / ⌥→ | Move by word; add ⇧ to select |
| ⌥Backspace | Delete the word before the cursor |
| ⌘← / ⌘→ | Move to the start or end of the line |
| ⌘↑ / ⌘↓ | Move to the start or end of the document |
| ⌥↑ / ⌥↓ | Move by paragraph; add ⇧ to extend the selection. Available only in Notepad, Chrome, Claude and Codex |
| ⌘Tab / ⌘⇧Tab | Switch applications forward or backward |

Line and word boundaries follow the target application's Windows behavior. Paragraph navigation sends Ctrl+↑/↓: ⌥↓ usually moves to the next paragraph, unlike the macOS behavior of stopping at the end of the current paragraph.

## Applications with mappings

| Application | Mappings |
| --- | --- |
| Notepad | Common editing, word and paragraph navigation, application switching |
| Chrome | Common editing, text navigation, application switching and the browser shortcuts below |
| VS Code | Editing, text navigation and application switching; requires the [keybinding bridge](integrations/vscode/README.md) |
| Explorer | ⌘C/V/X/A, ⌘⇧N to create a folder, application switching |
| Claude, Codex | Common editing, word and paragraph navigation, application switching |
| Visual Studio, Unreal Editor (UE5) | Common editing, word, line and document navigation, application switching |

Chrome also has ⌘T for a new tab, ⌘W to close a tab, ⌘R to reload, ⌘⇧T to reopen a closed tab, and ⌘[ / ⌘] to go back or forward.

⌥↑/↓ keep their native behavior in VS Code and Visual Studio. Explorer's ⌥↑ still goes to the parent folder. Applications outside this list, other keyboard layouts and elevated application windows retain native input.

## Installation and startup

You need Windows and **64-bit AutoHotkey v2.0.19 or later**. Download and extract the complete project, keeping its directory structure. Python is not required to run the generated configuration included with the project.

### Create a desktop shortcut — no terminal needed

1. Put the extracted project in a location you intend to keep, such as `C:\Tools\MacFlow`. Confirm that it contains `src\ahk\main.ahk`.
2. Right-click an empty area of the desktop and choose **New → Shortcut**.
3. In **Type the location of the item**, enter the AutoHotkey executable path followed by the MacFlow script path. For example:

   ```text
   "C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe" "C:\Tools\MacFlow\src\ahk\main.ahk"
   ```

   Replace both paths with their actual locations on your computer and keep both pairs of double quotes. For a portable AutoHotkey installation, the first path should point to its `AutoHotkey64.exe`.

4. Click **Next**, name the shortcut **MacFlow**, then click **Finish**.
5. Right-click the new shortcut and open **Properties → Shortcut**. Set **Start in** to the project root, such as `C:\Tools\MacFlow`. Under **Advanced**, leave **Run as administrator** unchecked, then save.

You can now **double-click the MacFlow desktop icon to start it, without opening PowerShell or Windows Terminal**. MacFlow appears in the system tray; if its icon is hidden, open the tray's overflow area using the arrow near the clock.

The shortcut depends on the original project and AutoHotkey locations. If you move either, update the shortcut's **Target** and **Start in** fields, or create a new shortcut.

### Enable mappings

1. MacFlow starts in **Native Mode** each time, leaving keyboard input unchanged.
2. Use the mouse to open **Status...** from the tray and confirm `Error: none`. For VS Code, complete the bridge setup and per-run confirmation below first.
3. Release all modifier keys, then choose **Enable mappings** from the tray.

Do not run MacFlow as administrator. It does not install drivers or change keyboard registry settings. At runtime it does not access the network or record input or clipboard contents.

After updating files or changing configuration, choose **Quit MacFlow** from the tray and start it again to load the new version.

### Start from PowerShell (optional)

You can also open a regular PowerShell window in the project directory, adjust the AutoHotkey path and run:

```powershell
$ahk = 'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe'
& $ahk .\src\ahk\main.ahk
```

### VS Code setup

Follow the [integration instructions](integrations/vscode/README.md) to back up and merge the keybindings and settings. Each time MacFlow starts, select **Confirm VS Code setup for this run...** from the tray, then **Enable mappings**. VS Code retains native input until that confirmation.

The bridge distinguishes the editor from the integrated terminal: ⌘C copies a terminal selection and sends no Ctrl+C when nothing is selected; ⌘V pastes. Merge the configuration rather than replacing your personal settings.

### Start at sign-in

This is off by default. Select **Start at Windows sign-in (Native Mode)** from the tray to enable it; select it again to disable it. MacFlow still starts in Native Mode after sign-in, so mappings must be enabled manually.

This option creates `MacFlow.lnk` in your user Startup folder. Enable it from the project copy you intend to keep. After moving the project, launch it from the new location and select the option again to update the path. Disabling the app in Windows Startup settings does not delete the shortcut or update the tray check mark.

## Known limitations

### Input methods

The allowed layouts are US English (`04090409`) and Simplified Chinese (`08040804`). Mappings apply in both Chinese and English modes of Microsoft Pinyin. Compatibility with other Chinese input methods has not been verified.

- **With Microsoft Pinyin, ⌘⇧Z has caused unexpected Chinese/English mode switching and occasional Start menu openings. This issue is not fixed.** Use the application's native redo shortcut as a workaround.
- MacFlow does not detect active Pinyin composition. Using a mapped shortcut before committing the text may commit or cancel the current input. Finish choosing the text before using shortcuts.
- Ordinary typing and pressing Shift alone to switch Chinese/English modes do not trigger MacFlow mappings.

### Terminals and editor panels

**Windows Terminal is not mapped at all.** Embedded terminal panels in Claude, Codex, Visual Studio and similar mapped applications share the editor's mappings; MacFlow cannot distinguish their focus. ⌘C sends Ctrl+C and may interrupt a command. ⌘Z and ⌘S may suspend a shell job or pause output. Switch to Native Mode and use the terminal's native shortcuts when working in these panels.

Unreal Editor viewports also receive mapped output. For example, ⌘→ sends End and may invoke a viewport command. Use text navigation mappings in text input areas. The current process match is UE5's `UnrealEditor.exe`.

Codex is identified by the process name `ChatGPT.exe`, so the ChatGPT desktop application with the same process name is also affected.

### Features not currently provided

- **⌘L is not mapped.** Windows may still treat it as Win+L and lock the screen. Use physical Ctrl+L for the address bar.
- Explorer's ⌘Backspace deletion mapping is disabled.
- Mappings cannot be isolated to a particular keyboard.
- Application matching uses process names. It cannot identify games, remote desktop sessions or other special content inside a browser. Switch to Native Mode when you need native keyboard behavior.

## Disable, troubleshoot and uninstall

Choose **Native Mode (disable mappings)** from the tray to disable mappings, or **Quit MacFlow** to exit. The emergency disable shortcut is **Ctrl+Alt+F12**.

If a mapping does not work, reopen **Status...** and check the mode, error and **Last mapped-chord decision**. Common reasons include an application or layout outside the allowed list, an elevated window, or missing VS Code confirmation. Status is a snapshot taken when opened. The last decision may belong to an earlier action, so check its age.

For stuck keys or an unresponsive process, follow the [recovery instructions](docs/rollback.md). If you use Task Manager, end only the relevant MacFlow process, not other AutoHotkey scripts.

To uninstall, quit MacFlow first. If start at sign-in was enabled, disable it from the tray or remove `MacFlow.lnk` from the Startup folder, then delete the desktop shortcut and project copy. Remove only the MacFlow additions from VS Code as described in the [integration instructions](integrations/vscode/README.md), keeping your personal settings.

## Configuration and development

Configuration lives in `config/` and uses a JSON-compatible subset of YAML. Set an application's `enabled` field to `false` in `config/apps.yaml` to disable its mappings. Removing `08040804` from `allowed_hkls` leaves Simplified Chinese layouts native. Regenerate the configuration and restart MacFlow after edits; do not edit `build/generated/` directly.

Building and testing require Python 3.9+. The full unit test suite also requires Git. From the project root, run:

```powershell
python tools\validate-config.py
python tools\generate-config.py
python tools\generate-config.py --check
python -m unittest discover -s tests -p "test_*.py"
```

If `python` is unavailable, use the command or full path for your installed interpreter. On macOS/Linux, use `python3`.

Windows self-checks use an installed AutoHotkey runtime to check configuration loading and Native hotkey registration separately. They do not send test keystrokes:

```powershell
$ahk = 'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe'
powershell -NoProfile -File .\tools\smoke-tests.ps1 -AutoHotkeyPath $ahk -SelfTest
powershell -NoProfile -File .\tools\smoke-tests.ps1 -AutoHotkeyPath $ahk -RegistrationTest
```

If execution policy blocks a downloaded PowerShell script, review it and use `Unblock-File .\tools\smoke-tests.ps1` to remove that file's download mark. If the current policy still prevents execution, add `-ExecutionPolicy Bypass` to that invocation only; there is no need to change the global policy. Resolve self-check failures or AHK warnings before proceeding.

To build a preview package from a Git checkout, stage the intended release files, then run:

```powershell
python tools\package-preview.py
python tools\package-preview.py --check
```

The outputs are `dist/MacFlow-development-preview.zip` and `dist/manifest.json`. The package includes both READMEs but not AutoHotkey. Packaging includes only tracked, staged files in the selected release paths; local evidence and untracked files are excluded. `--check` verifies reproducibility without writing files. Running an extracted preview does not require Git.

Automated checks cover configuration, generated files, packaging and parts of AHK initialization. **They do not establish physical keyboard compatibility.** Query release acceptance with `tools/validate-config.py --gate prototype` or `--gate v1`; valid configuration and accepted release status are separate results.

Record physical tests in `tests/evidence/`. Do not directly edit `config/release.yaml` in a copy being used for testing: it is checked during startup, and changes made in a development checkout must be followed immediately by configuration generation.

- [Shortcut configuration](config/mappings.yaml) · [Application configuration](config/apps.yaml)
- [Compatibility matrix](docs/compatibility-matrix.md) · [Test report](docs/test-report.md)
- [Manual checklist](tests/manual-checklist.md) · [VS Code integration](integrations/vscode/README.md)
- [Development contracts](docs/contracts.md) · [Implementation decisions](docs/decisions.md)

Some linked documents are currently available only in Chinese.
