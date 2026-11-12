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
        self.assertTrue(info['author_approved'])
        self.assertTrue(info['license_granted'])
        self.assertEqual(info['approved_version'], 'v1')
        self.assertEqual(info['approved_license'], 'CC-BY-4.0')
        self.assertEqual(info['approval_basis'], 'USER_CONFIRMED_2026_11_13_NOT_INDEPENDENT_ID_VERIFICATION')
        self.assertEqual(info['author_display_name'], 'Unjuno')
        self.assertTrue(info['unapproved_draft_rejected'])
        self.assertEqual(info['pdf_matches_markdown'], 'NOT_INDEPENDENTLY_PROVEN')

    def test_canonical_metadata_has_author_and_license_approval(self):
        import yaml
        meta=yaml.safe_load((SOURCE/'preprint.yaml').read_text('utf-8'))
        self.assertEqual(meta['authors'], [{'name':'Unjuno','orcid':None}])
        self.assertEqual(meta['license'], 'CC-BY-4.0')
        self.assertEqual(meta['version'], 'v1')

    def test_kit_root_is_still_an_unapproved_template(self):
        import yaml
        meta=yaml.safe_load((ROOT/'preprint.yaml').read_text('utf-8'))
        self.assertEqual(meta['version'],'v0')
        self.assertEqual(meta['license'],'UNSPECIFIED')

    def test_rights_notice_is_consistent_with_metadata(self):
        import yaml
        notice=(SOURCE/'LICENSE-NOTICE.txt').read_text('utf-8')
        self.assertIn('CC BY 4.0', notice)
        self.assertIn('Unjuno', notice)
        catalog=yaml.safe_load((SOURCE/'research-assets.yaml').read_text('utf-8'))
        for asset in catalog['public_assets']:
            if asset['role']=='supplementary':
                self.assertEqual(asset['license'],'CC-BY-4.0')

    def test_mislabeled_author_is_refused(self):
        manuscript=self.root/'different-author'
        shutil.copytree(SOURCE,manuscript)
        p=manuscript/'preprint.yaml'
        p.write_text(p.read_text('utf-8').replace('name: Unjuno','name: DifferentParty'),encoding='utf-8')
        result=self.execute(manuscript=manuscript)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('approved',result.stderr.lower())

    def test_mislabeled_license_is_refused(self):
        manuscript=self.root/'different-license'
        shutil.copytree(SOURCE,manuscript)
        p=manuscript/'preprint.yaml'
        p.write_text(p.read_text('utf-8').replace('CC-BY-4.0','CC-BY-NC-4.0'),encoding='utf-8')
        result=self.execute(manuscript=manuscript)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('approved',result.stderr.lower())

    def test_invalid_license_on_supplement_is_refused(self):
        manuscript=self.root/'bad-supplement-license'
        shutil.copytree(SOURCE,manuscript)
        p=manuscript/'research-assets.yaml'
        original=p.read_text('utf-8')
        self.assertIn('license: CC-BY-4.0',original)
        p.write_text(original.replace('license: CC-BY-4.0','license: CC-BY-NC-4.0',1),encoding='utf-8')
        result=self.execute(manuscript=manuscript)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('license',result.stderr.lower())

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


class ExportCandidateTests(unittest.TestCase):
    """The v1 manuscript candidate exported to TSA is the validated, exact self-application bundle."""

    def setUp(self):
        import test_release
        self.helper = test_release.ReleaseBundleTests()
        self.helper.setUp()
        self.addCleanup(self.helper.tearDown)
        self.helper.make_bundle()
        self.bundle = self.helper.bundle
        self.destination = self.helper.root / 'detached-candidate'
        sys.path.insert(0, str(ROOT / 'scripts'))
        import first_paper_selftest
        self.module = first_paper_selftest

    def test_exported_candidate_preserves_every_verified_byte(self):
        self.module.export_candidate(self.bundle, self.destination)
        self.assertEqual(
            {p.name: p.read_bytes() for p in self.bundle.iterdir()},
            {p.name: p.read_bytes() for p in self.destination.iterdir()},
        )
        from verify_release import verify
        self.assertEqual(verify(self.destination, None), [])

    def test_never_overwrites_a_preexisting_destination(self):
        self.destination.mkdir()
        important = self.destination / 'existing.txt'
        important.write_text('important old data', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.module.export_candidate(self.bundle, self.destination)
        self.assertEqual(important.read_text(encoding='utf-8'), 'important old data')

    def test_invalid_candidate_is_not_exported(self):
        (self.bundle / 'paper.pdf').write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'integrity'):
            self.module.export_candidate(self.bundle, self.destination)
        self.assertFalse(self.destination.exists())

    def test_symlinked_target_does_not_escape_or_get_overwritten(self):
        self.destination.symlink_to(self.helper.root)
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.module.export_candidate(self.bundle, self.destination)
        self.assertTrue(self.destination.is_symlink())

    def test_output_path_is_not_placed_under_the_source_bundle(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            self.module.export_candidate(self.bundle, self.bundle / 'export')


class FirstPaperLiveTimestampWorkflowTests(unittest.TestCase):
    def test_new_workflow_stamps_approved_metadata_and_verifies_in_fresh_runner(self):
        import yaml
        workflow = ROOT / '.github' / 'workflows' / 'first-paper-live-timestamp.yml'
        self.assertTrue(workflow.is_file())
        parsed = yaml.load(workflow.read_text('utf-8'), Loader=yaml.BaseLoader)
        self.assertEqual(parsed['permissions'], {'contents': 'read'})
        self.assertEqual(set(parsed['on']), {'push', 'workflow_dispatch'})
        self.assertEqual(parsed['on']['push']['branches'], ['main'])
        self.assertIn('first-paper-live-timestamp.yml', ' '.join(parsed['on']['push']['paths']))
        stamp = parsed['jobs']['stamp-v1']
        restore = parsed['jobs']['fresh-verify']
        self.assertEqual(restore['needs'], ['stamp-v1'])
        self.assertIn('timestamp.py stamp', str(stamp))
        self.assertIn('APPROVED_MANUSCRIPT_EXISTENCE_ONLY', str(stamp))
        self.assertIn('author_approved', str(stamp))
        self.assertIn('license_granted', str(stamp))
        self.assertIn('APPROVED_MANUSCRIPT_EXISTENCE_ONLY', str(restore))
        self.assertIn('timestamp.py verify', str(stamp))
        self.assertIn('preserve.py pack', str(stamp))
        self.assertIn("preservation['timestamp']=='VERIFIED'", str(stamp))
        self.assertNotIn("preservation['timestamp_verified']", str(stamp))
        self.assertIn('preserve.py restore', str(restore))
        self.assertIn('timestamp.py verify', str(restore))
        self.assertIn('download-artifact@', str(restore))
        self.assertNotIn('contents: write', workflow.read_text('utf-8'))
        self.assertNotIn('gh release create', workflow.read_text('utf-8'))
        self.assertNotIn('GH_TOKEN', workflow.read_text('utf-8'))
        for job in parsed['jobs'].values():
            self.assertLessEqual(int(job['timeout-minutes']), 15)
            for step in job['steps']:
                if 'uses' in step:
                    self.assertRegex(step['uses'], r'@[0-9a-f]{40}$')
                if 'run' in step:
                    self.assertNotIn('$'+'{{', step['run'])


if __name__ == '__main__':
    unittest.main()
