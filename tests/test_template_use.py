"""A user's completed manuscript must not break the template's own tests."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TemplateUseTests(unittest.TestCase):
    def test_validator_suite_ignores_author_manuscript_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / 'scripts', root / 'scripts', ignore=shutil.ignore_patterns('__pycache__'))
            (root / 'tests').mkdir()
            shutil.copy2(ROOT / 'tests/test_validate.py', root / 'tests/test_validate.py')
            (root / 'preprint.yaml').write_text('''schema_version: 1
title: "An author's real title, not a template placeholder"
authors:
  - name: "Synthetic group"
abstract: "Completed manuscript metadata, not a draft."
keywords: [synthetic]
version: v2
paper: paper/approved.pdf
license: CC0-1.0
''', encoding='utf-8')
            result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_validate.py', '-v'], cwd=root, text=True, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
