; Explorer deletion remains BLOCKED. No Delete/Shift+Delete is synthesized.
MF_ExplorerAction(action, profile) {
    if !IsObject(profile) || profile.Id != "explorer"
        return false
    if action = "explorer_new" {
        MF_SendTap("^+n")
        return true
    }
    return false
}
