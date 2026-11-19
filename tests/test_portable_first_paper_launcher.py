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

    def test_venv_console_script_and_utf8_inherited_by_publisher(self):
        # No GitHub calls; check the exact PATH a nested Python child will get.
        import os
        import shutil
        with tempfile.TemporaryDirectory() as folder:
            scripts = Path(folder) / ("Scripts" if os.name == "nt" else "bin")
            scripts.mkdir()
            executable = scripts / ("cffconvert.exe" if os.name == "nt" else "cffconvert")
            executable.write_bytes(b"not executed")
            executable.chmod(0o755)
            done = subprocess.CompletedProcess(["python"], 0, stdout="ready", stderr="")
            with patch.object(launcher.subprocess, "run", return_value=done) as proc:
                self.assertEqual(launcher.command(["python", "safe_child.py"],
                                                  path_prefix=scripts), "ready")
            env = proc.call_args.kwargs["env"]
            self.assertEqual(Path(env["PATH"].split(os.pathsep)[0]).resolve(),
                             scripts.resolve())
            self.assertEqual(Path(shutil.which("cffconvert", path=env["PATH"])).resolve(),
                             executable.resolve())
            self.assertEqual(env["PYTHONUTF8"], "1")
            self.assertEqual(env["PYTHONIOENCODING"], "utf-8")
            self.assertEqual(proc.call_args.kwargs["encoding"], "utf-8")
            self.assertEqual(proc.call_args.kwargs["errors"], "strict")

    def test_missing_venv_executable_directory_fails_before_child(self):
        with tempfile.TemporaryDirectory() as folder:
            missing = Path(folder) / "missing-Scripts"
            with patch.object(launcher.subprocess, "run",
                              side_effect=AssertionError("unexpected process")):
                with self.assertRaisesRegex(ValueError, "executable directory is missing"):
                    launcher.command(["python", "script.py"], path_prefix=missing)

    def test_publish_propagates_venv_scripts_only_to_explicit_publication_child(self):
        # Regression for the real Windows failure: cffconvert was installed in
        # venv/Scripts but first_paper_publish.py inherited a PATH without it.
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder) / "evidence"
            environment = work / "venv"
            python = launcher.venv_python(environment)
            python.parent.mkdir(parents=True)
            python.write_bytes(b"test-only stub; not executed")
            result = '{"status":"PASS","state":"VERIFIED_PUBLIC_PREPRINT"}'
            with patch.object(launcher, "check_paper"), \
                 patch.object(launcher, "check_owner_environment"), \
                 patch.object(launcher, "allocate_workspace", return_value=work), \
                 patch.object(launcher.venv.EnvBuilder, "create"), \
                 patch.object(launcher, "create_policy", return_value=work / "trust/policy.json"), \
                 patch.object(launcher, "command", side_effect=["", "", result]) as proc:
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(launcher.publish(), 0)
            self.assertEqual(len(proc.call_args_list), 3)
            install_a, install_b, child = proc.call_args_list
            self.assertNotIn("path_prefix", install_a.kwargs)
            self.assertNotIn("path_prefix", install_b.kwargs)
            self.assertEqual(child.kwargs["path_prefix"], python.parent)
            self.assertEqual(child.args[0][0], str(python))
            self.assertIn("--publish", child.args[0])

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
