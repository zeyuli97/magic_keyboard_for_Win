#!/usr/bin/env python3
"""Package Git-indexed preview files; --check verifies the committed manifest."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOP_LEVEL = frozenset(("README.md", "AGENTS.md", "PLAN.md"))
DIRECTORIES = frozenset(("src", "config", "integrations", "docs", "tools", "tests"))
REQUIRED = TOP_LEVEL | frozenset((
    "src/ahk/main.ahk", "config/schema.json", "config/mappings.yaml",
    "config/apps.yaml", "config/release.yaml", "build/generated/macflow.ini",
    "build/generated/macflow.ini.sha256", "build/generated/manifest.json",
    "tools/smoke-tests.ps1", "tests/manual-checklist.md",
))


class PackageError(ValueError):
    pass


def release_paths(root):
    """Read the index, never a directory walk or a network resource."""
    root = Path(root).resolve()
    try:
        top = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"], stderr=subprocess.PIPE
        ).decode("utf-8").strip()
        if Path(top).resolve() != root:
            raise PackageError("Run packaging against the repository root.")
        inventory = subprocess.check_output(
            ["git", "-C", str(root), "ls-files", "--stage", "-z"], stderr=subprocess.PIPE
        )
    except (OSError, subprocess.CalledProcessError, UnicodeError) as exc:
        raise PackageError("A readable Git index is required; directory scanning is forbidden.") from exc
    selected = []
    for record in inventory.split(b"\0"):
        if not record:
            continue
        try:
            metadata, raw_name = record.split(b"\t", 1)
            mode, _, stage = metadata.decode("ascii").split()
            name = raw_name.decode("utf-8")
        except (ValueError, UnicodeError) as exc:
            raise PackageError("Invalid Git inventory entry.") from exc
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name:
            raise PackageError("Unsafe tracked path: " + name)
        if not (name in TOP_LEVEL or path.parts[0] in DIRECTORIES or path.parts[:2] == ("build", "generated")):
            continue
        if any(part.startswith(".") or part in ("__pycache__", "local") for part in path.parts) or path.suffix == ".pyc":
            continue
        if stage != "0" or mode not in ("100644", "100755"):
            raise PackageError("Unmerged or non-regular tracked release file: " + name)
        target = root / path
        for length in range(1, len(path.parts) + 1):
            if root.joinpath(*path.parts[:length]).is_symlink():
                raise PackageError("Symlink in release path: " + name)
        if not target.exists() or not stat.S_ISREG(target.stat().st_mode):
            raise PackageError("Tracked release file is missing/not regular: " + name)
        selected.append(name)
    missing = REQUIRED - set(selected)
    if missing:
        raise PackageError("Required release files are not indexed: " + ", ".join(sorted(missing)))
    return sorted(selected)


def build_package(root):
    root = Path(root)
    contents = {name: (root / name).read_bytes() for name in release_paths(root)}
    buffer = io.BytesIO()
    # Stored data avoids platform/zlib-version-dependent compression output.
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as output:
        for name, data in contents.items():
            info = zipfile.ZipInfo("MacFlow/" + name, (2026, 10, 22, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_STORED
            output.writestr(info, data)
    archive = buffer.getvalue()
    manifest = {
        "format_version": 1, "archive": "MacFlow-development-preview.zip",
        "sha256": hashlib.sha256(archive).hexdigest(), "storage": "ZIP_STORED",
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in contents.items()},
        "delivery_status": "DEVELOPMENT PREVIEW", "hardware_validation": "NOT TESTED",
        "autohotkey_runtime_bundled": False,
    }
    return archive, (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")


def package(root, check=False):
    root = Path(root).resolve()
    result = subprocess.run([sys.executable, "-B", str(root / "tools/generate-config.py"), "--check"],
                            capture_output=True, text=True)
    if result.returncode:
        raise PackageError("Generated configuration check failed: " + result.stderr.strip())
    archive, manifest = build_package(root)
    destination = root / "dist"
    target = destination / "MacFlow-development-preview.zip"
    manifest_path = destination / "manifest.json"
    if check:
        if not manifest_path.is_file() or manifest_path.read_bytes() != manifest:
            raise PackageError("Release manifest is missing/stale. Stage intended files, rebuild, then commit dist/manifest.json.")
    else:
        destination.mkdir(exist_ok=True)
        target.write_bytes(archive)
        manifest_path.write_bytes(manifest)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true", help="Rebuild in memory and compare manifest; write nothing")
    args = parser.parse_args()
    try:
        target = package(args.root, args.check)
    except (PackageError, OSError) as exc:
        print("Package error: " + str(exc), file=sys.stderr)
        return 1
    print(("Verified reproducible manifest for " if args.check else "Built ") + str(target))
    return 0


if __name__ == "__main__":
    sys.exit(main())
