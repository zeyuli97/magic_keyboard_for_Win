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
    if !MF.Enabled
        return false
    if !MF_PhysicalChordMatches(chord) {
        MF_NoteDecision("Physical modifiers did not match a mapped chord")
        return false
    }
    ; Alt-Tab may focus an OS switcher, so subsequent Tab uses the captured session.
    if MF.SwitcherActive && (chord = "LWin+Tab" || chord = "LWin+Shift+Tab")
        return true
    try {
        reason := ""
        hwnd := WinExist("A")
        profile := MF_CurrentProfile(&reason)
        rule := MF_SelectRule(chord, profile)
        if !rule || WinExist("A") != hwnd {
            MF_NoteDecision(!profile ? "Bypassed: " reason
                : !rule ? "No mapping for this chord in profile " profile.Id
                : "Foreground changed during the decision")
            return false
        }
        MF.Pending[chord] := {Hwnd: hwnd, ProfileId: profile.Id, RuleId: rule.Id, Tick: A_TickCount}
        MF_NoteDecision("Accepted in profile " profile.Id)
        return true
    } catch {
        MF_NoteDecision("Decision failed")
        return false
    }
}

; RAM-only diagnostics for Status: a fixed reason label and when it happened.
; Never records key names, chords, text, window titles or clipboard data.
MF_NoteDecision(text) {
    global MF
    MF.LastDecision := text
    MF.LastDecisionTick := A_TickCount
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
    if !MF.Enabled
        return
    if !MF_PhysicalChordMatches(chord) {
        MF_NoteDecision("Consumed: modifiers changed before output")
        return
    }
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
    if !MF.Pending.Has(chord) {
        MF_NoteDecision("Consumed: no pending decision")
        return
    }
    pending := MF.Pending[chord]
    MF.Pending.Delete(chord)
    if WinExist("A") != pending.Hwnd || A_TickCount - pending.Tick > 500 {
        MF_NoteDecision("Consumed: foreground changed or decision expired")
        return
    }
    profile := MF_CurrentProfile()
    rule := MF_SelectRule(chord, profile)
    if !rule || rule.Id != pending.RuleId || profile.Id != pending.ProfileId {
        MF_NoteDecision("Consumed: profile or rule changed")
        return
    }
    MF.DispatchHwnd := pending.Hwnd
    MF_NoteDecision("Dispatched in profile " profile.Id)
    try MF_RunAction(rule.Action, profile)
    finally MF.DispatchHwnd := 0
}

; Returns true only when the chord was actually sent to the foreground window.
MF_SendTap(keys) {
    global MF
    ; Complete chords only; held synthetic Alt is managed explicitly elsewhere.
    if !MF.Enabled
        return false
    ; The dispatch window, when there is one, is the only target; reading the
    ; foreground once avoids a second read that could name another window.
    hwnd := MF.HasOwnProp("DispatchHwnd") && MF.DispatchHwnd ? MF.DispatchHwnd : WinExist("A")
    if !MF_SendTargetSafe(hwnd)
        return false
    SendLevel(0)
    ; A physical Option chord leaves Alt logically down. Send releases it for the
    ; output and restores it afterwards, so Windows and apps can see Alt, or Left
    ; Alt+Shift, pressed with only modifiers in between: WinUI access keys, menu
    ; bars and the input-language hotkey react to that. An unassigned
    ; non-modifier key while Alt is still down, before the output and after the
    ; restore, breaks those patterns. Hypothesis fix, NOT hardware-verified.
    altGuard := GetKeyState("LAlt", "P")
    ; Shift has the same pattern when the output has no Shift (Command+Shift+Z
    ; sends Ctrl+Y): Send releases the held Shift and restores it, and an IME
    ; may read the restored Shift and the user's release as a lone Shift tap,
    ; which switches Pinyin between Chinese and English. Same hypothesis guard.
    shiftGuard := !InStr(keys, "+") && (GetKeyState("LShift", "P") || GetKeyState("RShift", "P"))
    if altGuard {
        SendEvent("{Blind}{vkE8}")
        ; The guard is a send of its own, with its own key delay, so the window,
        ; mode or layout may have changed meanwhile. Nothing is output yet:
        ; repeat the final checks and consume the chord if one fails.
        if !MF_SendTargetSafe(hwnd)
            return false
    }
    SendEvent(keys)
    ; Complete the guard only in the window that received the output.
    if WinExist("A") = hwnd && (altGuard && GetKeyState("LAlt") || shiftGuard && GetKeyState("Shift"))
        SendEvent("{Blind}{vkE8}")
    return true
}

; Final checks right before output: mappings are still enabled, and hwnd is
; still the foreground window with a safe layout and integrity.
MF_SendTargetSafe(hwnd) {
    global MF
    reason := "no foreground window"
    if !hwnd || !MF_ForegroundSafe(hwnd, &reason) {
        MF_NoteDecision("Not sent: " reason)
        MF_ResetInput()
        return false
    }
    if !MF.Enabled
        return false
    if WinExist("A") != hwnd {
        MF_NoteDecision("Not sent: foreground changed")
        return false
    }
    return true
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

MF_ReleaseSynthetic(key, masked := false) {
    global MF
    if !MF.OwnedKeys.Has(key)
        return
    ; If physically pressed meanwhile, its eventual physical up owns release.
    if !GetKeyState(key, "P") {
        SendLevel(0)
        ; Masked: an unassigned key separates our Alt down and up, so a lone
        ; synthetic Alt cannot activate the foreground menu bar. Not used while
        ; the Alt-Tab switcher may be open.
        SendEvent(masked ? "{Blind}{vkE8}{" key " up}" : "{Blind}{" key " up}")
    }
    ; Keep ownership until key-up completes, including if OnExit interrupts.
    ; A nested cleanup may have already released/deleted the same owner.
    if MF.OwnedKeys.Has(key)
        MF.OwnedKeys.Delete(key)
}

MF_CancelSwitch(masked := false) {
    global MF
    MF.SwitcherActive := false
    MF.SwitcherStarted := 0
    MF.SwitchingHwnd := 0
    MF_ReleaseSynthetic("LAlt", masked)
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
