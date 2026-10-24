"""Exercise release inventory and reproducibility with a real temporary Git index."""
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("package_preview", ROOT / "tools/package-preview.py")
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="macflow-package-tests-")
        self.root = Path(self.temp.name)
        for name in packager.release_paths(ROOT):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        self.git("init", "-q")
        self.git("add", ".")

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def test_untracked_private_file_is_never_packaged(self):
        original = packager.build_package(self.root)
        (self.root / "src/private-notes.txt").write_text("private test sentinel")
        self.assertEqual(original, packager.build_package(self.root))
        with zipfile.ZipFile(io.BytesIO(original[0])) as archive:
            self.assertNotIn("MacFlow/src/private-notes.txt", archive.namelist())

    def test_indexed_symlink_is_rejected(self):
        # Index mode is sufficient, even on Windows without symlink privilege.
        blob = self.git("hash-object", "-w", "README.md").stdout.decode("ascii").strip()
        self.git("update-index", "--add", "--cacheinfo", "120000," + blob + ",src/link.txt")
        with self.assertRaises(packager.PackageError):
            packager.build_package(self.root)

    def test_missing_git_inventory_fails_without_directory_fallback(self):
        # Keep both paths in this test's temporary root. Renaming also works
        # with Git's read-only object files on Windows; tearDown cleans them.
        (self.root / ".git").rename(self.root / ".git-unavailable")
        with self.assertRaises(packager.PackageError):
            packager.build_package(self.root)

    def test_deterministic_stored_archive_and_manifest(self):
        first = packager.build_package(self.root)
        self.assertEqual(first, packager.build_package(self.root))
        self.assertEqual("NOT TESTED", json.loads(first[1])["hardware_validation"])
        with zipfile.ZipFile(io.BytesIO(first[0])) as archive:
            for entry in archive.infolist():
                self.assertEqual(zipfile.ZIP_STORED, entry.compress_type)
                self.assertEqual((2026, 10, 22, 0, 0, 0), entry.date_time)
                self.assertEqual(0o100644, entry.external_attr >> 16)

    def test_check_rejects_stale_manifest_without_writing(self):
        target = packager.package(self.root)
        target.unlink()
        packager.package(self.root, check=True)
        self.assertFalse(target.exists())
        manifest = self.root / "dist/manifest.json"
        manifest.write_bytes(manifest.read_bytes() + b" ")
        before = manifest.read_bytes()
        with self.assertRaises(packager.PackageError):
            packager.package(self.root, check=True)
        self.assertEqual(before, manifest.read_bytes())
        self.assertFalse(target.exists())

    def test_tracked_content_change_invalidates_manifest(self):
        packager.package(self.root)
        readme = self.root / "README.md"
        readme.write_bytes(readme.read_bytes() + b"\nchanged\n")
        self.git("add", "README.md")
        with self.assertRaisesRegex(packager.PackageError, "manifest is missing/stale"):
            packager.package(self.root, check=True)

    def test_unstaged_release_edit_is_refused_without_writing(self):
        readme = self.root / "README.md"
        readme.write_bytes(readme.read_bytes() + b"\nunstaged sentinel\n")
        with self.assertRaisesRegex(packager.PackageError, "Unstaged change in release file: README.md"):
            packager.package(self.root)
        self.assertFalse((self.root / "dist").exists())

    def test_archive_contains_staged_index_content(self):
        readme = self.root / "README.md"
        readme.write_bytes(readme.read_bytes() + b"\nstaged sentinel\n")
        self.git("add", "README.md")
        staged = self.git("show", ":README.md").stdout
        archive, _ = packager.build_package(self.root)
        with zipfile.ZipFile(io.BytesIO(archive)) as output:
            self.assertEqual(staged, output.read("MacFlow/README.md"))
        self.assertIn(b"staged sentinel", staged)


if __name__ == "__main__":
    unittest.main()
