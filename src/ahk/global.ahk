; DEVELOPMENT PREVIEW: these handlers have not run on Windows hardware.
; Input/router owns exact-chord matching, integrity/layout checks and SendLevel.
MF_GlobalAction(action, profile) {
    global MF
    if !IsObject(profile)
        return false

    if action = "app_next" || action = "app_previous" {
        ; Only Alt is owned across repetitions. Root's polling/lifecycle functions
        ; release it on LWin up, Esc, timeout, bypass, suspend, disable and exit.
        starting := !MF.SwitcherActive
        if starting {
            MF.SwitchingHwnd := WinExist("A")
            MF.SwitcherActive := true
        }
        MF.SwitcherStarted := A_TickCount
        try {
            MF_HoldSynthetic("LAlt")
            ; Preserve owned Alt while AHK adjusts Win/Ctrl/Shift for this tap.
            ; Do not emit an explicit physical-modifier key-up ourselves.
            if !MF_SendTap(action = "app_previous" ? "{Blind#^+}+{Tab}" : "{Blind#^+}{Tab}") {
                ; No Tab reached Windows: never keep the owned Alt held. Before any
                ; Tab there is no switcher, so mask the release from the menu bar.
                MF_CancelSwitch(starting)
            }
        } catch {
            MF_CancelSwitch()
            throw
        }
        return true
    }

    ; Code.exe / Cursor.exe cannot identify editor vs terminal focus. Dedicated
    ; triggers are interpreted by the manually installed native bindings.
    if profile.Id = "vscode" || profile.Id = "cursor" {
        if !MF_IntegrationReady(profile)
            return false
        static bridge := Map(
            "copy", "^!{F13}", "paste", "^!{F14}",
            "cut", "^!{F15}", "select_all", "^!{F16}",
            "undo", "^!{F17}", "redo", "^!{F18}",
            "save", "^!{F19}", "find", "^!{F20}",
            "word_left", "^!{F21}", "word_right", "^!{F22}",
            "select_word_left", "^!{F23}", "select_word_right", "^!{F24}",
            "delete_word", "^!+{F13}", "line_start", "^!+{F14}",
            "line_end", "^!+{F15}", "document_start", "^!+{F16}",
            "document_end", "^!+{F17}")
        if !bridge.Has(action)
            return false
        MF_SendTap(bridge[action])
        return true
    }

    ; No terminal generic fallback, even if future configuration is mistaken.
    ; Claude, Codex, Visual Studio and Unreal Editor take Notepad's keys; none of
    ; them can tell a built-in terminal panel from the editor (decisions.md #14).
    static direct := StrSplit("chrome|notepad|explorer|claude|codex|visual_studio|unreal|outlook|edge|wechat|word|excel|powerpoint|onenote|outlook_classic|discord|teams|whatsapp|github_desktop", "|")
    if !MF_Contains(direct, profile.Id)
        return false
    ; Ctrl+Up/Down move by paragraph in RichEdit and Chromium text, like Option+
    ; Up/Down on macOS. Only profiles with the paragraph context get them: Visual
    ; Studio keeps native Alt+Up/Down (move line), Unreal Editor is unverified.
    static paragraph := Map(
        "paragraph_up", "^{Up}", "paragraph_down", "^{Down}",
        "select_paragraph_up", "^+{Up}", "select_paragraph_down", "^+{Down}")
    if paragraph.Has(action) {
        if !MF_Contains(profile.Contexts, "paragraph")
            return false
        MF_SendTap(paragraph[action])
        return true
    }
    static keys := Map(
        "copy", "^c", "paste", "^v", "cut", "^x", "select_all", "^a",
        "undo", "^z", "redo", "^y", "save", "^s", "find", "^f",
        "word_left", "^{Left}", "word_right", "^{Right}",
        "select_word_left", "^+{Left}", "select_word_right", "^+{Right}",
        "delete_word", "^{Backspace}", "line_start", "{Home}",
        "line_end", "{End}", "document_start", "^{Home}",
        "document_end", "^{End}")
    if !keys.Has(action)
        return false
    ; Explorer's generic subset is intentionally limited to file clipboard and
    ; selection commands. Text navigation/save/find are not inferred from focus.
    if profile.Id = "explorer" && action != "copy" && action != "paste" && action != "cut" && action != "select_all"
        return false
    ; Basic editing excludes Save: Teams Ctrl+S can send a meeting request.
    static basic := StrSplit("discord|teams|whatsapp|github_desktop", "|")
    if MF_Contains(basic, profile.Id) && action = "save"
        return false
    ; In new Outlook, Ctrl+F forwards mail. Command+F opens mail search instead.
    if profile.Id = "outlook" && action = "find" {
        MF_SendTap("^e")
        return true
    }
    ; Classic Outlook uses F4 to find text in an open mail item. Ctrl+F forwards;
    ; Ctrl+E centers text when composing, so it is not a generic Find shortcut.
    if profile.Id = "outlook_classic" && action = "find" {
        MF_SendTap("{F4}")
        return true
    }
    MF_SendTap(keys[action])
    return true
}
