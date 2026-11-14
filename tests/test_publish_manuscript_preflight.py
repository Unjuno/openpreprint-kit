"""Regression guard: invalid publication inputs must never reach GitHub writes.

The runner used to commit/push to the new repository before the strict
research-asset validation (public_confirmed enforcement and undeclared-file
rejection) happened. It now validates and builds the complete bundle locally
first. These tests lock that in by:

1. using a valid dummy TSA policy (mocked load_policy) and a fully declared,
   public_confirmed=true manifest as the valid control;
2. injecting a single, isolated defect at a time (public_confirmed=false;
   an undeclared file inside a research area);
3. asserting the rejection reason mentions the specific defect;
4. asserting zero GitHub API/command calls were made for rejected input;
5. asserting the valid control proceeds past preflight into the first
   GitHub gateway call (tools()) without raising during validation.

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
        self.manuscript = self.tmp / "manuscript"
        self.manuscript.mkdir()
        for area in ("data", "analysis", "supplements"):
            (self.manuscript / area).mkdir()
        (self.manuscript / "paper.md").write_text("# test\n", encoding="utf-8")
        (self.manuscript / "LICENSE-NOTICE.txt").write_text("TEST\n", encoding="utf-8")
        (self.manuscript / "preprint.yaml").write_text(
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
        with (self.manuscript / "paper.pdf").open("wb") as fh:
            writer.write(fh)
        (self.manuscript / "data" / "release-matrix.json").write_text("{}\n",
                                                                     encoding="utf-8")
        (self.manuscript / "analysis" / "summarize_test.py").write_text(
            "print('PASS')\n", encoding="utf-8")
        self.out = self.tmp / "out"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _runner(self):
        import importlib
        return importlib.import_module("publish_manuscript")

    def _spy(self):
        class SpyGitHub:
            def __init__(self):
                self.calls = []

            def tools(self):
                self.calls.append("tools")
                raise RuntimeError("STOP-AFTER-PREFLIGHT")

            def command(self, args):
                self.calls.append(("command", tuple(args[:2])))
                raise RuntimeError("STOP-AFTER-PREFLIGHT")

            def api(self, method, path, data=None, *, allow_missing=False):
                self.calls.append(("api", method, path))
                raise RuntimeError("STOP-AFTER-PREFLIGHT")

            def anonymous_source(self, repository, commit, path):
                self.calls.append(("anonymous_source", repository))
                raise RuntimeError("STOP-AFTER-PREFLIGHT")

            def anonymous(self, repository, version, name):
                self.calls.append(("anonymous", repository, version, name))
                raise RuntimeError("STOP-AFTER-PREFLIGHT")

        return SpyGitHub()

    def _write_assets(self, assets_yaml: str):
        (self.manuscript / "research-assets.yaml").write_text(assets_yaml, encoding="utf-8")

    def _patch_and_run(self, spy_with_calls: bool = True):
        pm = self._runner()
        spy = self._spy()
        pm.GitHub = lambda: spy
        pm.load_policy = lambda path: {
            "tsa_url": "https://freetsa.org/tsr",
            "ca_file": "dummy", "ca_sha256": "0" * 64,
            "crl_file": "dummy", "policy_oid": "1.2.3.4.1",
            "timeout_seconds": 45,
        }
        try:
            pm.execute(self.manuscript, "v1", "Unjuno/test-does-not-exist",
                       new_repo=True, paper_pdf=self.manuscript / "paper.pdf",
                       paper_sha256=pm.digest_file(self.manuscript / "paper.pdf"),
                       policy_path=self.tmp / "dummy-policy.json",
                       output=self.out)
        except Exception as exc:  # expected: either spy's STOP or a validation error
            return exc, spy
        return None, spy

    _VALID_YAML = (
        "schema_version: 1\n"
        "public_assets:\n"
        "- path: data/release-matrix.json\n"
        "  role: dataset\n"
        "  description: declared\n"
        "  license: CC-BY-4.0\n"
        "  public_confirmed: true\n"
        "- path: analysis/summarize_test.py\n"
        "  role: analysis_code\n"
        "  description: declared\n"
        "  license: MIT\n"
        "  public_confirmed: true\n"
        "- path: supplements/paper.md\n"
        "  role: supplementary\n"
        "  description: declared\n"
        "  license: CC-BY-4.0\n"
        "  public_confirmed: true\n"
        "- path: supplements/LICENSE-NOTICE.txt\n"
        "  role: supplementary\n"
        "  description: declared\n"
        "  license: CC-BY-4.0\n"
        "  public_confirmed: true\n"
        "relations: []\n"
    )

    def test_valid_input_reaches_first_github_call(self):
        self._write_assets(self._VALID_YAML)
        exc, spy = self._patch_and_run()
        self.assertIsNotNone(exc)
        self.assertIn("STOP-AFTER-PREFLIGHT", str(exc))
        self.assertEqual(spy.calls, ["tools"])

    def test_public_confirmed_false_alone_is_rejected(self):
        self._write_assets(self._VALID_YAML.replace("public_confirmed: true",
                                                    "public_confirmed: false", 1))
        exc, spy = self._patch_and_run()
        self.assertIsNotNone(exc)
        self.assertIn("public_confirmed", str(exc))
        self.assertEqual(spy.calls, [])

    def test_undeclared_file_in_research_area_alone_is_rejected(self):
        (self.manuscript / "data" / "extra.txt").write_text("hidden\n", encoding="utf-8")
        self._write_assets(self._VALID_YAML)  # only declared files
        exc, spy = self._patch_and_run()
        self.assertIsNotNone(exc)
        self.assertIn("undeclared research file", str(exc))
        self.assertEqual(spy.calls, [])


if __name__ == "__main__":
    unittest.main()
