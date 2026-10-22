#!/usr/bin/env python3
"""Assemble source-only Windows preview without downloading or running anything."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    subprocess.run([sys.executable, str(ROOT / "tools/generate-config.py"), "--check"], check=True)
    destination = ROOT / "dist"
    destination.mkdir(exist_ok=True)
    archive = destination / "MacFlow-development-preview.zip"
    files = [ROOT / name for name in ("README.md", "AGENTS.md", "PLAN.md")]
    for directory in ("src", "build/generated", "config", "integrations", "docs", "tools", "tests"):
        files.extend(p for p in (ROOT / directory).rglob("*") if p.is_file() and not p.is_symlink()
                     and not any(part.startswith(".") for part in p.relative_to(ROOT).parts)
                     and "__pycache__" not in p.parts and "local" not in p.parts and p.suffix != ".pyc")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for path in sorted(set(files)):
            info = zipfile.ZipInfo("MacFlow/" + path.relative_to(ROOT).as_posix(), (2026, 10, 22, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, path.read_bytes())
    manifest = {
        "archive": archive.name, "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "delivery_status": "DEVELOPMENT PREVIEW", "hardware_validation": "NOT TESTED",
        "autohotkey_runtime_bundled": False,
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(archive)
    return 0


if __name__ == "__main__":
    sys.exit(main())
