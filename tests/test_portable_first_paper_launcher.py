"""Cross-platform, no-network regression tests for the owner publication launcher."""
from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/publish_first_paper.py"
spec = importlib.util.spec_from_file_location("opk_portable_publisher", SCRIPT)
launcher = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(launcher)


class PortableFirstPaperLauncherTests(unittest.TestCase):
    def test_plan_is_offline_and_has_no_side_effects(self):
        with patch.object(launcher, "check_paper", side_effect=AssertionError("unexpected file read")), \
             patch.object(launcher, "check_owner_environment", side_effect=AssertionError("unexpected network")), \
             patch.object(launcher, "publish", side_effect=AssertionError("unexpected publication")), \
             patch.object(launcher.tempfile, "mkdtemp", side_effect=AssertionError("unexpected write")):
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(launcher.main([]), 0)
            self.assertIn('"publication_performed": false', output.getvalue())
            self.assertIn("PLAN_ONLY", output.getvalue())

    def test_cli_plan_runs_without_shell_or_installation(self):
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, str(SCRIPT), "--plan"],
                                    cwd=folder, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PLAN_ONLY", result.stdout)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_real_approved_pdf_is_pinned(self):
        self.assertEqual(launcher.check_paper(), launcher.PAPER_SHA256)

    def test_modified_pdf_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            changed = Path(folder) / "paper.pdf"
            changed.write_bytes(b"%PDF-1.4\nunapproved")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                launcher.check_paper(changed)

    def test_bad_pdf_stops_before_auth_network_or_workspace(self):
        with patch.object(launcher, "check_paper", side_effect=ValueError("bad paper")), \
             patch.object(launcher, "check_owner_environment", side_effect=AssertionError("auth called")), \
             patch.object(launcher.tempfile, "mkdtemp", side_effect=AssertionError("workspace created")):
            with self.assertRaisesRegex(ValueError, "bad paper"):
                launcher.publish()

    def test_persistent_evidence_directory_and_source_separation(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder) / "owner-evidence"
            work = launcher.allocate_workspace(base)
            self.assertEqual(work.parent.resolve(), base.resolve())
            self.assertTrue(work.is_dir())
            with self.assertRaisesRegex(ValueError, "outside the toolkit"):
                launcher.allocate_workspace(ROOT / "disallowed-evidence")
            self.assertFalse((ROOT / "disallowed-evidence").exists())

    def test_windows_and_unix_venv_paths(self):
        base = Path("temporary") / "env"
        self.assertEqual(launcher.venv_python(base, windows=True),
                         base / "Scripts/python.exe")
        self.assertEqual(launcher.venv_python(base, windows=False),
                         base / "bin/python")

    def test_unknown_flags_cannot_publish(self):
        with self.assertRaises(SystemExit) as error:
            launcher.main(["--force"])
        self.assertEqual(error.exception.code, 2)

    def test_publish_requires_explicit_flag(self):
        with patch.object(launcher, "publish", return_value=0) as op:
            with redirect_stdout(io.StringIO()):
                self.assertEqual(launcher.main(["--plan"]), 0)
            op.assert_not_called()
            self.assertEqual(launcher.main(["--publish"]), 0)
            op.assert_called_once_with()

    def test_no_untrusted_timestamp_hosts(self):
        with self.assertRaisesRegex(ValueError, "unexpected TSA trust URL"):
            launcher.trust_download("https://evil.example/ca.pem")
        with self.assertRaisesRegex(ValueError, "unexpected TSA trust URL"):
            launcher.trust_download("http://freetsa.org/files/cacert.pem")

    def test_redirect_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "redirected"):
            launcher.NoRedirect().redirect_request(None, None, 302, "redirect", {},
                                                    "https://evil.example/ca.pem")

    def test_failed_command_does_not_expose_stdout_or_stderr(self):
        completed = subprocess.CompletedProcess(args=["gh"], returncode=1,
                                                stdout="private-token", stderr="credential-data")
        with patch.object(launcher.subprocess, "run", return_value=completed):
            with self.assertRaises(ValueError) as raised:
                launcher.command(["gh", "auth", "status"])
        self.assertNotIn("private-token", str(raised.exception))
        self.assertNotIn("credential-data", str(raised.exception))

    def test_no_fallback_when_root_pin_is_wrong(self):
        class Response:
            status = 200
            def geturl(self):
                return launcher.CA_URL
            def read(self, maximum):
                return b"untrusted replacement CA"
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False

        class Opener:
            def open(self, request, timeout):
                return Response()

        with patch.object(launcher.urllib.request, "build_opener", return_value=Opener()):
            with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
                launcher.trust_download(launcher.CA_URL,
                                        expected_sha256=launcher.CA_SHA256)


if __name__ == "__main__":
    unittest.main()
