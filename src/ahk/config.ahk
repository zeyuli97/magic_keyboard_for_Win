; Generated configuration is data, never evaluated as AHK source.
MF_LoadConfig(root) {
    path := root "\build\generated\macflow.ini"
    expected := Trim(FileRead(path ".sha256", "UTF-8"))
    if !RegExMatch(expected, "^[a-f0-9]{64}$") || MF_SHA256(path) != expected
        throw Error("Generated configuration checksum mismatch. Regenerate on the development machine.")
    if MF_Ini(path, "meta", "schema_version") != "1"
        throw Error("Unsupported configuration schema.")
    if MF_Ini(path, "meta", "mode") != "ahk-only"
        throw Error("This preview supports only the single-process AHK backend.")
    if MF_Ini(path, "meta", "delivery_status") != "DEVELOPMENT PREVIEW"
        throw Error("Unexpected release status.")
    config := {SchemaVersion: 1, Hash: MF_Ini(path, "meta", "source_hash"),
        Rules: [], Profiles: [], BypassProcesses: [], AllowedLayouts: []}
    if !RegExMatch(config.Hash, "^[a-f0-9]{64}$")
        throw Error("Invalid source hash.")
    config.AllowedLayouts := MF_IniList(path, "meta", "allowed_hkls")
    for layout in config.AllowedLayouts
        if layout != "04090409"
            throw Error("Only the US English layout is enabled in this preview.")
    config.BypassProcesses := MF_IniList(path, "meta", "bypass_processes")
    for process in config.BypassProcesses
        if !RegExMatch(process, "^[a-z0-9_.-]+\.exe$")
            throw Error("Invalid bypass process.")
    ruleCount := MF_IniInteger(path, "meta", "rule_count", 1, 256)
    profileCount := MF_IniInteger(path, "meta", "profile_count", 1, 16)
    actions := StrSplit("copy|paste|cut|select_all|undo|redo|save|find|word_left|word_right|select_word_left|select_word_right|delete_word|line_start|line_end|document_start|document_end|app_next|app_previous|browser_address|browser_new|browser_close|browser_reload|browser_restore|browser_back|browser_forward|explorer_new|explorer_delete|terminal_copy|terminal_paste", "|")
    ids := Map()
    Loop ruleCount {
        section := "rule." A_Index
        rule := {Id: MF_Ini(path, section, "id"), Enabled: MF_IniBool(path, section, "enabled"),
            Chord: MF_Ini(path, section, "physical_chord"), Contexts: MF_IniList(path, section, "contexts"),
            Action: MF_Ini(path, section, "action"), Priority: MF_IniInteger(path, section, "priority", 0, 1000),
            BlockedReason: MF_Ini(path, section, "blocked_reason")}
        if !RegExMatch(rule.Id, "^[a-z][a-z0-9_.-]*$") || ids.Has(rule.Id)
            throw Error("Invalid/duplicate mapping ID.")
        ids[rule.Id] := true
        if !RegExMatch(rule.Chord, "^(LWin|LAlt)(\+Shift)?\+([a-z]|Left|Right|Up|Down|Backspace|Tab|\[|\])$")
            throw Error("Invalid physical chord: " rule.Id)
        if !MF_Contains(actions, rule.Action)
            throw Error("Unknown action: " rule.Id)
        MF_ValidateContexts(rule.Contexts)
        if rule.Enabled && (rule.BlockedReason != "" || MF_Contains(["browser_address", "explorer_delete", "terminal_copy", "terminal_paste"], rule.Action))
            throw Error("Blocked mapping must remain disabled: " rule.Id)
        ; Never register the protected chord under another action name.
        if rule.Enabled && (rule.Chord = "LWin+l" || rule.Chord = "LWin+Backspace")
            throw Error("Protected/deletion chord is unavailable in this backend.")
        config.Rules.Push(rule)
    }
    processes := Map()
    profileIds := Map()
    Loop profileCount {
        section := "profile." A_Index
        profile := {Id: MF_Ini(path, section, "id"), Processes: MF_IniList(path, section, "processes"),
            Contexts: MF_IniList(path, section, "contexts"), Enabled: MF_IniBool(path, section, "enabled"),
            RequiresIntegration: MF_IniBool(path, section, "requires_integration")}
        if !MF_Contains(["chrome", "notepad", "vscode", "explorer", "windows_terminal"], profile.Id) || profileIds.Has(profile.Id)
            throw Error("Invalid/duplicate profile.")
        profileIds[profile.Id] := true
        MF_ValidateContexts(profile.Contexts)
        if profile.Id = "windows_terminal" && profile.Enabled
            throw Error("Windows Terminal must bypass in this preview.")
        if profile.Id = "vscode" && !profile.RequiresIntegration
            throw Error("VS Code requires its native binding bridge.")
        if profile.Id != "vscode" && profile.RequiresIntegration
            throw Error("Unexpected integration requirement.")
        for process in profile.Processes {
            if !RegExMatch(process, "^[a-z0-9_.-]+\.exe$") || processes.Has(process)
                throw Error("Invalid/overlapping process profile.")
            processes[process] := true
        }
        config.Profiles.Push(profile)
    }
    for profile in config.Profiles {
        matching := Map()
        for rule in config.Rules {
            if !rule.Enabled || !MF_Intersects(rule.Contexts, profile.Contexts)
                continue
            key := rule.Chord "|" rule.Priority
            if matching.Has(key)
                throw Error("Ambiguous mapping for " profile.Id ": " rule.Chord)
            matching[key] := true
        }
    }
    return config
}

