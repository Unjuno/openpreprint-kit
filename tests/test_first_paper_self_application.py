"""The first actual OPK manuscript is its own bounded, non-publishing smoke test."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

from pypdf import PdfWriter

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'first_paper_selftest.py'
SOURCE = ROOT / 'manuscripts' / 'openpreprint-kit'


class FirstPaperSelfApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.pdf = self.root / 'draft.pdf'
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        with self.pdf.open('wb') as stream:
            writer.write(stream)

    def execute(self, manuscript=SOURCE, report=None, pdf=None):
        cmd = [sys.executable, str(SCRIPT), '--manuscript', str(manuscript),
               '--paper-pdf', str(pdf or self.pdf)]
        if report is not None:
            cmd += ['--report', str(report)]
        return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=60)

    def test_first_actual_manuscript_local_pass_includes_four_negative_controls(self):
        result = self.execute()
        self.assertEqual(result.returncode, 0, result.stderr)
        info = json.loads(result.stdout)
        self.assertEqual(info['verdict'], 'PASS')
        self.assertEqual(info['scope'], 'LOCAL_SELF_APPLICATION_ONLY')
        self.assertEqual(info['baseline_tests'], 274)
        self.assertEqual(info['public_research_assets'], 7)
        self.assertEqual(len(info['negative_cases']), 4)
        self.assertTrue(all(info['negative_cases'].values()))
        self.assertFalse(info['timestamp_verified'])
        self.assertFalse(info['release_published'])
        self.assertFalse(info['author_approved'])
        self.assertFalse(info['license_granted'])
        self.assertEqual(info['pdf_matches_markdown'], 'NOT_INDEPENDENTLY_PROVEN')

    def test_workflow_generates_actual_manuscript_pdf_without_publishing(self):
        workflow = ROOT / '.github' / 'workflows' / 'first-paper-selftest.yml'
        self.assertTrue(workflow.is_file(), 'first paper must be tested with a real typeset PDF in CI')
        content = workflow.read_text('utf-8')
        self.assertIn('pandoc manuscripts/openpreprint-kit/paper.md', content)
        self.assertIn('scripts/first_paper_selftest.py', content)
        self.assertIn('SOURCE_DATE_EPOCH', content)
        self.assertIn('contents: read', content)
        self.assertIn('persist-credentials: false', content)
        self.assertNotIn('contents: write', content)
        self.assertNotIn('gh release create', content)
        self.assertNotIn('GH_TOKEN', content)

    def test_workflow_explicitly_installs_pandoc_required_lmodern_style(self):
        workflow = ROOT / '.github' / 'workflows' / 'first-paper-selftest.yml'
        content = workflow.read_text('utf-8')
        self.assertIn(' lmodern', content,
                      'XeLaTeX needs lmodern.sty; --no-install-recommends skips the required Ubuntu package')

    def test_workflow_installs_xecjk_japanese_typesetting_package(self):
        workflow = ROOT / '.github' / 'workflows' / 'first-paper-selftest.yml'
        content = workflow.read_text('utf-8')
        self.assertIn(' texlive-lang-cjk', content,
                      'Ubuntu 24.04 needs texlive-lang-cjk for xeCJK.sty')

    def test_workflow_installs_ctexhook_dependency(self):
        workflow = ROOT / '.github' / 'workflows' / 'first-paper-selftest.yml'
        content = workflow.read_text('utf-8')
        self.assertIn(' texlive-lang-chinese', content,
                      'Ubuntu 24.04 places ctexhook.sty in texlive-lang-chinese')

    def test_workflow_installs_pzdr_font_metrics(self):
        workflow = ROOT / '.github' / 'workflows' / 'first-paper-selftest.yml'
        content = workflow.read_text('utf-8')
        self.assertIn(' texlive-fonts-recommended', content,
                      'Ubuntu 24.04 needs TeX zapfding/pzdr font metrics')

    def test_does_not_replace_existing_report(self):
        output = self.root / 'existing.json'
        output.write_text('important existing evidence', encoding='utf-8')
        result = self.execute(report=output)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_text(encoding='utf-8'), 'important existing evidence')

    def test_modified_retained_log_is_refused(self):
        manuscript = self.root / 'manuscript'
        shutil.copytree(SOURCE, manuscript)
        log = manuscript / 'data' / 'baseline-ci.txt.gz'
        log.write_bytes(log.read_bytes()[:-1]+b'X')
        result = self.execute(manuscript=manuscript)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('hash', result.stderr.lower())

    def test_generated_python_bytecode_is_not_mistaken_for_public_research(self):
        manuscript = self.root / 'working-manuscript'
        shutil.copytree(SOURCE, manuscript)
        cache = manuscript / 'analysis' / '__pycache__'
        cache.mkdir(exist_ok=True)
        (cache / 'temporary.cpython-313.pyc').write_bytes(b'ephemeral python bytecode')
        result = self.execute(manuscript=manuscript)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['public_research_assets'], 7)

    def test_missing_pdf_is_refused(self):
        result = self.execute(pdf=self.root / 'absent.pdf')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('PASS', result.stdout)

    def test_symlink_pdf_is_refused(self):
        link = self.root / 'link.pdf'
        link.symlink_to(self.pdf)
        result = self.execute(pdf=link)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('symlink', result.stderr.lower())


if __name__ == '__main__':
    unittest.main()
