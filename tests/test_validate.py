"""Basic tests for the metadata validator (Python standard library + PyYAML)."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE_ROOT = Path(__file__).resolve().parents[1]


class ValidatePreprintTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "scripts").mkdir()
        (self.root / "paper").mkdir()
        shutil.copy2(SOURCE_ROOT / "scripts" / "validate.py", self.root / "scripts" / "validate.py")
        shutil.copy2(SOURCE_ROOT / "preprint.yaml", self.root / "preprint.yaml")

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_validator(self, *args):
        return subprocess.run(
            [sys.executable, str(self.root / "scripts" / "validate.py"), *args],
            capture_output=True, text=True, check=False,
        )

    def test_draft_does_not_claim_complete_publication(self):
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("WARNING", result.stdout)

    def test_missing_pdf_blocks_strict_release(self):
        result = self.run_validator("--strict")
        self.assertEqual(result.returncode, 1)
        self.assertIn("paper file not found", result.stderr)

    def test_non_string_title_reports_error_without_crashing(self):
        path = self.root / "preprint.yaml"
        path.write_text(path.read_text().replace('title: "Untitled Preprint"', 'title: []'), encoding="utf-8")
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("title must be a non-empty string", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
