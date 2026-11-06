"""Guard against unpinned build or runtime distributions in release/CI installs."""
from pathlib import Path
import re
import unittest
import yaml
ROOT=Path(__file__).resolve().parents[1]

class DependencyLockTests(unittest.TestCase):
    def test_all_resolved_packages_are_pinned_with_hashes(self):
        for name in ('requirements.lock','requirements-build.lock'):
            file=ROOT/name
            self.assertTrue(file.is_file(),'resolved hash lock missing')
            joined=file.read_text().replace('\\\n',' ')
            rows=[s.strip() for s in joined.splitlines() if s.strip() and not s.startswith('#')]
            self.assertTrue(rows)
            for row in rows:
                self.assertRegex(row,r'^[A-Za-z0-9_.-]+==[A-Za-z0-9_.-]+\s+')
                self.assertRegex(row,r'--hash=sha256:[a-f0-9]{64}')
                self.assertNotIn('http',row)

    def test_runtime_and_publication_requirements_agree_with_lock(self):
        self.assertTrue((ROOT/'requirements.lock').exists(),'resolved hash lock missing')
        lock=(ROOT/'requirements.lock').read_text().lower().replace('_','-')
        for file in ('requirements.txt','requirements-publication-checks.txt'):
            for row in (ROOT/file).read_text().splitlines():
                if '==' in row and not row.startswith('#'):
                    self.assertIn(row.strip().lower().replace('_','-')+' ',lock)

    def test_ci_and_publisher_require_distribution_hashes(self):
        for name in ('publish.yml','validate.yml','quality.yml'):
            text=(ROOT/'.github/workflows'/name).read_text()
            self.assertIn('--require-hashes -r requirements-build.lock',text)
            self.assertIn('--no-build-isolation -r requirements.lock',text)
            self.assertNotRegex(text,r'pip install -r requirements(?:\.txt|-publication)')
