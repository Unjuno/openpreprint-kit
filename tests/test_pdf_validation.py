"""Security-focused black-box tests for publication PDF gate."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import yaml

from pdf_fixture import write_pdf

ROOT = Path(__file__).resolve().parents[1]

class PdfPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "scripts", self.root / "scripts")
        (self.root / "paper").mkdir()
        self.paper = self.root / "paper" / "paper.pdf"
        self.metadata = {
            "schema_version": 1, "title": "Verified Test Paper",
            "authors": [{"given_names": "Alice", "family_names": "Example"}],
            "abstract": "A synthetic document for testing only.",
            "keywords": ["test"], "version": "v1",
            "paper": "paper/paper.pdf", "license": "CC-BY-4.0",
        }
        (self.root / "preprint.yaml").write_text(yaml.safe_dump(self.metadata), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def run_strict(self):
        return subprocess.run([sys.executable, str(self.root / "scripts" / "validate.py"), "--strict"],
                              capture_output=True, text=True, timeout=12, check=False)

    def test_dependency_manifest_uses_known_patched_pypdf(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("pypdf==6.21.4", requirements,
                      "Unpatched PDF parser versions are forbidden for publication")

    def test_valid_structural_pdf_passes(self):
        write_pdf(self.paper)
        result = self.run_strict()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_magic_only_fake_pdf_fails(self):
        self.paper.write_bytes(b"%PDF-1.7\nthis is not a real PDF\n%%EOF\n")
        result = self.run_strict()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PDF", result.stderr)

    def test_pdf_without_pages_fails(self):
        write_pdf(self.paper, pages=0)
        result = self.run_strict()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("page", result.stderr.lower())

    def test_javascript_open_action_fails(self):
        write_pdf(self.paper, javascript=True)
        result = self.run_strict()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("interactive", result.stderr.lower())

    def test_attached_file_fails(self):
        write_pdf(self.paper, attachment=True)
        result = self.run_strict()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("interactive", result.stderr.lower())

    def test_encrypted_pdf_fails(self):
        write_pdf(self.paper, encrypted=True)
        result = self.run_strict()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("encrypted", result.stderr.lower())

    def test_page_limit_fails(self):
        write_pdf(self.paper, pages=501)
        result = self.run_strict()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("500", result.stderr)

    def test_size_limit_fails_before_parsing(self):
        self.paper.write_bytes(b"%PDF-1.7\n")
        with self.paper.open("ab") as stream:
            stream.truncate(25 * 1024 * 1024 + 1)
        result = self.run_strict()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("25 MiB", result.stderr)

if __name__ == "__main__":
    unittest.main()
