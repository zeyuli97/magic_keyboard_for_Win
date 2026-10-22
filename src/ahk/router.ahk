; No foreground title, text, password or clipboard inspection.
MF_CurrentProfile() {
    global MF
    if !MF.Enabled || !IsObject(MF.Config) || A_IsAdmin
        return 0
    hwnd := WinExist("A")
    if !hwnd || !MF_ForegroundSafe(hwnd)
        return 0
    try process := StrLower(WinGetProcessName("ahk_id " hwnd))
    catch
        return 0
    if MF_Contains(MF.Config.BypassProcesses, process)
        return 0
    for profile in MF.Config.Profiles {
        if !profile.Enabled || !MF_Contains(profile.Processes, process)
            continue
        if profile.RequiresIntegration && !MF.VscodeReady
            return 0
        if profile.Id = "explorer" {
            try {
                if !MF_Contains(["CabinetWClass", "ExploreWClass"], WinGetClass("ahk_id " hwnd))
                    return 0
            } catch {
                return 0
            }
        }
        return profile
    }
    return 0
}

MF_ForegroundSafe(hwnd) {
    global MF
    try {
        pid := 0
        thread := DllCall("User32\GetWindowThreadProcessId", "Ptr", hwnd, "UInt*", &pid, "UInt")
        if !thread || !pid
            return false
        layout := Format("{:08X}", DllCall("User32\GetKeyboardLayout", "UInt", thread, "UPtr") & 0xFFFFFFFF)
        if !MF_Contains(MF.Config.AllowedLayouts, layout)
            return false
        return MF_ProcessNotElevated(pid)
    } catch {
        return false
    }
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
        return NumGet(elevated, 0, "UInt") = 0
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
