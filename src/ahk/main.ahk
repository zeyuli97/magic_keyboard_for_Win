#Requires AutoHotkey v2.0.19+
#SingleInstance Off
#Warn

; DEVELOPMENT PREVIEW. No AHK/Windows/hardware success is claimed by this file.
; A runtime mutex prevents duplicate mapping engines without killing a live one.
; Source includes are static; generated configuration is data loaded at runtime.
#Include %A_ScriptDir%\config.ahk
#Include %A_ScriptDir%\input.ahk
#Include %A_ScriptDir%\router.ahk
#Include %A_ScriptDir%\global.ahk
#Include %A_ScriptDir%\terminal.ahk
#Include %A_ScriptDir%\browser.ahk
#Include %A_ScriptDir%\explorer.ahk
#Include %A_ScriptDir%\emergency.ahk

SplitPath(A_ScriptDir, , &MF_SourceDir)
SplitPath(MF_SourceDir, , &MF_RepoRoot)
global MF := {
    Enabled: false, Config: 0, ConfigError: "", Root: MF_RepoRoot,
    VscodeReady: false, OwnedKeys: Map(), SwitcherActive: false,
    SwitchingHwnd: 0, SwitcherStarted: 0, Registered: [],
    SessionRegistered: false, MutexHandle: 0, TrayReady: false,
    LastReason: "Started in Native Mode", ShuttingDown: false,
    InputDispatchActive: false, ResetPending: false
}
MF_Main()

MF_Main() {
    global MF
    ; Disable AHK's input history and executed-line history before hook setup.
    KeyHistory(0)
    ListLines(false)
    SendLevel(0)
    SetWorkingDir(MF.Root)
    selfTest := false
    for argument in A_Args {
        if argument = "--help" {
            MF_WriteStdout("MacFlow DEVELOPMENT PREVIEW`n"
                . "Usage: AutoHotkey64.exe src\ahk\main.ahk [--self-test|--help]`n"
                . "Normal launch starts in Native Mode. Enable from the tray only.`n"
                . "--self-test loads config and exits Native; no mappings/hooks are installed.`n")
            ExitApp(0)
        }
        if argument = "--self-test"
            selfTest := true
        else {
            MF_WriteStdout("Unknown argument. Use --help.`n")
            ExitApp(2)
        }
    }
    if A_IsAdmin || A_PtrSize != 8 {
        message := "MacFlow requires a non-elevated 64-bit AutoHotkey v2 process. No mappings were enabled."
        MF_WriteStdout(message "`n")
        if !selfTest
            MsgBox(message, "MacFlow - start refused", "Iconx")
        ExitApp(2)
    }
    try MF.Config := MF_LoadConfig(MF.Root)
    catch Error as err
        MF.ConfigError := err.Message
    if selfTest {
        if MF.ConfigError != "" {
            MF_WriteStdout("SELF-TEST FAIL: " MF.ConfigError "`n")
            ExitApp(1)
        }
        MF_WriteStdout("SELF-TEST PASS: configuration loaded; Native Mode; no mappings/hooks installed. Hardware NOT TESTED.`n")
        ExitApp(0)
    }
    OnExit(MF_OnExit)
    MF.MutexHandle := DllCall("Kernel32\CreateMutexW", "Ptr", 0, "Int", false,
        "Str", "Local\MacFlow-AHK-Development-Preview", "Ptr")
    mutexError := A_LastError
    if !MF.MutexHandle || mutexError = 183 {
        MsgBox("MacFlow is already running, or its single-process guard could not be created."
            . "`nUse the existing tray icon. No second mapping engine was started.", "MacFlow", "Icon!")
        ExitApp(3)
    }
    Persistent(true)
    MF_BuildTray()
    OnError(MF_OnRuntimeError)
    try {
        InstallKeybdHook()
        OnMessage(0x0218, MF_OnPowerBroadcast)
        OnMessage(0x02B1, MF_OnSessionChange)
        OnMessage(0x0011, MF_OnQueryEndSession)
        MF.SessionRegistered := DllCall("Wtsapi32\WTSRegisterSessionNotification",
            "Ptr", A_ScriptHwnd, "UInt", 0, "Int") != 0
        if !MF.SessionRegistered
            throw Error("Session notification registration failed. Restart MacFlow after Windows sign-in completes.")
        if MF.ConfigError = ""
            MF_RegisterMappings()
        MF_RegisterEmergency()
        SetTimer(MF_LifecyclePoll, 30)
    } catch Error as err {
        MF.ConfigError := "Initialization failed: " err.Message
        MF_Disable()
    }
    MF_UpdateTray()
    if MF.ConfigError != ""
        TrayTip("Native Mode: " MF.ConfigError, "MacFlow configuration / startup error", 3)
}

