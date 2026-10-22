"""Artifact integration tests; import the Lead-owned generator when integrated."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from test_config import ROOT, fixture, make_root
from macflow_config import ConfigError

GENERATOR = ROOT / "tools" / "generate-config.py"
if GENERATOR.exists():
    spec = importlib.util.spec_from_file_location("macflow_generator_tested", GENERATOR)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
else:
    generator = None


@unittest.skipIf(generator is None, "Lead generator not integrated in this worktree")
class ArtifactGenerationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="macflow-generation-test-")
        self.root = make_root(Path(self.temp.name))

    def tearDown(self):
        self.temp.cleanup()

    def test_deterministic_artifacts_and_sha256_match(self):
        first = generator.build_outputs(self.root)
        self.assertEqual(first, generator.build_outputs(self.root))
        self.assertEqual({"macflow.ini", "macflow.ini.sha256", "manifest.json"}, set(first))
        ini = first["macflow.ini"]
        self.assertTrue(ini.startswith(b"\xff\xfe"))
        checksum = hashlib.sha256(ini).hexdigest()
        self.assertEqual(checksum, first["macflow.ini.sha256"].decode("ascii").strip())
        manifest = json.loads(first["manifest.json"])
        self.assertEqual(checksum, manifest["artifacts"]["macflow.ini"])
        self.assertEqual("NOT TESTED", manifest["hardware_validation"])
        self.assertEqual("DEVELOPMENT PREVIEW", manifest["delivery_status"])

    def test_unicode_disabled_reason_round_trips(self):
        bundle = fixture()
        bundle["mappings"]["mappings"][0].update(enabled=False, blocked_reason="中文说明：待实测")
        make_root(self.root, bundle)
        ini = generator.build_outputs(self.root)["macflow.ini"].decode("utf-16")
        self.assertIn("blocked_reason=中文说明：待实测", ini)

    def test_check_detects_missing_and_tampered_artifact_without_writing(self):
        with self.assertRaises(ConfigError):
            generator.generate(self.root, check=True)
        self.assertFalse((self.root / "build").exists())
        outputs = generator.generate(self.root)
        generator.generate(self.root, check=True)
        target = self.root / "build" / "generated" / "macflow.ini"
        target.write_bytes(outputs["macflow.ini"] + b"\x00\x00")
        before = {p.name: p.read_bytes() for p in target.parent.iterdir()}
        with self.assertRaises(ConfigError):
            generator.generate(self.root, check=True)
        self.assertEqual(before, {p.name: p.read_bytes() for p in target.parent.iterdir()})

    def test_source_change_makes_artifacts_stale(self):
        generator.generate(self.root)
        release = self.root / "config" / "release.yaml"
        release.write_text(release.read_text() + "\n")
        with self.assertRaises(ConfigError):
            generator.generate(self.root, check=True)

    def test_invalid_configuration_preserves_existing_artifacts(self):
        generator.generate(self.root)
        target = self.root / "build" / "generated"
        before = {p.name: p.read_bytes() for p in target.iterdir()}
        bundle = fixture()
        bundle["mappings"]["mappings"][0]["physical_chord"] = "RWin+c"
        make_root(self.root, bundle)
        with self.assertRaises(ConfigError):
            generator.generate(self.root)
        self.assertEqual(before, {p.name: p.read_bytes() for p in target.iterdir()})

    def test_invalid_configuration_writes_no_artifacts(self):
        bundle = fixture()
        bundle["mappings"]["mappings"][0]["physical_chord"] = "RWin+c"
        make_root(self.root, bundle)
        with self.assertRaises(ConfigError):
            generator.generate(self.root)
        self.assertFalse((self.root / "build").exists())


if __name__ == "__main__":
    unittest.main()