MF_Ini(path, section, key) {
    value := IniRead(path, section, key, "__MACFLOW_MISSING__")
    if value = "__MACFLOW_MISSING__"
        throw Error("Missing configuration field: " section "." key)
    return value
}

MF_IniList(path, section, key) {
    value := MF_Ini(path, section, key)
    if value = ""
        throw Error("Empty configuration list: " key)
    result := StrSplit(value, "|")
    seen := Map()
    for entry in result {
        if entry = "" || seen.Has(entry)
            throw Error("Empty/duplicate list entry: " key)
        seen[entry] := true
    }
    return result
}

MF_IniInteger(path, section, key, minimum, maximum) {
    value := MF_Ini(path, section, key)
    if !RegExMatch(value, "^\d+$") || Integer(value) < minimum || Integer(value) > maximum
        throw Error("Invalid integer: " key)
    return Integer(value)
}

MF_IniBool(path, section, key) {
    return MF_IniInteger(path, section, key, 0, 1) = 1
}

MF_ValidateContexts(contexts) {
    for context in contexts
        if !MF_Contains(["edit", "text", "browser", "explorer", "vscode", "terminal"], context)
            throw Error("Unknown application context.")
}

MF_Contains(values, needle) {
    for value in values
        if value = needle
            return true
    return false
}

MF_Intersects(left, right) {
    for value in left
        if MF_Contains(right, value)
            return true
    return false
}

MF_SHA256(path) {
    data := FileRead(path, "RAW")
    provider := 0, hash := 0
    try {
        if !DllCall("Advapi32\CryptAcquireContextW", "Ptr*", &provider, "Ptr", 0, "Ptr", 0, "UInt", 24, "UInt", 0xF0000000)
            throw Error("Cannot initialize configuration checksum.")
        if !DllCall("Advapi32\CryptCreateHash", "Ptr", provider, "UInt", 0x800C, "Ptr", 0, "UInt", 0, "Ptr*", &hash)
            throw Error("Cannot initialize SHA256.")
        if !DllCall("Advapi32\CryptHashData", "Ptr", hash, "Ptr", data, "UInt", data.Size, "UInt", 0)
            throw Error("Cannot hash configuration.")
        output := Buffer(32), size := 32
        if !DllCall("Advapi32\CryptGetHashParam", "Ptr", hash, "UInt", 2, "Ptr", output, "UInt*", &size, "UInt", 0)
            throw Error("Cannot read configuration checksum.")
        result := ""
        Loop 32
            result .= Format("{:02x}", NumGet(output, A_Index - 1, "UChar"))
        return result
    } finally {
        if hash
            DllCall("Advapi32\CryptDestroyHash", "Ptr", hash)
        if provider
            DllCall("Advapi32\CryptReleaseContext", "Ptr", provider, "UInt", 0)
    }
}
