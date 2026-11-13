"""Approved first paper publication: mock GitHub transport, never fake public success."""
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pdf_fixture import write_pdf
from test_pilot import FakeGitHub
import test_timestamp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
SCRIPT = ROOT / 'scripts/first_paper_publish.py'


def module():
    return importlib.import_module('first_paper_publish')


class FirstPaperPublishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.authority_temp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.authority_temp.name)
        cls.authority = test_timestamp.Authority(cls.base / 'tsa')
        cls.policy = cls.base / 'policy.json'
        cls.policy.write_text(json.dumps(cls.authority.policy()))

    @classmethod
    def tearDownClass(cls):
        cls.authority_temp.cleanup()

    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), 'approved first-paper publication entry point is missing')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pdf = self.root / 'paper.pdf'
        write_pdf(self.pdf)
        self.gateway = FakeGitHub(self.root)
        self.gateway.template['is_template'] = True
        self.output = self.root / 'publication'
        import hashlib
        self.fingerprint = hashlib.sha256(self.pdf.read_bytes()).hexdigest()

    def tsa(self, url, query, timeout):
        with tempfile.TemporaryDirectory() as d:
            q, r = Path(d)/'query.tsq', Path(d)/'reply.tsr'
            q.write_bytes(query)
            self.authority.sign(q, r)
            return r.read_bytes()

    def execute(self, **kwargs):
        with patch('timestamp.post_query', side_effect=self.tsa):
            return module().execute('example/kit', 'example/opk-first-paper',
                self.pdf, self.fingerprint, self.policy, self.output,
                gateway=self.gateway, **kwargs)

    def test_default_plan_has_no_network_or_side_effects(self):
        with patch('subprocess.run', side_effect=AssertionError('no subprocess allowed')):
            report = module().plan('example/kit', 'example/opk-first-paper')
        self.assertFalse(report['publication_performed'])
        self.assertEqual(report['mode'], 'PLAN_ONLY')
        self.assertEqual(report['version'], 'v1')

    def test_forbidden_destinations(self):
        for dest in ('example/kit', 'EXAMPLE/KIT', 'https://github.com/example/paper', 'bad name/paper'):
            with self.subTest(dest=dest), self.assertRaises(ValueError):
                module().plan('example/kit', dest)

    def test_existing_output_untouched(self):
        self.output.mkdir()
        (self.output/'keep').write_text('previous evidence')
        with self.assertRaises(ValueError): self.execute()
        self.assertEqual((self.output/'keep').read_text(), 'previous evidence')
        self.assertEqual(self.gateway.calls, [])

    def test_wrong_pdf_pin_stops_before_any_network(self):
        self.fingerprint = '0'*64
        with self.assertRaisesRegex(ValueError, 'fingerprint'): self.execute()
        self.assertEqual(self.gateway.calls, [])

    def test_pdf_symlink_rejected(self):
        linked = self.root/'linked.pdf'; linked.symlink_to(self.pdf); self.pdf=linked
        with self.assertRaisesRegex(ValueError, 'symlink'): self.execute()
        self.assertEqual(self.gateway.calls, [])

    def test_existing_repository_never_modified(self):
        self.gateway.repos['example/opk-first-paper']={'full_name':'example/opk-first-paper'}
        with self.assertRaisesRegex(ValueError, 'already exists'): self.execute()
        self.assertFalse(any(c[0] in ('PATCH','PUT','POST') for c in self.gateway.calls))

    def test_immutable_setting_failure_stops_release(self):
        self.gateway.disable_immutable=True
        with self.assertRaisesRegex(ValueError, 'immutable'): self.execute()
        self.assertEqual(self.gateway.releases, {})

    def test_success_binds_real_manuscript_data_and_source_commit(self):
        report=self.execute()
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual(report['state'], 'VERIFIED_PUBLIC_PREPRINT')
        self.assertFalse(report['synthetic_only'])
        self.assertEqual(report['paper_sha256'],self.fingerprint)
        self.assertEqual(report['author_display_name'],'Unjuno')
        self.assertEqual(report['license'],'CC-BY-4.0')
        self.assertEqual(report['independent_witness'],'NOT_PERFORMED')
        self.assertEqual(report['production_readiness'],'NOT_ESTABLISHED')
        release=self.gateway.releases[('example/opk-first-paper','v1')]
        metadata=json.loads(release['assets']['preprint-metadata.json'])
        self.assertEqual(metadata['source_claim']['repository'],'example/opk-first-paper')
        self.assertEqual(metadata['source_claim']['commit'],report['source_commit'])
        self.assertEqual(metadata['authors'],[{'name':'Unjuno','orcid':None}])
        self.assertTrue(report['restore_byte_equality'])
        self.assertEqual(len(release['assets']),11)
        self.assertTrue((self.output/'first-paper.opk.zip').is_file())
        self.assertFalse(any('--prerelease' in c for c in self.gateway.calls))

    def test_corrupt_draft_never_promoted(self):
        self.gateway.corrupt_draft=True
        with self.assertRaisesRegex(ValueError,'bytes differ'): self.execute()
        self.assertTrue(self.gateway.releases[('example/opk-first-paper','v1')]['draft'])
        self.assertFalse(any(c[:3]==('gh','release','edit') for c in self.gateway.calls))

    def test_attestation_failure_preserves_public_pending_state(self):
        self.gateway.fail_attestation=True
        with self.assertRaisesRegex(ValueError,'attestation'): self.execute()
        report=json.loads((self.output/'publication-report.json').read_text())
        self.assertEqual(report['status'],'FAIL')
        self.assertEqual(report['state'],'PUBLIC_VERIFICATION_PENDING')
        self.assertFalse(self.gateway.releases[('example/opk-first-paper','v1')]['draft'])
        self.assertFalse(report['rollback_performed'])
        self.assertTrue((self.output/'first-paper.opk.zip').is_file())
        self.assertEqual(len(report['archive_sha256']), 64)

    def test_published_paper_proves_anonymous_source_bytes_match_versioned_bundle(self):
        report = self.execute()
        self.assertEqual(report['source_snapshot']['source_snapshot'], 'VERIFIED_PUBLIC_GIT_BYTES')
        self.assertIn('paper/paper.pdf', report['source_snapshot']['checked_paths'])
        self.assertIn('analysis/summarize_ci.py', report['source_snapshot']['checked_paths'])

    def test_wrong_public_git_source_blocks_public_promotion(self):
        self.gateway.corrupt_source = True
        with self.assertRaisesRegex(ValueError, 'paper/paper.pdf'):
            self.execute()
        # A prepublication draft is expected; the safety invariant is that
        # invalid source bytes never reach a *public* immutable Release.
        draft = self.gateway.releases[('example/opk-first-paper', 'v1')]
        self.assertTrue(draft['draft'])
        report = json.loads((self.output / 'publication-report.json').read_text())
        self.assertEqual(report['status'], 'FAIL')
        self.assertEqual(report['state'], 'DRAFT_CREATED')
        self.assertFalse(any(c[:3] == ('gh','release','edit') for c in self.gateway.calls))

    def test_only_declared_paper_files_are_uploaded(self):
        self.execute()
        blobs=[c for c in self.gateway.calls if c[:2]==('POST','repos/example/opk-first-paper/git/trees')]
        self.assertEqual(len(blobs),1)
        names={entry['path'] for entry in blobs[0][2]['tree']}
        self.assertIn('paper/paper.pdf',names)
        self.assertIn('data/baseline-ci.txt.gz',names)
        self.assertIn('analysis/summarize_ci.py',names)
        self.assertNotIn('timestamp-policy.json',names)
        self.assertNotIn('trust/ca.pem',names)
        self.assertFalse(any('key' in p or 'private' in p for p in names))
