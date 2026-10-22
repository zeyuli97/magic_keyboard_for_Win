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
    ; These observers never suppress native keys. Cleanup happens on modifier
    ; transitions as well as the polling fallback, not only on the next Tab.
    HotIf(MF_SwitcherWatchActive)
    try {
        for key in ["LCtrl", "RCtrl", "RWin", "RAlt", "LAlt", "Esc", "LWin up"]
            Hotkey("$~*" key, MF_SwitcherTransition, "On I1")
    } finally {
        HotIf()
    }
}

MF_SwitcherWatchActive(*) {
    global MF
    return MF.SwitcherActive
}

MF_SwitcherTransition(*) {
    MF_CancelSwitch()
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
    ; Critical buffers ordinary hotkeys/timers, but low-numbered OnMessage
    ; callbacks can still interrupt. Reset must defer ownership cleanup until
    ; this transaction returns; otherwise an interrupted Alt-down could resume
    ; after its ownership record has already been cleared.
    previousCritical := A_IsCritical
    Critical("On")
    MF.InputDispatchActive := true
    try MF_HandleChordLocked(chord)
    finally {
        MF.InputDispatchActive := false
        try {
            if MF.ResetPending
                MF_ResetInput()
        } finally Critical(previousCritical)
    }
}

MF_HandleChordLocked(chord) {
    global MF
    if !MF.Enabled || !MF_PhysicalChordMatches(chord)
        return
    if MF.SwitcherActive && (chord = "LWin+Tab" || chord = "LWin+Shift+Tab") {
        hwnd := WinExist("A")
        if !hwnd || !MF_ForegroundSafe(hwnd) {
            MF_CancelSwitch()
            return
        }
        MF_RunAction(chord = "LWin+Tab" ? "app_next" : "app_previous", {Id: "switcher"})
        return
    }
    if MF.SwitcherActive {
        MF_CancelSwitch()
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
    if !MF.Enabled
        return
    if MF.HasOwnProp("DispatchHwnd") && MF.DispatchHwnd && WinExist("A") != MF.DispatchHwnd
        return
    hwnd := WinExist("A")
    if !hwnd || !MF_ForegroundSafe(hwnd) {
        MF_ResetInput()
        return
    }
    if !MF.Enabled || WinExist("A") != hwnd
        return
    SendLevel(0)
    SendEvent(keys)
}

MF_HoldSynthetic(key) {
    global MF
    if !MF.Enabled || MF.ResetPending || !MF.InputDispatchActive
        throw Error("Cannot acquire a synthetic modifier in Native Mode.")
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
    ; If physically pressed meanwhile, its eventual physical up owns release.
    if !GetKeyState(key, "P") {
        SendLevel(0)
        SendEvent("{Blind}{" key " up}")
    }
    ; Keep ownership until key-up completes, including if OnExit interrupts.
    ; A nested cleanup may have already released/deleted the same owner.
    if MF.OwnedKeys.Has(key)
        MF.OwnedKeys.Delete(key)
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
    if MF.InputDispatchActive && !MF.ShuttingDown {
        ; MF_Disable has already stopped new routing. Keep owned state intact
        ; until the interrupted send finishes; the dispatch finally releases it.
        MF.ResetPending := true
        return
    }
    ; OnExit is final: no interrupted sender will resume after process exit.
    MF.ResetPending := false
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
    foreignModifier := GetKeyState("LCtrl", "P") || GetKeyState("RCtrl", "P") || GetKeyState("RWin", "P") || GetKeyState("RAlt", "P") || GetKeyState("LAlt", "P")
    if !MF.Enabled || !GetKeyState("LWin", "P") || GetKeyState("Esc", "P") || foreignModifier || A_TickCount - MF.SwitcherStarted > 10000 {
        MF_CancelSwitch()
        return
    }
    hwnd := WinExist("A")
    if !hwnd || !MF_ForegroundSafe(hwnd)
        MF_CancelSwitch()
}
