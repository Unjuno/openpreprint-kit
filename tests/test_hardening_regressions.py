"""Regression tests for the 2026-11-17 technical-hardening audit.

Each test corresponds to a finding in docs/TECHNICAL_AUDIT_2026-11-17.md:
it reproduces the original failure condition and asserts the fixed behaviour.
"""
from __future__ import annotations

import contextlib
import importlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

SHA = "a" * 64
COMMIT = "b" * 40


def _publisher_patches(**overrides):
    pm = importlib.import_module("publish_manuscript")
    noop = lambda *a, **k: None
    base = {
        "validate_input_tree": noop,
        "read_metadata": lambda m, e: {"title": "t", "version": "v1"},
        "inspect_pdf": lambda p: (b"", 1),
        "load_policy": lambda p: {"tsa_url": "https://x/tsr", "timeout_seconds": 45},
        "stage": lambda m, p, s, md: ([], ""),
        "validate_assets_in": lambda s: {},
        "digest_file": lambda p: SHA,
        "run": lambda script, *args, **k: (
            Path(args[args.index("--output") + 1]).mkdir(parents=True, exist_ok=True)
            if "--output" in args else None) or "",
        "_commit_inputs": lambda *a, **k: COMMIT,
        "preflight": lambda *a, **k: {"status": "PASS"},
        "make_query": lambda *a, **k: b"q",
        "post_query": lambda *a, **k: b"r",
        "attach": noop,
        "verify_all": lambda *a, **k: {"existence_tsa_time_utc": "2026-01-01T00:00:00+00:00"},
        "download_bundle": noop,
        "_same": noop,
        "verify_source_snapshot": lambda *a, **k: {},
        "pack": lambda *a, **k: {"archive_sha256": "c" * 64},
        "restore": noop,
        "verify_existing_v2_preserved": lambda *a, **k: {},
    }
    base.update(overrides)
    return pm, [patch.object(pm, name, value) for name, value in base.items()]


