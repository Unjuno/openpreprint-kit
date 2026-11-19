"""Regression tests for the 2026-11-18 continuation-cycle audit.

Findings: docs/TECHNICAL_AUDIT_2026-11-18.md (AUD-10..AUD-13).
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

RID = "f" * 32


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], text=True,
                          capture_output=True, check=True).stdout.strip()


class Iteration3FixTests(unittest.TestCase):
    """AUD-10: all-zero baseline must never return PASS."""

    def test_all_zero_baseline_is_rejected(self):
        import commitment_history as ch
        errors = ch.protect_history(ROOT, "0" * 40)
        self.assertTrue(errors)
        self.assertIn("zero", " ".join(errors))

    """AUD-11: tamper-and-restore in intermediate commits must fail."""

    def test_tamper_then_restore_is_rejected(self):
        import commitment_history as ch
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            folder = repo / "evidence" / "commitments"
            folder.mkdir(parents=True)
            receipt = folder / (RID + ".json")
            original = json.dumps({"schema_version": 1, "record_id": RID,
                                   "algorithm": "HMAC-SHA256", "commitment": "a" * 64})
            receipt.write_text(original, encoding="utf-8")
            _git(repo, "init", "-q", "-b", "main")
            _git(repo, "config", "user.email", "t@e.invalid")
            _git(repo, "config", "user.name", "T")
            _git(repo, "add", "-A")
            _git(repo, "commit", "-qm", "base")
            base = _git(repo, "rev-parse", "HEAD")

            receipt.write_text(original.replace("a" * 64, "b" * 64), encoding="utf-8")
            _git(repo, "add", "-A")
            _git(repo, "commit", "-qm", "tamper")
            receipt.write_text(original, encoding="utf-8")
            _git(repo, "add", "-A")
            _git(repo, "commit", "-qm", "restore")

            # The old net-endpoint diff was empty (the bug).
            net = _git(repo, "diff", "--name-status", base, "HEAD", "--", "evidence/commitments")
            self.assertEqual(net, "")
            # The new per-commit guard must still reject the tamper.
            errors = ch.protect_history(repo, base)
            self.assertTrue(errors)
            self.assertTrue(any("changed or deleted" in e for e in errors))

    def test_tampered_receipt_merged_from_side_branch_is_rejected(self):
        import commitment_history as ch
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            folder = repo / "evidence" / "commitments"
            folder.mkdir(parents=True)
            receipt = folder / (RID + ".json")
            original = json.dumps({"schema_version": 1, "record_id": RID,
                                   "algorithm": "HMAC-SHA256", "commitment": "a" * 64})
            receipt.write_text(original, encoding="utf-8")
            _git(repo, "init", "-q", "-b", "main")
            _git(repo, "config", "user.email", "t@e.invalid")
            _git(repo, "config", "user.name", "T")
            _git(repo, "add", "-A")
            _git(repo, "commit", "-qm", "base")
            base = _git(repo, "rev-parse", "HEAD")

            _git(repo, "checkout", "-qb", "side")
            receipt.write_text(original.replace("a" * 64, "b" * 64), encoding="utf-8")
            _git(repo, "add", "-A")
            _git(repo, "commit", "-qm", "side tamper")
            _git(repo, "checkout", "-q", "main")
            (repo / "README.md").write_text("advance main\n", encoding="utf-8")
            _git(repo, "add", "-A")
            _git(repo, "commit", "-qm", "main advance")
            _git(repo, "merge", "-q", "--no-ff", "side", "-m", "merge side")

            self.assertTrue(ch.protect_history(repo, base))

    """AUD-12: deeply nested JSON must produce a clean FAIL, not a traceback."""

    def test_deeply_nested_json_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "reviews").mkdir()
            (root / "reviews" / "record.json").write_text(
                "[" * 3000 + "]" * 3000, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "research_record.py"),
                 "--root", str(root), "--record", "reviews/record.json"],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("FAIL:", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    """AUD-13: '..' must not bypass the outside-the-bundle guard."""

    def test_export_candidate_resolves_dotdot(self):
        import first_paper_selftest as fps
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            bundle = root / "bundle"
            bundle.mkdir()
            (bundle / "paper.pdf").write_bytes(b"%PDF-1.7\n")
            (root / "sibling").mkdir()
            destination = root / "sibling" / ".." / "bundle" / "export"

            calls = {"n": 0}

            def spy(*args, **kwargs):
                calls["n"] += 1
                raise AssertionError("copytree must not be reached")

            with mock.patch.object(fps, "verify_bundle", return_value=[]), \
                    mock.patch.object(fps.shutil, "copytree", side_effect=spy):
                with self.assertRaisesRegex(ValueError, "outside the source bundle"):
                    fps.export_candidate(bundle, destination)
            self.assertEqual(calls["n"], 0)


if __name__ == "__main__":
    unittest.main()
