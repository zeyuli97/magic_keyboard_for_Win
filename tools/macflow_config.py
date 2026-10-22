"""Strict, standard-library-only configuration validation for MacFlow.

The .yaml files deliberately contain JSON only. Validation never enables the
runtime, changes release evidence, contacts a service, or reads keyboard input.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


class ConfigError(ValueError):
    """A configuration cannot safely be consumed."""


CONTEXTS = frozenset(("edit", "text", "browser", "explorer", "vscode", "terminal"))
ACTIONS = frozenset((
    "copy", "paste", "cut", "select_all", "undo", "redo", "save", "find",
    "word_left", "word_right", "select_word_left", "select_word_right",
    "delete_word", "line_start", "line_end", "document_start", "document_end",
    "app_next", "app_previous", "browser_address", "browser_new",
    "browser_close", "browser_reload", "browser_restore", "browser_back",
    "browser_forward", "explorer_new", "explorer_delete", "terminal_copy",
    "terminal_paste",
))
PROFILE_CONTRACTS = {
    "chrome": ("chrome.exe", {"edit", "text", "browser"}),
    "notepad": ("notepad.exe", {"edit", "text"}),
    "vscode": ("code.exe", {"vscode"}),
    "explorer": ("explorer.exe", {"explorer"}),
    "windows_terminal": ("windowsterminal.exe", {"terminal"}),
}
PROFILE_IDS = frozenset(PROFILE_CONTRACTS)
CHORD = re.compile(r"(?:LWin|LAlt)(?:\+Shift)?\+(?:[a-z]|\[|\]|Left|Right|Up|Down|Backspace|Tab)\Z")
IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_.-]*\Z")
PROCESS = re.compile(r"[a-z0-9][a-z0-9_.-]*\.exe\Z")
CASE_PRIORITIES = {
    "T01": "P0", "T01b": "P1", "T02": "P0", "T03": "P0",
    "T04": "P0", "T05": "P0", "T06": "P0", "T06b": "P0",
    "T07": "P0", "T07b": "P0", "T07c": "CONDITIONAL",
    "T07d": "P0", "T08": "P0", "T09": "P1",
}
STATUSES = frozenset(("NOT TESTED", "BLOCKED", "PASS", "FAIL"))
SCHEMA_KEYWORDS = frozenset((
    "$schema", "$id", "title", "description", "type", "properties", "required",
    "additionalProperties", "items", "enum", "const", "pattern", "minimum",
    "maximum", "minItems", "maxItems", "uniqueItems", "minLength", "maxLength",
))


def _fail(path, message):
    raise ConfigError(f"{path}: {message}")


def _object(value, keys, path):
    if not isinstance(value, dict):
        _fail(path, "must be an object")
    missing, extra = set(keys) - value.keys(), value.keys() - set(keys)
    if missing:
        _fail(path, "missing fields: " + ", ".join(sorted(missing)))
    if extra:
        _fail(path, "unknown fields: " + ", ".join(sorted(extra)))


def _bool(value, path):
    if type(value) is not bool:
        _fail(path, "must be a boolean")


def _str(value, path, *, nonempty=True):
    if not isinstance(value, str) or (nonempty and not value.strip()):
        _fail(path, "must be a nonempty string" if nonempty else "must be a string")
    if any(ord(char) < 32 for char in value):
        _fail(path, "must be a single line without control characters")
    return value


def _list(value, path, *, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value):
        _fail(path, "must be a nonempty array" if nonempty else "must be an array")
    return value


def _strings(value, path, *, nonempty=False, allowed=None, pattern=None):
    values = _list(value, path, nonempty=nonempty)
    seen = set()
    for index, item in enumerate(values):
        item_path = f"{path}[{index}]"
        _str(item, item_path)
        if item in seen:
            _fail(item_path, "duplicate value")
        if allowed is not None and item not in allowed:
            _fail(item_path, "unsupported value")
        if pattern is not None and not pattern.fullmatch(item):
            _fail(item_path, "invalid syntax")
        seen.add(item)
    return values


def _version(data, path):
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        _fail(path + ".schema_version", "must be integer 1")


def _unique_id(item, seen, path):
    _str(item["id"], path + ".id")
    if not IDENTIFIER.fullmatch(item["id"]):
        _fail(path + ".id", "invalid identifier")
    if item["id"] in seen:
        _fail(path + ".id", "duplicate identifier")
    seen.add(item["id"])


def validate_bundle(bundle):
    """Validate the frozen contract and return the same, unmodified bundle."""
    _object(bundle, ("mappings", "apps", "release"), "bundle")
    mappings, apps, release = (bundle[name] for name in ("mappings", "apps", "release"))
    _object(mappings, ("schema_version", "mappings"), "mappings")
    _object(apps, ("schema_version", "allowed_hkls", "bypass_processes", "profiles"), "apps")
    _object(release, ("schema_version", "delivery_status", "mode", "baseline", "cases"), "release")
    for name, value in (("mappings", mappings), ("apps", apps), ("release", release)):
        _version(value, name)

    rules = _list(mappings["mappings"], "mappings.mappings", nonempty=True)
    ids, chord_contexts = set(), set()
    for index, rule in enumerate(rules):
        path = f"mappings.mappings[{index}]"
        _object(rule, ("id", "enabled", "physical_chord", "contexts", "action",
                       "priority", "on_unmatched", "blocked_reason"), path)
        _unique_id(rule, ids, path)
        _bool(rule["enabled"], path + ".enabled")
        _str(rule["physical_chord"], path + ".physical_chord")
        if not CHORD.fullmatch(rule["physical_chord"]):
            _fail(path + ".physical_chord", "only exact left Command/Option chords are allowed")
        contexts = _strings(rule["contexts"], path + ".contexts", nonempty=True, allowed=CONTEXTS)
        if not isinstance(rule["action"], str) or rule["action"] not in ACTIONS:
            _fail(path + ".action", "unknown action")
        if type(rule["priority"]) is not int or not 0 <= rule["priority"] <= 1000:
            _fail(path + ".priority", "must be an integer from 0 to 1000")
        if rule["on_unmatched"] != "passthrough":
            _fail(path + ".on_unmatched", "must be passthrough")
        _str(rule["blocked_reason"], path + ".blocked_reason", nonempty=False)
        if rule["enabled"] and rule["physical_chord"] in ("LWin+l", "LWin+Backspace"):
            _fail(path, "reserved or unsafe chords cannot be enabled under another action")
        if rule["enabled"] and rule["blocked_reason"].strip():
            _fail(path, "blocked rules must be disabled")
        if rule["enabled"] and rule["action"] in ("browser_address", "explorer_delete", "terminal_copy", "terminal_paste"):
            _fail(path, "this action is blocked in the initial backend")
        if "terminal" in contexts and rule["action"] not in ("terminal_copy", "terminal_paste"):
            _fail(path, "terminal context cannot fall back to generic actions")
        if rule["action"].startswith("terminal_") and set(contexts) != {"terminal"}:
            _fail(path, "terminal actions require only terminal context")
        for context in contexts:
            key = (rule["physical_chord"], context, rule["priority"])
            if key in chord_contexts:
                _fail(path, "ambiguous chord/context/priority")
            chord_contexts.add(key)

    layouts = _strings(apps["allowed_hkls"], "apps.allowed_hkls", nonempty=True)
    if layouts != ["04090409"]:
        _fail("apps.allowed_hkls", "initial backend permits only exact HKL 04090409")
    bypass = set(_strings(apps["bypass_processes"], "apps.bypass_processes", pattern=PROCESS))
    profiles = _list(apps["profiles"], "apps.profiles", nonempty=True)
    ids, active_processes = set(), set()
    for index, profile in enumerate(profiles):
        path = f"apps.profiles[{index}]"
        _object(profile, ("id", "processes", "contexts", "enabled", "requires_integration"), path)
        _unique_id(profile, ids, path)
        if profile["id"] not in PROFILE_IDS:
            _fail(path + ".id", "unknown profile")
        processes = set(_strings(profile["processes"], path + ".processes", nonempty=True, pattern=PROCESS))
        contexts = set(_strings(profile["contexts"], path + ".contexts", nonempty=True, allowed=CONTEXTS))
        expected_process, expected_contexts = PROFILE_CONTRACTS[profile["id"]]
        if processes != {expected_process} or not contexts.issubset(expected_contexts):
            _fail(path, "profile process/context does not match its fixed safety boundary")
        _bool(profile["enabled"], path + ".enabled")
        _bool(profile["requires_integration"], path + ".requires_integration")
        if profile["id"] == "windows_terminal" and profile["enabled"]:
            _fail(path, "Windows Terminal profile must remain disabled")
        if profile["requires_integration"] != (profile["id"] == "vscode"):
            _fail(path, "only VS Code must require the guarded native integration")
        if processes & active_processes:
            _fail(path, "profile processes overlap")
        active_processes.update(processes)
        if profile["enabled"]:
            if processes & bypass:
                _fail(path, "enabled profile overlaps bypass_processes")
        matches = {}
        for rule in rules:
            if rule["enabled"] and contexts.intersection(rule["contexts"]):
                key = (rule["physical_chord"], rule["priority"])
                if key in matches:
                    _fail(path, f"rules {matches[key]} and {rule['id']} overlap at equal priority")
                matches[key] = rule["id"]

    if release["delivery_status"] != "DEVELOPMENT PREVIEW":
        _fail("release.delivery_status", "this implementation supports DEVELOPMENT PREVIEW only")
    if release["mode"] != "ahk-only":
        _fail("release.mode", "initial backend must be ahk-only")
    _strings(release["baseline"], "release.baseline", nonempty=True)
    cases = _list(release["cases"], "release.cases", nonempty=True)
    case_ids = set()
    for index, case in enumerate(cases):
        path = f"release.cases[{index}]"
        _object(case, ("id", "priority", "required_prototype", "required_v1", "status", "reason"), path)
        _unique_id(case, case_ids, path)
        expected = CASE_PRIORITIES.get(case["id"])
        if expected is None or case["priority"] != expected:
            _fail(path, "unknown case or incorrect priority")
        for field in ("required_prototype", "required_v1"):
            _bool(case[field], path + "." + field)
        if case["required_prototype"] != (expected == "P0"):
            _fail(path, "prototype must require every P0 and only P0")
        if case["required_v1"] != (expected in ("P0", "P1")):
            _fail(path, "v1 must require every P0/P1; T07c is not applicable to ahk-only")
        if not isinstance(case["status"], str) or case["status"] not in STATUSES:
            _fail(path + ".status", "unknown result status")
        _str(case["reason"], path + ".reason", nonempty=False)
        if case["status"] in ("BLOCKED", "FAIL") and not case["reason"].strip():
            _fail(path + ".reason", "BLOCKED/FAIL requires a reason")
    if case_ids != set(CASE_PRIORITIES):
        _fail("release.cases", "missing required inventory: " + ", ".join(sorted(set(CASE_PRIORITIES) - case_ids)))
    return bundle


def assess_release(bundle):
    """Report gate results from supplied evidence; never upgrade delivery status.

    PASS strings are claims supplied by the operator, not authenticated hardware
    evidence. This function cannot establish that a manual test really occurred.
    """
    validate_bundle(bundle)
    result = {}
    for name, field in (("prototype", "required_prototype"), ("v1", "required_v1")):
        required = [case for case in bundle["release"]["cases"] if case[field]]
        blocking = [
            {"id": case["id"], "status": case["status"], "reason": case["reason"]}
            for case in required if case["status"] != "PASS"
        ]
        result[name] = {"accepted": bool(required) and not blocking, "blocking": blocking}
    return result


def _validate_schema(value, schema, path):
    """Validate the intentionally small schema vocabulary used by this repo."""
    if not isinstance(schema, dict):
        _fail(path, "schema must be an object")
    unknown = set(schema) - SCHEMA_KEYWORDS
    if unknown:
        _fail(path, "unsupported schema keyword: " + ", ".join(sorted(unknown)))
    kind = schema.get("type")
    checks = {
        "object": lambda x: isinstance(x, dict),
        "array": lambda x: isinstance(x, list),
        "string": lambda x: isinstance(x, str),
        "integer": lambda x: type(x) is int,
        "number": lambda x: type(x) in (int, float),
        "boolean": lambda x: type(x) is bool,
        "null": lambda x: x is None,
    }
    if kind is not None and (kind not in checks or not checks[kind](value)):
        _fail(path, "does not match schema type")
    if "enum" in schema and not any(type(value) is type(item) and value == item for item in schema["enum"]):
        _fail(path, "not in schema enum")
    if "const" in schema and not (type(value) is type(schema["const"]) and value == schema["const"]):
        _fail(path, "does not match schema const")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        missing = set(schema.get("required", ())) - value.keys()
        if missing:
            _fail(path, "missing schema fields: " + ", ".join(sorted(missing)))
        for key, child in value.items():
            if key in properties:
                _validate_schema(child, properties[key], path + "." + key)
            elif schema.get("additionalProperties", True) is False:
                _fail(path + "." + key, "unknown schema field")
            elif isinstance(schema.get("additionalProperties"), dict):
                _validate_schema(child, schema["additionalProperties"], path + "." + key)
    if isinstance(value, list):
        for constraint, operation in (("minItems", lambda x, y: x < y), ("maxItems", lambda x, y: x > y)):
            if constraint in schema and operation(len(value), schema[constraint]):
                _fail(path, "violates schema " + constraint)
        if schema.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in value}) != len(value):
            _fail(path, "duplicate schema array item")
        if "items" in schema:
            for index, child in enumerate(value):
                _validate_schema(child, schema["items"], f"{path}[{index}]")
    if isinstance(value, str):
        if "pattern" in schema:
            try:
                matches = re.search(schema["pattern"], value)
            except re.error as exc:
                raise ConfigError(path + ": invalid schema pattern") from exc
            if not matches:
                _fail(path, "does not match schema pattern")
        for constraint, operation in (("minLength", lambda x, y: x < y), ("maxLength", lambda x, y: x > y)):
            if constraint in schema and operation(len(value), schema[constraint]):
                _fail(path, "violates schema " + constraint)
    if type(value) in (int, float):
        if "minimum" in schema and value < schema["minimum"]:
            _fail(path, "below schema minimum")
        if "maximum" in schema and value > schema["maximum"]:
            _fail(path, "above schema maximum")


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ConfigError("JSON contains duplicate object keys")
        result[key] = value
    return result


def _constant(_value):
    raise ConfigError("JSON nonfinite numbers are not permitted")


def _read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=_pairs, parse_constant=_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConfigError(f"{path.name}: cannot read strict JSON ({type(exc).__name__})") from exc


def load_and_validate(root: Path):
    root = Path(root)
    schemas = _read_json(root / "config" / "schema.json")
    _object(schemas, ("mappings", "apps", "release"), "schema")
    bundle = {}
    for name in ("mappings", "apps", "release"):
        value = _read_json(root / "config" / (name + ".yaml"))
        try:
            _validate_schema(value, schemas[name], name)
        except ConfigError:
            raise
        except (TypeError, KeyError, ValueError) as exc:
            raise ConfigError(name + ": malformed schema") from exc
        bundle[name] = value
    return validate_bundle(bundle)
