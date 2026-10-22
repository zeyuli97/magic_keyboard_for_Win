; Mouse tray remains the primary recovery path, including when input hooks fail.
MF_RegisterEmergency() {
    HotIf(MF_EmergencyAvailable)
    try Hotkey("$~^!F12", MF_Disable, "On I1")
    finally HotIf()
}

MF_EmergencyAvailable(*) {
    global MF
    ; Native mode does not consume this key. Tilde also preserves native delivery
    ; while enabled. The emergency action can disable, never enable, mappings.
    return MF.Enabled
}
