import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "release_tag.py"


class PublicReleaseTagTest(unittest.TestCase):
    def run_tag_reader(self, version):
        with tempfile.TemporaryDirectory() as temp:
            metadata = Path(temp) / "preprint-metadata.json"
            metadata.write_text(json.dumps({"version": version}), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(SCRIPT), str(metadata)],
                capture_output=True, text=True, check=False,
            )

    def test_stable_semver_tags_are_emitted(self):
        for version in ("v1.0.0", "v2.0.0", "v2.0.1", "v10.12.3"):
            with self.subTest(version=version):
                result = self.run_tag_reader(version)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), f"tag={version}")

    def test_shorthand_and_draft_versions_are_rejected(self):
        for version in ("v0", "v1", "v2", "v1.1", "v2.0", "v2.0.0-rc.1", "1.0.0", ""):
            with self.subTest(version=version):
                result = self.run_tag_reader(version)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("vMAJOR.MINOR.PATCH", result.stderr)

    def test_missing_or_non_string_version_is_rejected(self):
        for value in (None, 2):
            with self.subTest(value=value):
                result = self.run_tag_reader(value)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("vMAJOR.MINOR.PATCH", result.stderr)


if __name__ == "__main__":
    unittest.main()
