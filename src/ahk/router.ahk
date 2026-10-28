; No foreground title, text, password or clipboard inspection.
; reason receives a fixed diagnostic label; it never contains key names.
MF_CurrentProfile(&reason := "") {
    global MF
    if !MF.Enabled || !IsObject(MF.Config) || A_IsAdmin {
        reason := "Native Mode or configuration unavailable"
        return 0
    }
    hwnd := WinExist("A")
    if !hwnd {
        reason := "no foreground window"
        return 0
    }
    if !MF_ForegroundSafe(hwnd, &reason)
        return 0
    try process := StrLower(WinGetProcessName("ahk_id " hwnd))
    catch {
        reason := "foreground process unavailable"
        return 0
    }
    if MF_Contains(MF.Config.BypassProcesses, process) {
        reason := "bypassed process " process
        return 0
    }
    for profile in MF.Config.Profiles {
        if !profile.Enabled || !MF_Contains(profile.Processes, process)
            continue
        if profile.RequiresIntegration && !MF_IntegrationReady(profile) {
            reason := (profile.Id = "cursor" ? "Cursor" : "VS Code") " setup not confirmed for this run"
            return 0
        }
        if profile.Id = "explorer" {
            try {
                if !MF_Contains(["CabinetWClass", "ExploreWClass"], WinGetClass("ahk_id " hwnd)) {
                    reason := "Explorer window is not a folder window"
                    return 0
                }
            } catch {
                reason := "Explorer window class unavailable"
                return 0
            }
        }
        reason := "profile " profile.Id
        return profile
    }
    reason := "process " process " is not allowlisted"
    return 0
}

; Each editor requires its own per-run acknowledgement. Unknown integrations
; cannot inherit another editor's confirmation.
MF_IntegrationReady(profile) {
    global MF
    if profile.Id = "vscode"
        return MF.VscodeReady
    if profile.Id = "cursor"
        return MF.CursorReady
    return false
}

MF_ForegroundSafe(hwnd, &reason := "") {
    global MF
    try {
        pid := 0
        threadId := DllCall("User32\GetWindowThreadProcessId", "Ptr", hwnd, "UInt*", &pid, "UInt")
        if !threadId || !pid {
            reason := "foreground thread unavailable"
            return false
        }
        ; Keys reach the focus window, whose thread can differ from the top-level
        ; window's: Windows 11 Notepad edits on its own thread. A layout switch
        ; updates that input thread while the top-level thread can keep a stale
        ; layout (seen 2026-10-23: frame 08040804, editor 04090409). Only the
        ; input thread's layout therefore decides.
        if !MF_FocusWindow(threadId, &focus) {
            ; A failed query is not "no focus window": the input thread, and so
            ; its layout, is unknown. Never fall back to the top-level thread.
            reason := "focus window unavailable"
            return false
        }
        inputThread := focus ? DllCall("User32\GetWindowThreadProcessId", "Ptr", focus, "Ptr", 0, "UInt") : threadId
        if !inputThread {
            ; Thread 0 would read this script's own layout, so treat it as unknown.
            reason := "focus thread unavailable"
            return false
        }
        ; Simplified Chinese 08040804 maps in Chinese and English mode alike, so no
        ; IME state is read: a chord during composition sends the same Windows
        ; shortcut that pressing it natively would.
        layout := MF_ThreadLayout(inputThread)
        if !MF_Contains(MF.Config.AllowedLayouts, layout) {
            reason := "keyboard layout " layout " is not allowed"
            return false
        }
        if !MF_ProcessNotElevated(pid) {
            reason := "elevated or unknown integrity"
            return false
        }
        return true
    } catch {
        reason := "foreground check failed"
        return false
    }
}

MF_ThreadLayout(threadId) {
    return Format("{:08X}", DllCall("User32\GetKeyboardLayout", "UInt", threadId, "UPtr") & 0xFFFFFFFF)
}

; focus receives GUITHREADINFO.hwndFocus of the thread's input queue, which is 0
; when the queue has no focus window. Returns false when the query itself fails.
MF_FocusWindow(threadId, &focus) {
    focus := 0
    info := Buffer(A_PtrSize = 8 ? 72 : 48, 0)
    NumPut("UInt", info.Size, info)
    if !DllCall("User32\GetGUIThreadInfo", "UInt", threadId, "Ptr", info)
        return false
    focus := NumGet(info, A_PtrSize = 8 ? 16 : 12, "Ptr")
    return true
}

MF_ProcessNotElevated(pid) {
    process := DllCall("Kernel32\OpenProcess", "UInt", 0x1000, "Int", false, "UInt", pid, "Ptr")
    if !process
        return false
    token := 0
    try {
        if !DllCall("Advapi32\OpenProcessToken", "Ptr", process, "UInt", 0x0008, "Ptr*", &token)
            return false
        elevated := Buffer(4, 0), length := 0
        if !DllCall("Advapi32\GetTokenInformation", "Ptr", token, "Int", 20, "Ptr", elevated, "UInt", 4, "UInt*", &length)
            return false
        if NumGet(elevated, 0, "UInt") != 0
            return false
        ; A non-elevated token alone does not establish its integrity level.
        length := 0
        DllCall("Advapi32\GetTokenInformation", "Ptr", token, "Int", 25, "Ptr", 0, "UInt", 0, "UInt*", &length)
        if length < A_PtrSize + 4 || length > 4096
            return false
        mandatoryLabel := Buffer(length, 0)
        if !DllCall("Advapi32\GetTokenInformation", "Ptr", token, "Int", 25, "Ptr", mandatoryLabel, "UInt", length, "UInt*", &length)
            return false
        sid := NumGet(mandatoryLabel, 0, "Ptr")
        if !sid || !DllCall("Advapi32\IsValidSid", "Ptr", sid, "Int")
            return false
        countPtr := DllCall("Advapi32\GetSidSubAuthorityCount", "Ptr", sid, "Ptr")
        if !countPtr || !(count := NumGet(countPtr, 0, "UChar"))
            return false
        ridPtr := DllCall("Advapi32\GetSidSubAuthority", "Ptr", sid, "UInt", count - 1, "Ptr")
        if !ridPtr
            return false
        rid := NumGet(ridPtr, 0, "UInt")
        ; Known low/medium only; high, system, medium-plus and unknown bypass.
        return rid = 0x1000 || rid = 0x2000
    } finally {
        if token
            DllCall("Kernel32\CloseHandle", "Ptr", token)
        DllCall("Kernel32\CloseHandle", "Ptr", process)
    }
}

MF_SelectRule(chord, profile) {
    global MF
    if !IsObject(profile)
        return 0
    selected := 0
    for rule in MF.Config.Rules {
        if !rule.Enabled || rule.Chord != chord || !MF_Intersects(rule.Contexts, profile.Contexts)
            continue
        if !selected || rule.Priority > selected.Priority
            selected := rule
    }
    return selected
}

MF_RunAction(action, profile) {
    ; An unknown handler is a configuration/runtime fault, never a blind fallback.
    if MF_GlobalAction(action, profile)
        return
    if MF_BrowserAction(action, profile)
        return
    if MF_ExplorerAction(action, profile)
        return
    if MF_TerminalAction(action, profile)
        return
    throw Error("No safe handler for action: " action)
}