class AuditFixTests(unittest.TestCase):
    """F1: per-Release immutable/draft/tag/asset readback before PASS."""

    def test_mutable_public_release_is_rejected(self):
        pm, patches = _publisher_patches()
        calls = []

        class FakeGitHub:
            def tools(self):
                pass

            def command(self, args):
                return ""

            def api(self, method, path, data=None, *, allow_missing=False):
                calls.append(path)
                if path == "repos/Unjuno/openpreprint-kit":
                    return {"private": False, "full_name": "Unjuno/openpreprint-kit", "is_template": True}
                if path == "repos/owner/repo" and allow_missing:
                    return None
                if path == "repos/owner/repo" and not allow_missing:
                    return {"private": False, "full_name": "owner/repo",
                            "permissions": {"admin": True},
                            "template_repository": {"full_name": "Unjuno/openpreprint-kit"}}
                if path == "repos/owner/repo/immutable-releases":
                    return {"enabled": True}
                if path == "repos/owner/repo/releases/tags/v1":
                    return {"immutable": False, "draft": False, "tag_name": "v1", "assets": []}
                raise AssertionError("unexpected API path: " + path)

        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            pdf = work / "paper.pdf"
            pdf.write_bytes(b"%PDF-1.7\n")
            manuscript = work / "manuscript"
            manuscript.mkdir()
            all_patches = [patch.object(pm, "GitHub", FakeGitHub), *patches]
            for p in all_patches:
                p.start()
            try:
                with self.assertRaisesRegex(ValueError, "readback"):
                    pm.execute(manuscript, "v1", "owner/repo", True, pdf,
                               SHA, work / "policy.json", work / "out")
            finally:
                for p in reversed(all_patches):
                    p.stop()
        self.assertIn("repos/owner/repo/releases/tags/v1", calls)

    def test_immutable_public_release_reports_readback(self):
        pm, patches = _publisher_patches()

        class FakeGitHub:
            def tools(self):
                pass

            def command(self, args):
                return ""

            def api(self, method, path, data=None, *, allow_missing=False):
                if path == "repos/Unjuno/openpreprint-kit":
                    return {"private": False, "full_name": "Unjuno/openpreprint-kit", "is_template": True}
                if path == "repos/owner/repo" and allow_missing:
                    return None
                if path == "repos/owner/repo" and not allow_missing:
                    return {"private": False, "full_name": "owner/repo",
                            "permissions": {"admin": True},
                            "template_repository": {"full_name": "Unjuno/openpreprint-kit"}}
                if path == "repos/owner/repo/immutable-releases":
                    return {"enabled": True}
                if path == "repos/owner/repo/releases/tags/v1":
                    return {"immutable": True, "draft": False, "tag_name": "v1", "assets": []}
                raise AssertionError("unexpected API path: " + path)

        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            pdf = work / "paper.pdf"
            pdf.write_bytes(b"%PDF-1.7\n")
            manuscript = work / "manuscript"
            manuscript.mkdir()
            all_patches = [patch.object(pm, "GitHub", FakeGitHub), *patches]
            for p in all_patches:
                p.start()
            try:
                report = pm.execute(manuscript, "v1", "owner/repo", True, pdf,
                                    SHA, work / "policy.json", work / "out")
            finally:
                for p in reversed(all_patches):
                    p.stop()
        self.assertEqual(report["status"], "PASS")
        self.assertIs(report["release_immutable_readback"], True)

    """F2: git-tag availability must be checked before any source commit."""

    def test_occupied_git_tag_blocks_before_write(self):
        events = []

        class FakeGitHub:
            def tools(self):
                pass

            def command(self, args):
                events.append(("command", tuple(args[:2])))
                return ""

            def api(self, method, path, data=None, *, allow_missing=False):
                events.append(("api", path))
                if path == "repos/Unjuno/openpreprint-kit":
                    return {"private": False, "full_name": "Unjuno/openpreprint-kit", "is_template": True}
                if path == "repos/owner/repo":
                    return {"private": False, "full_name": "owner/repo"}
                if path == "repos/owner/repo/immutable-releases":
                    return {"enabled": True}
                if path == "repos/owner/repo/releases/tags/v2":
                    return None
                if path == "repos/owner/repo/git/ref/tags/v2":
                    return {"ref": "refs/tags/v2"}
                raise AssertionError("unexpected API path: " + path)

        def commit_hook(*a, **k):
            events.append(("WRITE", "commit"))
            return COMMIT

        pm, patches = _publisher_patches(
            read_metadata=lambda m, e: {"title": "t", "version": "v2"},
            _commit_inputs=commit_hook)
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            pdf = work / "paper.pdf"
            pdf.write_bytes(b"%PDF-1.7\n")
            manuscript = work / "manuscript"
            manuscript.mkdir()
            all_patches = [patch.object(pm, "GitHub", FakeGitHub), *patches]
            for p in all_patches:
                p.start()
            try:
                with self.assertRaisesRegex(ValueError, "git tag already exists"):
                    pm.execute(manuscript, "v2", "owner/repo", False, pdf,
                               SHA, work / "policy.json", work / "out")
            finally:
                for p in reversed(all_patches):
                    p.stop()
        self.assertFalse(any(e[0] == "WRITE" for e in events), events)

    """F3: owner_setup read-back re-validates identity/visibility/admin."""

    def test_owner_setup_readback_flip_is_rejected(self):
        owner_setup = importlib.import_module("owner_setup")
        state = {"repo_gets": 0, "writes": []}

        def fake_api(method, path, payload=None):
            if method == "GET" and path == "repos/example/research":
                state["repo_gets"] += 1
                if state["repo_gets"] == 1:
                    return {"full_name": "example/research", "private": False,
                            "permissions": {"admin": True}}
                return {"full_name": "example/research", "private": True,
                        "permissions": {"admin": False}}
            if method == "GET" and path.endswith("/immutable-releases"):
                return {"enabled": True}
            if method in ("PUT", "PATCH"):
                state["writes"].append((method, path))
                return None
            raise AssertionError((method, path))

        for apply in (False, True):
            state["repo_gets"] = 0
            state["writes"] = []
            with self.assertRaisesRegex(ValueError, "changed during configuration"):
                owner_setup.configure("example/research", apply, False, api=fake_api)
            if not apply:
                self.assertEqual(state["writes"], [])

    """F4: exactly one publication mode."""

    def test_plan_cannot_be_combined_with_publish(self):
        pm = importlib.import_module("publish_manuscript")
        for flags in (["--plan", "--publish"], ["--plan", "--verify-inputs"]):
            argv = ["prog", *flags, "--version", "v1", "--repository", "o/r",
                    "--manuscript", "m"]
            out = io.StringIO()
            with mock.patch.object(sys, "argv", argv), \
                    contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = pm.main()
            self.assertEqual(code, 2, flags)
            self.assertNotIn("PLAN_ONLY", out.getvalue())

    """F5: research_package re-validates containment at read time."""

    def test_ancestor_swap_after_collect_is_rejected(self):
        rp = importlib.import_module("research_package")
        import yaml

        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "repo"
            root.mkdir()
            (root / "data").mkdir()
            (root / "data" / "synthetic.csv").write_text("PUBLIC,x\n1,2\n", encoding="utf-8")
            cfg = {"schema_version": 1, "public_assets": [{
                "path": "data/synthetic.csv", "role": "dataset",
                "description": "Synthetic public data", "license": "CC0-1.0",
                "public_confirmed": True}], "relations": []}
            (root / "research-assets.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
            plan = rp.collect(root)
            self.assertIsNotNone(plan)

            outside = base / "outside"
            outside.mkdir()
            (outside / "synthetic.csv").write_text("SECRET,PATIENT\nacedeadbeef,cancer\n",
                                                   encoding="utf-8")
            (root / "data" / "synthetic.csv").unlink()
            (root / "data").rmdir()
            if sys.platform == "win32":
                res = subprocess.run(["cmd", "/c", "mklink", "/J",
                                      str(root / "data"), str(outside)],
                                     capture_output=True)
                if res.returncode:
                    self.skipTest("junction creation unavailable on this host")
            else:
                (root / "data").symlink_to(outside, target_is_directory=True)

            output = base / "release"
            output.mkdir()
            with self.assertRaisesRegex(ValueError, "unsafe during preparation"):
                rp.create_research(root, output, plan, "a" * 64, "v1")

    """AUD-09: the Hypothesis test module must import when the test-only
    dependency is absent (CI does not install it)."""

    def test_hypothesis_module_imports_without_dependency(self):
        code = (
            "import importlib.util, sys\n"
            "real = importlib.util.find_spec\n"
            "importlib.util.find_spec = lambda n,*a,**k: None if n=='hypothesis' else real(n,*a,**k)\n"
            f"sys.path.insert(0, {str(ROOT / 'tests')!r})\n"
            f"sys.path.insert(0, {str(ROOT / 'scripts')!r})\n"
            "import test_hypothesis_properties\n"
        )
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    """F6/F7: citation validation binds BibTeX and rejects duplicate keys."""

    def _citation_folder(self, metadata_text):
        import yaml
        folder = Path(tempfile.mkdtemp())
        cff = {"cff-version": "1.2.0", "message": "Cite", "title": "T", "version": "v1",
               "license": "CC-BY-4.0",
               "authors": [{"family-names": "Doe", "given-names": "Jane"}]}
        (folder / "CITATION.cff").write_text(yaml.safe_dump(cff), encoding="utf-8")
        (folder / "preprint-metadata.json").write_text(metadata_text, encoding="utf-8")
        return folder

    def test_duplicate_metadata_keys_rejected(self):
        cv = importlib.import_module("citation_validation")
        meta = ('{"title":"T","version":"v1","license":"WRONG",'
                '"license":"CC-BY-4.0",'
                '"authors":[{"family_names":"Doe","given_names":"Jane"}]}')
        folder = self._citation_folder(meta)
        (folder / "citation.bib").write_text("@misc{x,title={T},author={Doe, Jane},note={v1}}\n",
                                             encoding="utf-8")
        with mock.patch("citation_validation.subprocess.run",
                        return_value=SimpleNamespace(returncode=0, stderr="", stdout="")):
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                cv.validate_citations(folder)

    def test_mismatched_bibtex_is_rejected(self):
        cv = importlib.import_module("citation_validation")
        folder = self._citation_folder(json.dumps({
            "title": "T", "version": "v1", "license": "CC-BY-4.0",
            "authors": [{"family_names": "Doe", "given_names": "Jane"}]}))
        (folder / "citation.bib").write_text(
            "@misc{x,title={WRONG TITLE},author={Fraud, Fiona},note={v1}}\n", encoding="utf-8")
        with mock.patch("citation_validation.subprocess.run",
                        return_value=SimpleNamespace(returncode=0, stderr="", stdout="")):
            with self.assertRaisesRegex(ValueError, "BibTeX title"):
                cv.validate_citations(folder)


if __name__ == "__main__":
    unittest.main()

