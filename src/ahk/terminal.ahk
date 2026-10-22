; Standalone terminal hosts are bypassed in the prototype. There is no Ctrl+C
; fallback: a copy request must never become a shell interrupt.
MF_TerminalAction(action, profile) {
    global MF
    if !IsObject(profile) || profile.Id != "vscode" || !MF.VscodeReady
        return false
    ; Aliases for a future explicit VS Code context mapping; the current
    ; configuration routes shared copy/paste via MF_GlobalAction directly.
    if action = "terminal_copy"
        return MF_GlobalAction("copy", profile)
    if action = "terminal_paste"
        return MF_GlobalAction("paste", profile)
    return false
}
