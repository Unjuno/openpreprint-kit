"""The owner launcher defaults to no action and authenticates before creating work."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/publish_first_paper.sh'


class FirstPaperLauncherTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), 'owner first-paper launcher missing')

    def test_default_is_offline_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=subprocess.run(['/bin/bash',str(SCRIPT)],cwd=tmp,
                env={**os.environ,'PATH':'/nonexistent'},capture_output=True,text=True,timeout=10)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertIn('PLAN_ONLY',r.stdout)
            self.assertIn('Unjuno/openpreprint-kit-paper',r.stdout)
            self.assertEqual(list(Path(tmp).iterdir()),[])

    def test_unknown_flag_rejected(self):
        r=subprocess.run(['/bin/bash',str(SCRIPT),'--force'],capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,2)

    def test_shell_syntax(self):
        r=subprocess.run(['/bin/bash','-n',str(SCRIPT)],capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stderr)

    def test_fixed_inputs_and_trust_are_explicit(self):
        text=SCRIPT.read_text()
        self.assertIn('43279522755',text)
        self.assertIn('manuscripts/openpreprint-kit/approved-v1/paper.pdf',text)
        self.assertNotIn('gh run download',text)
        self.assertIn('0860b735379fb1b9b223f5d535442dae8421f456d7ae1c6bf6ce8d3141a1b07c',text)
        self.assertIn('2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438',text)
        self.assertIn('--require-hashes',text)
        self.assertIn('openssl crl',text)
        self.assertNotIn('curl -k',text)
        self.assertNotIn('gh auth token',text)
        self.assertLess(text.index('gh auth status'),text.index('mktemp -d'))
        self.assertLess(text.index('sha256sum -c'),text.index('scripts/first_paper_publish.py'))

    def test_auth_failure_does_not_start_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake=Path(tmp)/'gh'
            fake.write_text('#!/bin/sh\nexit 1\n'); fake.chmod(0o755)
            before=set(Path(tmp).iterdir())
            r=subprocess.run(['/bin/bash',str(SCRIPT),'--publish'],cwd=tmp,
                env={**os.environ,'PATH':tmp+':'+os.environ['PATH']},
                capture_output=True,text=True,timeout=10)
            self.assertNotEqual(r.returncode,0)
            self.assertEqual(set(Path(tmp).iterdir()),before)
