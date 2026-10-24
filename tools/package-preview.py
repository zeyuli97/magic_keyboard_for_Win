#!/usr/bin/env python3
"""Package Git-index content of preview files; --check verifies the committed manifest."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOP_LEVEL = frozenset(("README.md", "AGENTS.md", "PLAN.md"))
# Explicit files outside the release directories. The shipped test suite checks
# this CI wiring, so the archive carries it and the suite runs from the archive.
EXTRA_FILES = frozenset((".github/workflows/static-checks.yml",))
DIRECTORIES = frozenset(("src", "config", "integrations", "docs", "tools", "tests"))
REQUIRED = TOP_LEVEL | EXTRA_FILES | frozenset((
    "src/ahk/main.ahk", "config/schema.json", "config/mappings.yaml",
    "config/apps.yaml", "config/release.yaml", "build/generated/macflow.ini",
    "build/generated/macflow.ini.sha256", "build/generated/manifest.json",
    "tools/smoke-tests.ps1", "tests/manual-checklist.md",
))
OBJECT_ID = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")


class PackageError(ValueError):
    pass


def is_release_path(name):
    """Whether a repository-relative POSIX path belongs in the preview archive."""
    path = PurePosixPath(name)
    if name in TOP_LEVEL or name in EXTRA_FILES:
        return True
    if not (path.parts[0] in DIRECTORIES or path.parts[:2] == ("build", "generated")):
        return False
    return not (any(part.startswith(".") or part in ("__pycache__", "local") for part in path.parts)
                or path.suffix == ".pyc")


def _release_entries(root):
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
            mode, object_id, stage = metadata.decode("ascii").split()
            name = raw_name.decode("utf-8")
        except (ValueError, UnicodeError) as exc:
            raise PackageError("Invalid Git inventory entry.") from exc
        if not OBJECT_ID.fullmatch(object_id):
            raise PackageError("Invalid Git object ID for: " + name)
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name:
            raise PackageError("Unsafe tracked path: " + name)
        if not is_release_path(name):
            continue
        if stage != "0" or mode not in ("100644", "100755"):
            raise PackageError("Unmerged or non-regular tracked release file: " + name)
        target = root / path
        for length in range(1, len(path.parts) + 1):
            if root.joinpath(*path.parts[:length]).is_symlink():
                raise PackageError("Symlink in release path: " + name)
        if not target.exists() or not stat.S_ISREG(target.stat().st_mode):
            raise PackageError("Tracked release file is missing/not regular: " + name)
        selected.append((name, object_id))
    missing = REQUIRED - {name for name, _ in selected}
    if missing:
        raise PackageError("Required release files are not indexed: " + ", ".join(sorted(missing)))
    return sorted(selected)


def release_paths(root):
    return [name for name, _ in _release_entries(root)]


def _index_blobs(root, object_ids):
    request = b"".join(object_id.encode("ascii") + b"\n" for object_id in object_ids)
    try:
        output = subprocess.run(["git", "-C", str(root), "cat-file", "--batch"],
                                input=request, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise PackageError("Cannot read release file content from the Git index.") from exc
    blobs, offset = {}, 0
    for object_id in object_ids:
        end = output.find(b"\n", offset)
        header = output[offset:end].split() if end >= 0 else []
        if len(header) != 3 or header[0] != object_id.encode("ascii") or header[1] != b"blob" or not header[2].isdigit():
            raise PackageError("Invalid Git object for release content: " + object_id)
        start = end + 1
        stop = start + int(header[2])
        if output[stop:stop + 1] != b"\n":
            raise PackageError("Truncated Git object for release content: " + object_id)
        blobs[object_id] = output[start:stop]
        offset = stop + 1
    return blobs


def release_contents(root):
    """Return staged blob bytes, refusing working-tree edits the index lacks.

    Configuration checks read the working tree, so equality keeps the packaged
    bytes identical to the bytes those checks validated.
    """
    root = Path(root).resolve()
    entries = _release_entries(root)
    blobs = _index_blobs(root, sorted({object_id for _, object_id in entries}))
    contents = {}
    for name, object_id in entries:
        if (root / name).read_bytes() != blobs[object_id]:
            raise PackageError("Unstaged change in release file: " + name + ". Stage or revert it before packaging.")
        contents[name] = blobs[object_id]
    return contents


def build_package(root):
    contents = release_contents(root)
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
