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
        (self.folder / "preprint-metadata.json").write_text(json.dumps({"title": "Sample", "version": "v1"}), encoding="utf-8")
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
        self.assertIn(str(self.folder / "CITATION.cff"), proc.call_args.args[0])

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