MF_BuildTray() {
    global MF
    A_TrayMenu.Delete()
    A_TrayMenu.Add("Status...", MF_ShowStatus)
    A_TrayMenu.Add()
    A_TrayMenu.Add("Enable mappings", MF_SetEnabled.Bind(true))
    A_TrayMenu.Add("Native Mode (disable mappings)", MF_Disable)
    A_TrayMenu.Add()
    A_TrayMenu.Add("Confirm VS Code setup for this run...", MF_ConfirmVscode)
    A_TrayMenu.Add("Revoke VS Code setup confirmation", MF_RevokeVscode)
    A_TrayMenu.Add()
    A_TrayMenu.Add("Quit MacFlow", MF_Quit)
    A_TrayMenu.Default := "Status..."
    MF.TrayReady := true
    MF_UpdateTray()
}

MF_SetEnabled(enabled, *) {
    global MF
    if !enabled {
        MF_Disable()
        return
    }
    if MF.ConfigError != "" || !IsObject(MF.Config) || A_IsAdmin {
        MF_Disable()
        MsgBox("Enable refused. See Status for the startup/configuration error."
            . "`nRun a standard, non-administrator AHK process.", "MacFlow", "Icon!")
        return
    }
    if MF_ModifiersDown() {
        MF_Disable()
        MsgBox("Release Command/Win, Control, Option/Alt and Shift on every keyboard,"
            . " then choose Enable mappings again.", "MacFlow", "Icon!")
        return
    }
    MF_ResetInput()
    MF.Enabled := true
    MF.LastReason := "Enabled manually; unknown/elevated apps and non-US layouts still bypass"
    MF_UpdateTray()
}

MF_Disable(*) {
    global MF
    ; Turn routing off before releasing only synthetic keys tracked by input.ahk.
    MF.Enabled := false
    MF_ResetInput()
    MF.LastReason := "Native Mode selected"
    MF_UpdateTray()
}

MF_ModifiersDown() {
    ; Never release a physical modifier merely because it is down.
    for entry in [["LWin", 0x5B], ["RWin", 0x5C], ["LControl", 0xA2],
            ["RControl", 0xA3], ["LAlt", 0xA4], ["RAlt", 0xA5],
            ["LShift", 0xA0], ["RShift", 0xA1]] {
        ; Async state also catches a modifier held before the hook was installed.
        if GetKeyState(entry[1], "P") || (DllCall("User32\GetAsyncKeyState", "Int", entry[2], "Short") & 0x8000)
            return true
    }
    return false
}

MF_ConfirmVscode(*) {
    global MF
    MF_Disable()
    result := MsgBox("Confirm only after following integrations\vscode\README.md:"
        . "`n`n- Back up and merge the native keybindings and settings manually."
        . "`n- Check reserved Ctrl+Alt+F13..F24 and shifted variants for collisions."
        . "`n- Confirm terminal.integrated.sendKeybindingsToShell is false."
        . "`n- Check editor focus, terminal selection and no-selection copy behavior."
        . "`n`nThis is a per-run setup acknowledgement, not a hardware PASS."
        . "`nMappings stay Native until you explicitly enable them."
        . "`n`nIs the documented setup complete?", "MacFlow - VS Code setup", "YesNo Default2 Icon!")
    MF.VscodeReady := result = "Yes"
    MF.LastReason := MF.VscodeReady ? "VS Code setup confirmed for this run; Native Mode" : "VS Code setup not confirmed; Native Mode"
    MF_UpdateTray()
}

MF_RevokeVscode(*) {
    global MF
    MF_Disable()
    MF.VscodeReady := false
    MF.LastReason := "VS Code setup confirmation revoked; Native Mode"
    MF_UpdateTray()
}

