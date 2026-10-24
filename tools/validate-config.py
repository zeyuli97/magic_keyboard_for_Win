#!/usr/bin/env python3
"""Validate config and report evidence-based gates without running keyboard code."""
import argparse
import json
import sys
from pathlib import Path

from macflow_config import ConfigError, assess_release, load_and_validate, load_coverage


def main(argv=None):
    # Redirected output uses the locale code page (cp1252 on the test host).
    # Escape what it cannot encode rather than crash with the INVALID exit code.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--gate", choices=("prototype", "v1"),
                        help="also fail unless the named gate's required results are all PASS"
                             " and every enabled mapping is exercised by a qualifying case")
    parser.add_argument("--json", action="store_true", help="print machine-readable gate results")
    args = parser.parse_args(argv)
    try:
        bundle = load_and_validate(args.root)
    except ConfigError as exc:
        print(f"Configuration INVALID: {exc}", file=sys.stderr)
        return 1
    try:
        coverage, coverage_error = load_coverage(args.root, bundle), ""
    except ConfigError as exc:
        coverage, coverage_error = None, str(exc)
    gates = assess_release(bundle, coverage)
    if coverage_error:
        # The runtime configuration is still valid; only gate evidence is missing.
        for gate in gates.values():
            gate["accepted"] = False
            gate["blocking"].append({"id": "COVERAGE", "status": "UNAVAILABLE", "reason": coverage_error})
    report = {"configuration": "VALID", "delivery_status": bundle["release"]["delivery_status"], "gates": gates}
    if args.json:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        print("Configuration VALID (static check only)")
        print("Delivery: " + bundle["release"]["delivery_status"])
        for name, gate in gates.items():
            print(f"{name}: {'required results PASS' if gate['accepted'] else 'NOT ACCEPTED'}")
            for case in gate["blocking"]:
                print(f"  {case['id']}: {case['status']} — {case['reason']}")
        print("This command does not run AHK or verify hardware evidence.")
    return 2 if args.gate and not gates[args.gate]["accepted"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
