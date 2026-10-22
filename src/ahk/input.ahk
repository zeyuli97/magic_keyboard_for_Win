MF_RegisterMappings() {
    global MF
    MF.Pending := Map()
    MF.DispatchHwnd := 0
    chords := Map()
    for rule in MF.Config.Rules {
        if !rule.Enabled || chords.Has(rule.Chord)
            continue
        chords[rule.Chord] := true
        predicate := MF_CanHandle.Bind(rule.Chord)
        callback := MF_HandleChord.Bind(rule.Chord)
        HotIf(predicate)
        try {
            key := MF_HotkeyName(rule.Chord)
            Hotkey(key, callback, "On I1 T1")
            MF.Registered.Push({Key: key, Predicate: predicate, Callback: callback})
        } finally {
            HotIf()
        }
    }
}

MF_HotkeyName(chord) {
    parts := StrSplit(chord, "+")
    modifier := parts[1] = "LWin" ? "<#" : "<!"
    shift := parts.Length = 3 ? "+" : ""
    ; Wildcard permits our owned synthetic Alt during switching; the physical
    ; predicate below rejects every unsupported real modifier combination.
    return "$*" modifier shift parts[parts.Length]
}

MF_PhysicalChordMatches(chord) {
    parts := StrSplit(chord, "+")
    wantsWin := parts[1] = "LWin"
    wantsShift := parts.Length = 3
    if GetKeyState("LCtrl", "P") || GetKeyState("RCtrl", "P") || GetKeyState("RWin", "P") || GetKeyState("RAlt", "P")
        return false
    if !!GetKeyState("LWin", "P") != wantsWin || !!GetKeyState("LAlt", "P") = wantsWin
        return false
    return !!(GetKeyState("LShift", "P") || GetKeyState("RShift", "P")) = wantsShift
}

MF_CanHandle(chord, *) {
    global MF
    if !MF.Enabled || !MF_PhysicalChordMatches(chord)
        return false
    ; Alt-Tab may focus an OS switcher, so subsequent Tab uses the captured session.
    if MF.SwitcherActive && (chord = "LWin+Tab" || chord = "LWin+Shift+Tab")
        return true
    try {
        hwnd := WinExist("A")
        profile := MF_CurrentProfile()
        rule := MF_SelectRule(chord, profile)
        if !rule || WinExist("A") != hwnd
            return false
        MF.Pending[chord] := {Hwnd: hwnd, ProfileId: profile.Id, RuleId: rule.Id, Tick: A_TickCount}
        return true
    } catch {
        return false
    }
}

MF_HandleChord(chord, *) {
    global MF
    if !MF.Enabled || !MF_PhysicalChordMatches(chord)
        return
    if MF.SwitcherActive && (chord = "LWin+Tab" || chord = "LWin+Shift+Tab") {
        MF_RunAction(chord = "LWin+Tab" ? "app_next" : "app_previous", {Id: "switcher"})
        return
    }
    ; Recheck focus after hook dispatch. If it moved, consume instead of injecting
    ; into a new window. No replay can safely guarantee the old target.
    if !MF.Pending.Has(chord)
        return
    pending := MF.Pending[chord]
    MF.Pending.Delete(chord)
    if WinExist("A") != pending.Hwnd || A_TickCount - pending.Tick > 500
        return
    profile := MF_CurrentProfile()
    rule := MF_SelectRule(chord, profile)
    if !rule || rule.Id != pending.RuleId || profile.Id != pending.ProfileId
        return
    MF.DispatchHwnd := pending.Hwnd
    try MF_RunAction(rule.Action, profile)
    finally MF.DispatchHwnd := 0
}

MF_SendTap(keys) {
    global MF
    ; Complete chords only; held synthetic Alt is managed explicitly elsewhere.
    if MF.HasOwnProp("DispatchHwnd") && MF.DispatchHwnd && WinExist("A") != MF.DispatchHwnd
        return
    SendLevel(0)
    SendEvent(keys)
}

MF_HoldSynthetic(key) {
    global MF
    if key != "LAlt"
        throw Error("Unexpected held synthetic key.")
    if GetKeyState(key, "P")
        throw Error("Cannot own a physically held modifier.")
    if !MF.OwnedKeys.Has(key) {
        MF.OwnedKeys[key] := true
        SendLevel(0)
        SendEvent("{Blind}{" key " down}")
    }
}

MF_ReleaseSynthetic(key) {
    global MF
    if !MF.OwnedKeys.Has(key)
        return
    MF.OwnedKeys.Delete(key)
    ; If physically pressed meanwhile, its eventual physical up owns release.
    if !GetKeyState(key, "P") {
        SendLevel(0)
        SendEvent("{Blind}{" key " up}")
    }
}

MF_CancelSwitch() {
    global MF
    MF.SwitcherActive := false
    MF.SwitcherStarted := 0
    MF.SwitchingHwnd := 0
    MF_ReleaseSynthetic("LAlt")
}

MF_ResetInput() {
    global MF
    MF_CancelSwitch()
    if MF.HasOwnProp("Pending")
        MF.Pending.Clear()
    MF.DispatchHwnd := 0
    ; No physical Ctrl, Win, Shift or Option state is blindly reset.
}

MF_PollInput() {
    global MF
    if !MF.SwitcherActive
        return
    if !MF.Enabled || !GetKeyState("LWin", "P") || GetKeyState("Esc", "P") || A_TickCount - MF.SwitcherStarted > 10000 {
        MF_CancelSwitch()
        return
    }
    hwnd := WinExist("A")
    if !hwnd || !MF_ForegroundSafe(hwnd)
        MF_CancelSwitch()
}
