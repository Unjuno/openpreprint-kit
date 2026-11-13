"""Exact approved bytes must survive Actions-artifact expiry and preview copies."""
import hashlib
import json
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / 'manuscripts/openpreprint-kit/approved-v1/paper.pdf'
ARCHIVE = ROOT / 'evidence/first-paper/approved-v1/prepublication.opk.zip'
PDF_SHA = '0860b735379fb1b9b223f5d535442dae8421f456d7ae1c6bf6ce8d3141a1b07c'
ARCHIVE_SHA = '3e78455af37a0872d994d9d3c12eca6a1db1568a86671d55aa71ac020aa76a3d'


class ApprovedPaperInputTests(unittest.TestCase):
    def test_versioned_pdf_is_exactly_the_approved_stamped_input(self):
        self.assertTrue(PDF.is_file(), 'approved PDF must not exist only in an expiring CI artifact')
        self.assertFalse(PDF.is_symlink())
        self.assertEqual(hashlib.sha256(PDF.read_bytes()).hexdigest(), PDF_SHA)

    def test_retained_archive_contains_identical_pdf_and_original_proof(self):
        self.assertTrue(ARCHIVE.is_file(), 'original issued proof must be retained without relabeling')
        self.assertEqual(hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(), ARCHIVE_SHA)
        with zipfile.ZipFile(ARCHIVE) as z:
            self.assertEqual(z.read('bundle/paper.pdf'), PDF.read_bytes())
            meta = json.loads(z.read('bundle/preprint-metadata.json'))
            self.assertIsNone(meta['source_claim'])
            self.assertIn('bundle/timestamp.tsq', z.namelist())
            self.assertIn('bundle/timestamp.tsr', z.namelist())
            self.assertFalse(any(name.endswith('.key') for name in z.namelist()))

    def test_launcher_does_not_require_temporary_artifact_download(self):
        launcher = (ROOT / 'scripts/publish_first_paper.sh').read_text()
        self.assertNotIn('gh run download', launcher)
        self.assertIn('manuscripts/openpreprint-kit/approved-v1/paper.pdf', launcher)
        self.assertLess(launcher.index('sha256sum -c'), launcher.index('gh auth status'))

    def test_wrong_preview_pdf_is_rejected_before_authentication(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root / 'scripts').mkdir()
            p = root / 'manuscripts/openpreprint-kit/approved-v1/paper.pdf'
            p.parent.mkdir(parents=True); p.write_bytes(b'%PDF-1.4\nnot approved bytes')
            script = root / 'scripts/publish_first_paper.sh'
            shutil.copyfile(ROOT / 'scripts/publish_first_paper.sh', script)
            tools = root / 'bin'; tools.mkdir()
            called = root / 'gh-was-called'
            (tools / 'gh').write_text('#!/bin/sh\ntouch "'+str(called)+'"\nexit 1\n')
            (tools / 'gh').chmod(0o755)
            result = subprocess.run(['/bin/bash', str(script), '--publish'], cwd=root,
                env={**os.environ, 'PATH': str(tools)+os.pathsep+os.environ['PATH']},
                capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(called.exists(), 'unapproved PDF must be rejected before asking for credentials')

    def test_evidence_copy_is_not_mislabeled_as_a_public_release(self):
        path = ROOT / 'evidence/first-paper/approved-v1/retention.json'
        self.assertTrue(path.is_file(), 'retention receipt missing')
        report = json.loads(path.read_text())
        self.assertEqual(report['scope'], 'RETAINED_APPROVED_PREPUBLICATION_INPUT_NOT_A_RELEASE')
        self.assertFalse(report['public_paper_release'])
        self.assertEqual(report['origin_run'], 43279522755)


if __name__ == '__main__': unittest.main()
