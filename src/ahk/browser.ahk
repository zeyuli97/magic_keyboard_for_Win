; Chrome/Edge application shortcuts. Website shortcuts may override native ones.
MF_BrowserAction(action, profile) {
    if !IsObject(profile) || (profile.Id != "chrome" && profile.Id != "edge")
        return false
    ; Command+L is deliberately absent: physical LWin+L may lock Windows.
    if action = "browser_address"
        return false
    static keys := Map(
        "browser_new", "^t", "browser_close", "^w", "browser_reload", "^r",
        "browser_restore", "^+t", "browser_back", "!{Left}",
        "browser_forward", "!{Right}")
    if !keys.Has(action)
        return false
    MF_SendTap(keys[action])
    return true
}
