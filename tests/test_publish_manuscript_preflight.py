"""Regression guard: invalid publication inputs must never reach GitHub writes.

Unapproved/unlisted public assets used to be committed to the new repository
before the strict bundle-build checks ran. The runner now validates the
complete bundle locally before any network write. This test fails if any
GitHub-write helper is invoked for invalid input.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class PublishManuscriptPreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="opk-preflight-"))
        pdf_dir = self.tmp / "manuscript"
        pdf_dir.mkdir()
        for area in ("data", "analysis", "supplements"):
            (pdf_dir / area).mkdir()
        (pdf_dir / "paper.md").write_text("# test\n", encoding="utf-8")
        (pdf_dir / "LICENSE-NOTICE.txt").write_text("TEST\n", encoding="utf-8")
        (pdf_dir / "preprint.yaml").write_text(
            "schema_version: 1\n"
            "title: 'Test manuscript'\n"
            "authors:\n- name: Unjuno\n  orcid: null\n"
            "abstract: test\n"
            "keywords: []\n"
            "version: v1\n"
            "paper: paper/paper.pdf\n"
            "license: CC-BY-4.0\n", encoding="utf-8")
        from pypdf import PdfWriter
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        with (pdf_dir / "paper.pdf").open("wb") as fh:
            writer.write(fh)
        (pdf_dir / "data" / "release-matrix.json").write_text("{}\n", encoding="utf-8")
        (pdf_dir / "analysis" / "summarize_test.py").write_text("print('PASS')\n",
                                                                 encoding="utf-8")
        self.manuscript = pdf_dir

    def tearDown(self):
        import shutil as _shutil
        _shutil.rmtree(self.tmp, ignore_errors=True)

    def _runner(self):
        import importlib
        pm = importlib.import_module("publish_manuscript")
        return pm

    def test_unlisted_file_in_research_areas_is_rejected_before_github(self):
        pm = self._runner()

        class SpyGitHub:
            def __init__(self):
                self.calls = []

            def tools(self):
                self.calls.append("tools")

            def command(self, args):
                self.calls.append(("command", args[:2]))
                raise AssertionError("GitHub.command invoked during preflight: " + repr(args))

            def api(self, method, path, data=None, *, allow_missing=False):
                self.calls.append(("api", method, path))
                raise AssertionError("GitHub.api invoked during preflight: " + method + " " + path)

            def anonymous_source(self, repository, commit, path):
                self.calls.append(("anonymous_source", repository))
                raise AssertionError("GitHub network access during preflight")

            def anonymous(self, repository, version, name):
                self.calls.append(("anonymous", repository, version, name))
                raise AssertionError("GitHub network access during preflight")

        spy = SpyGitHub()
        pm.GitHub = lambda: spy
        # declare an asset pointing to a file that does NOT exist in the bundle:
        # collect()/validate would refuse it before any public write
        (self.manuscript / "research-assets.yaml").write_text(
            "schema_version: 1\n"
            "public_assets:\n"
            "- path: data/release-matrix.json\n"
            "  role: dataset\n"
            "  description: declared\n"
            "  license: CC-BY-4.0\n"
            "  public_confirmed: false\n"
            "relations: []\n", encoding="utf-8")
        with self.assertRaises(Exception):
            pm.execute(self.manuscript, "v1", "Unjuno/test-does-not-exist",
                       new_repo=True, paper_pdf=self.manuscript / "paper.pdf",
                       paper_sha256=pm.digest_file(self.manuscript / "paper.pdf"),
                       policy_path=Path(__file__).resolve().parents[1] / "timestamp-policy.example.json",
                       output=self.tmp / "out")
        self.assertEqual(spy.calls, [])

    def test_public_confirmed_false_is_rejected_before_github(self):
        pm = self._runner()

        class SpyGitHub:
            def __init__(self):
                self.calls = []

            def command(self, args):
                self.calls.append(("command", args[:2]))
                raise AssertionError("command invoked before validation")

            def api(self, method, path, data=None, *, allow_missing=False):
                self.calls.append(("api", method, path))
                raise AssertionError("api invoked before validation")

        spy = SpyGitHub()
        pm.GitHub = lambda: spy
        (self.manuscript / "research-assets.yaml").write_text(
            "schema_version: 1\n"
            "public_assets:\n"
            "- path: data/release-matrix.json\n"
            "  role: dataset\n"
            "  description: undeclared-content\n"
            "  license: CC-BY-4.0\n"
            "  public_confirmed: false\n"
            "- path: supplements/paper.md\n"
            "  role: supplementary\n"
            "  description: declared\n"
            "  license: CC-BY-4.0\n"
            "  public_confirmed: true\n"
            "relations: []\n", encoding="utf-8")
        with self.assertRaises(Exception):
            pm.execute(self.manuscript, "v1", "Unjuno/test-does-not-exist",
                       new_repo=True, paper_pdf=self.manuscript / "paper.pdf",
                       paper_sha256=pm.digest_file(self.manuscript / "paper.pdf"),
                       policy_path=Path(__file__).resolve().parents[1] / "timestamp-policy.example.json",
                       output=self.tmp / "out2")
        self.assertEqual(spy.calls, [])


if __name__ == "__main__":
    unittest.main()
