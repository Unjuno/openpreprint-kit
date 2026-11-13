"""External CFF/BibTeX publication validation contract tests."""
from pathlib import Path
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from types import SimpleNamespace
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class CitationValidationTests(unittest.TestCase):
    def setUp(self):
        from citation_validation import validate_citations
        self.validate_citations = validate_citations
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.valid_cff = {
            "cff-version": "1.2.0", "message": "Cite this preprint",
            "title": "Sample", "authors": [{"family-names": "Doe", "given-names": "Jane"}],
            "version": "v1", "license": "CC-BY-4.0"
        }
        (self.folder / "CITATION.cff").write_text(yaml.safe_dump(self.valid_cff), encoding="utf-8")
        (self.folder / "citation.bib").write_text("@misc{sample_v1, title={Sample}, author={Doe, Jane}, note={v1}}\n", encoding="utf-8")
        self.metadata = {
            "title": "Sample", "version": "v1", "license": "CC-BY-4.0",
            "authors": [{"family_names": "Doe", "given_names": "Jane"}],
        }
        (self.folder / "preprint-metadata.json").write_text(json.dumps(self.metadata), encoding="utf-8")
        self.fake_bib = SimpleNamespace(loads=lambda x: SimpleNamespace(entries=[{
            "ENTRYTYPE": "misc", "title": "Sample", "author": "Doe, Jane", "note": "v1"}]))

    def tearDown(self):
        self.temp.cleanup()

    def validated(self, result=None, fake_bib=None):
        status = result or SimpleNamespace(returncode=0, stderr="", stdout="")
        with mock.patch("citation_validation.subprocess.run", return_value=status) as proc:
            with mock.patch.dict(sys.modules, {"bibtexparser": fake_bib or self.fake_bib}):
                self.validate_citations(self.folder)
        return proc

    def test_valid_cff_and_bibtex_pass(self):
        proc = self.validated()
        self.assertIn("--validate", proc.call_args.args[0])
        self.assertEqual(Path(proc.call_args.args[0][-1]).resolve(),
                         (self.folder / "CITATION.cff").resolve())

    def test_windows_venv_cffconvert_is_found_without_path_activation(self):
        # Reproduce the reported incident: venv/Scripts contains cffconvert,
        # while the caller's PATH does not include that directory.
        with tempfile.TemporaryDirectory() as folder:
            scripts = Path(folder) / "venv" / "Scripts"
            scripts.mkdir(parents=True)
            python = scripts / "python.exe"
            python.write_bytes(b"test-only stub")
            cff = scripts / "cffconvert.exe"
            cff.write_bytes(b"test-only stub; subprocess is mocked")
            with mock.patch("citation_validation.sys.executable", str(python)), \
                 mock.patch("citation_validation.shutil.which", return_value=None):
                proc = self.validated()
            self.assertEqual(Path(proc.call_args.args[0][0]), cff)

    def test_cffconvert_fallback_to_existing_path_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            python = Path(folder) / "no-venv" / "python.exe"
            with mock.patch("citation_validation.sys.executable", str(python)), \
                 mock.patch("citation_validation.shutil.which",
                            return_value="cffconvert-on-PATH"):
                proc = self.validated()
            self.assertEqual(proc.call_args.args[0][0], "cffconvert-on-PATH")

    def test_invalid_cff_schema_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "CFF"):
            self.validated(result=SimpleNamespace(returncode=1, stderr="failed schema", stdout=""))

    def test_malformed_bibtex_is_rejected(self):
        fake = SimpleNamespace(loads=lambda x: SimpleNamespace(entries=[]))
        with self.assertRaisesRegex(ValueError, "BibTeX"):
            self.validated(fake_bib=fake)

    def test_citation_title_conflict_is_rejected(self):
        cff = dict(self.valid_cff, title="Different title")
        (self.folder / "CITATION.cff").write_text(yaml.safe_dump(cff), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "title"):
            self.validated()

    def test_license_conflict_is_rejected(self):
        cff = dict(self.valid_cff, license="MIT")
        (self.folder / "CITATION.cff").write_text(yaml.safe_dump(cff), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "license"):
            self.validated()

    def test_author_conflict_is_rejected(self):
        cff = dict(self.valid_cff, authors=[{"name": "Impostor Group"}])
        (self.folder / "CITATION.cff").write_text(yaml.safe_dump(cff), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "authors"):
            self.validated()

    @unittest.skipUnless(importlib.util.find_spec("bibtexparser") and shutil.which("cffconvert"),
                         "actual external citation validators unavailable in local environment")
    def test_generated_publication_bundle_passes_real_schema(self):
        import test_release
        fixture = test_release.ReleaseBundleTests(methodName="test_roundtrip_and_citation_files")
        fixture.setUp()
        try:
            fixture.make_bundle()
            self.validate_citations(fixture.bundle)
        finally:
            fixture.tearDown()

    def test_bibtex_symlink_is_rejected(self):
        (self.folder / "citation.bib").unlink()
        (self.folder / "citation.bib").symlink_to(self.folder / "CITATION.cff")
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.validated()

    @unittest.skipUnless(importlib.util.find_spec("bibtexparser") and shutil.which("cffconvert"),
                         "actual external citation validators unavailable in local environment")
    def test_real_external_validators_accept_schema_conformant_fixture(self):
        self.validate_citations(self.folder)


if __name__ == "__main__":
    unittest.main()