MF_UpdateTray() {
    global MF
    if !MF.TrayReady
        return
    mode := MF.Enabled ? "Enabled" : "Native Mode"
    A_IconTip := "MacFlow - " mode "`nDEVELOPMENT PREVIEW / Windows hardware NOT TESTED"
    if MF.Enabled {
        A_TrayMenu.Check("Enable mappings")
        A_TrayMenu.Uncheck("Native Mode (disable mappings)")
    } else {
        A_TrayMenu.Uncheck("Enable mappings")
        A_TrayMenu.Check("Native Mode (disable mappings)")
    }
    if MF.ConfigError != "" || !IsObject(MF.Config)
        A_TrayMenu.Disable("Enable mappings")
    else
        A_TrayMenu.Enable("Enable mappings")
    if MF.VscodeReady {
        A_TrayMenu.Check("Confirm VS Code setup for this run...")
        A_TrayMenu.Enable("Revoke VS Code setup confirmation")
    } else {
        A_TrayMenu.Uncheck("Confirm VS Code setup for this run...")
        A_TrayMenu.Disable("Revoke VS Code setup confirmation")
    }
}

MF_ShowStatus(*) {
    global MF
    hash := IsObject(MF.Config) ? MF.Config.Hash : "not loaded"
    MsgBox("DEVELOPMENT PREVIEW - Windows hardware NOT TESTED"
        . "`nMode: " (MF.Enabled ? "Enabled" : "Native Mode")
        . "`nBackend: AHK only; no Kanata or controller process"
        . "`nVS Code setup acknowledged this run: " (MF.VscodeReady ? "yes" : "no")
        . "`nConfig hash: " hash
        . "`nLast transition: " MF.LastReason
        . "`nError: " (MF.ConfigError != "" ? MF.ConfigError : "none")
        . "`n`nEnabled mappings affect ALL keyboards. Device identity is unknown."
        . "`nOnly exact US English HKL 04090409 and allowlisted non-elevated apps qualify."
        . "`nChinese IME/other layouts, Windows Terminal, physical Ctrl and right Command stay native."
        . "`nCommand+L is blocked; physical Win+L may still lock Windows."
        . "`n`nRecovery: tray Native Mode / Quit; emergency Ctrl+Alt+F12 disables only."
        . "`nNo key contents, clipboard contents or runtime files are recorded.", "MacFlow status")
}

MF_LifecyclePoll() {
    global MF
    try MF_PollInput()
    catch Error as err {
        MF.ConfigError := "Input polling failed; restart required: " err.Message
        MF_Disable()
        SetTimer(MF_LifecyclePoll, 0)
    }
}

MF_OnPowerBroadcast(wParam, *) {
    global MF
    ; Suspend and all standard resume notifications require manual re-enable.
    if wParam = 4 || wParam = 6 || wParam = 7 || wParam = 18 {
        MF_Disable()
        MF.LastReason := "Power suspend/resume; Native Mode, manual re-enable required"
    }
}

MF_OnSessionChange(*) {
    global MF
    MF_Disable()
    MF.LastReason := "Windows session changed; Native Mode, manual re-enable required"
}

MF_OnQueryEndSession(*) {
    MF_Disable()
    ; No return value: do not veto or intercept shutdown/logoff processing.
}

MF_OnRuntimeError(err, mode) {
    global MF
    MF.Enabled := false
    MF.ConfigError := "Runtime error; restart required: " (IsObject(err) && HasProp(err, "Message") ? err.Message : "unknown exception")
    try MF_ResetInput()
    try MF_UpdateTray()
    ; Retain AHK's normal error reporting; no input contents are logged.
    return 0
}

MF_Quit(*) {
    MF_Disable()
    ExitApp(0)
}

MF_OnExit(*) {
    global MF
    MF.Enabled := false
    MF.ShuttingDown := true
    try SetTimer(MF_LifecyclePoll, 0)
    try MF_ResetInput()
    if MF.SessionRegistered {
        try DllCall("Wtsapi32\WTSUnRegisterSessionNotification", "Ptr", A_ScriptHwnd, "Int")
        MF.SessionRegistered := false
    }
    if MF.MutexHandle {
        DllCall("Kernel32\CloseHandle", "Ptr", MF.MutexHandle)
        MF.MutexHandle := 0
    }
}

MF_WriteStdout(message) {
    try FileAppend(message, "*", "UTF-8")
}
