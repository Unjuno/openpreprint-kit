"""Black-box regression tests for preprint publication bundle and verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

SOURCE_ROOT = Path(__file__).resolve().parents[1]


class ReleaseBundleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "scripts").mkdir()
        (self.root / "paper").mkdir()
        for file in ("validate.py", "prepare_release.py", "verify_release.py"):
            shutil.copy2(SOURCE_ROOT / "scripts" / file, self.root / "scripts" / file)
        self.paper = self.root / "paper" / "paper.pdf"
        # This stub is sufficient for signature checks; PDF rendering is not tested.
        self.paper.write_bytes(b"%PDF-1.7\n% Unit test fixture\n%%EOF\n")
        self.metadata = {
            "schema_version": 1,
            "title": "A test preprint on {physics} & mathematics",
            "authors": [
                {"family_names": "Doe", "given_names": "Jane", "orcid": "0000-0002-1825-0097"},
                {"name": "Research Group"},
            ],
            "abstract": "A small reproducibility test.",
            "keywords": ["research", "検証"],
            "version": "v1",
            "paper": "paper/paper.pdf",
            "license": "CC-BY-4.0",
        }
        self.write_metadata()
        self.bundle = self.root / "dist"

    def tearDown(self):
        self.temporary.cleanup()

    def write_metadata(self):
        (self.root / "preprint.yaml").write_text(
            yaml.safe_dump(self.metadata, allow_unicode=True), encoding="utf-8"
        )

    def run_script(self, name, *arguments):
        return subprocess.run(
            [sys.executable, str(self.root / "scripts" / name), *map(str, arguments)],
            capture_output=True, text=True, check=False,
        )

    def make_bundle(self):
        result = self.run_script(
            "prepare_release.py", "--output", self.bundle,
            "--repository", "example/science-paper",
            "--commit", "a" * 40,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_roundtrip_and_citation_files(self):
        self.make_bundle()
        result = self.run_script("verify_release.py", self.bundle)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("NOT established", result.stdout)
        cited = yaml.safe_load((self.bundle / "CITATION.cff").read_text())
        self.assertEqual(cited["cff-version"], "1.2.0")
        self.assertEqual(cited["authors"][0]["family-names"], "Doe")
        self.assertEqual(cited["authors"][1]["name"], "Research Group")
        self.assertIn(r"\{physics\} \&", (self.bundle / "citation.bib").read_text())
        record = json.loads((self.bundle / "preprint-metadata.json").read_text())
        self.assertEqual(record["time_attestation"], None)
        self.assertEqual(record["paper_sha256"], hashlib.sha256(self.paper.read_bytes()).hexdigest())

    def test_tampered_pdf_is_rejected(self):
        self.make_bundle()
        (self.bundle / "paper.pdf").write_bytes(b"%PDF-1.7\nModified content\n")
        result = self.run_script("verify_release.py", self.bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checksum/size mismatch", result.stderr)

    def test_tampered_manifest_is_rejected(self):
        self.make_bundle()
        (self.bundle / "manifest.json").write_text("{}", encoding="utf-8")
        result = self.run_script("verify_release.py", self.bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported manifest schema", result.stderr)

    def test_mismatched_trusted_fingerprint_is_rejected(self):
        self.make_bundle()
        result = self.run_script(
            "verify_release.py", self.bundle, "--expected-paper-sha256", "0" * 64
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("separately supplied", result.stderr)

    def test_matching_trusted_fingerprint(self):
        self.make_bundle()
        digest = hashlib.sha256(self.paper.read_bytes()).hexdigest()
        result = self.run_script(
            "verify_release.py", self.bundle, "--expected-paper-sha256", digest
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("separately supplied", result.stdout)

    def test_draft_is_not_publishable(self):
        self.metadata["title"] = "Untitled Preprint"
        self.write_metadata()
        result = self.run_script("prepare_release.py", "--output", self.bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.bundle.exists())

    def test_traversal_in_pdf_path_is_rejected(self):
        self.metadata["paper"] = "../../outside.pdf"
        self.write_metadata()
        result = self.run_script("prepare_release.py", "--output", self.bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("paper path must stay inside", result.stderr)

    def test_overwriting_an_existing_bundle_is_rejected(self):
        self.make_bundle()
        result = self.run_script("prepare_release.py", "--output", self.bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be empty", result.stderr)

    def test_build_is_deterministic(self):
        self.make_bundle()
        original = {p.name: p.read_bytes() for p in self.bundle.iterdir()}
        shutil.rmtree(self.bundle)
        self.make_bundle()
        self.assertEqual(original, {p.name: p.read_bytes() for p in self.bundle.iterdir()})

    def test_absent_release_asset_is_rejected(self):
        self.make_bundle()
        (self.bundle / "citation.bib").unlink()
        result = self.run_script("verify_release.py", self.bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing", result.stderr)

    def test_symlink_is_rejected(self):
        self.make_bundle()
        (self.bundle / "citation.bib").unlink()
        (self.bundle / "citation.bib").symlink_to(self.bundle / "CITATION.cff")
        result = self.run_script("verify_release.py", self.bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("non-symlink", result.stderr)


if __name__ == "__main__":
    unittest.main()
