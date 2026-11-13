"""Post-publication recovery: real RFC3161 crypto, simulated GitHub transport.

These are not external publication/independence claims. All operations must be
read-only even when earlier publication completed but its verification failed.
"""
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_release
import test_research_package
import test_timestamp
from test_pilot import FakeGitHub

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import timestamp
from preserve import pack


def publisher():
    return importlib.import_module('first_paper_publish')


class PublicationRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.tmp.name)
        cls.authority = test_timestamp.Authority(cls.base / 'authority')
        cls.policy = cls.base / 'policy.json'
        cls.policy.write_text(json.dumps(cls.authority.policy()), encoding='utf-8')
        cls.helper = test_research_package.ResearchBundleTests()
        cls.helper.setUp()
        cls.helper.make_bundle()
        policy = timestamp.load_policy(cls.policy)
        query = timestamp.make_query(cls.helper.bundle, policy)
        q, r = cls.base / 'query.tsq', cls.base / 'response.tsr'
        q.write_bytes(query)
        cls.authority.sign(q, r)
        timestamp.attach(cls.helper.bundle, query, r.read_bytes(), policy)
        cls.archive = cls.base / 'evidence.opk.zip'
        cls.archive_sha = pack(cls.helper.bundle, cls.archive, cls.policy)['archive_sha256']

    @classmethod
    def tearDownClass(cls):
        cls.helper.tearDown()
        cls.tmp.cleanup()

    def setUp(self):
        self.tmp_case = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_case.cleanup)
        self.root = Path(self.tmp_case.name)
        self.repository = 'example/science-paper'
        self.gateway = FakeGitHub(self.root)
        self.gateway.repos[self.repository] = {
            'full_name': self.repository, 'private': False,
            'default_branch': 'main', 'head': 'a' * 40, 'immutable': True,
        }
        from source_provenance import expected_source_files
        self.gateway.sources[(self.repository, 'a' * 40)] = expected_source_files(self.helper.bundle)
        self.gateway.releases[(self.repository, 'v1')] = {
            'id': 1, 'draft': False, 'commit': 'a' * 40,
            'assets': {p.name: p.read_bytes() for p in self.helper.bundle.iterdir()},
        }
        self.out = self.root / 'verification'

    def run_verification(self, **kwargs):
        fn = getattr(publisher(), 'verify_existing', None)
        self.assertTrue(callable(fn), 'read-only post-publication verification must exist')
        options = dict(repository=self.repository, archive=self.archive,
                       archive_sha256=self.archive_sha, policy_path=self.policy,
                       output=self.out, gateway=self.gateway)
        options.update(kwargs)
        return fn(**options)

    def assert_read_only(self):
        for call in self.gateway.calls:
            self.assertNotIn(call[0], ('POST', 'PATCH', 'PUT', 'DELETE'))
            if call[0] == 'gh':
                self.assertIn(call[1:3], (('release', 'verify'), ('release', 'verify-asset')))

    def test_verified_archive_recovers_without_write_or_new_timestamp(self):
        with patch('timestamp.post_query', side_effect=AssertionError('must not reissue')):
            result = self.run_verification()
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['scope'], 'READ_ONLY_PUBLICATION_VERIFICATION')
        self.assertFalse(result['publication_performed'])
        self.assertEqual(result['independent_witness'], 'NOT_PERFORMED')
        self.assertTrue((self.out / 'verification-report.json').is_file())
        self.assert_read_only()

    def test_wrong_archive_pin_fails_before_network(self):
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            self.run_verification(archive_sha256='0' * 64)
        self.assertEqual(self.gateway.calls, [])

    def test_existing_output_is_not_overwritten(self):
        self.out.mkdir(); (self.out / 'keep').write_text('old evidence')
        with self.assertRaisesRegex(ValueError, 'new|exist'):
            self.run_verification()
        self.assertEqual((self.out / 'keep').read_text(), 'old evidence')
        self.assertEqual(self.gateway.calls, [])

    def test_tag_target_must_match_time_stamped_source_commit(self):
        self.gateway.releases[(self.repository, 'v1')]['commit'] = 'b' * 40
        with self.assertRaisesRegex(ValueError, 'tag.*commit|commit.*tag'):
            self.run_verification()
        self.assert_read_only()

    def test_private_repository_is_not_a_publication_success(self):
        self.gateway.repos[self.repository]['private'] = True
        with self.assertRaisesRegex(ValueError, 'public'):
            self.run_verification()
        self.assert_read_only()

    def test_duplicate_asset_inventory_is_rejected(self):
        api = self.gateway.api
        def duplicate(method, path, *args, **kwargs):
            result = api(method, path, *args, **kwargs)
            if '/releases/tags/' in path and result:
                result['assets'].append(dict(result['assets'][0]))
            return result
        with patch.object(self.gateway, 'api', side_effect=duplicate):
            with self.assertRaisesRegex(ValueError, 'asset'):
                self.run_verification()
        self.assert_read_only()

    def test_anonymous_byte_substitution_cannot_be_pass(self):
        self.gateway.releases[(self.repository, 'v1')]['assets']['paper.pdf'] += b'CORRUPT'
        with self.assertRaises(ValueError):
            self.run_verification()
        info = json.loads((self.out / 'verification-report.json').read_text())
        self.assertEqual(info['status'], 'FAIL')
        self.assert_read_only()

    def test_delayed_attestation_can_be_rechecked_without_republication(self):
        self.gateway.fail_attestation = True
        with self.assertRaisesRegex(ValueError, 'attestation'):
            self.run_verification()
        failed = (self.out / 'verification-report.json').read_bytes()
        self.gateway.fail_attestation = False
        result = self.run_verification(output=self.root / 'second-verification')
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(failed, (self.out / 'verification-report.json').read_bytes())
        self.assertFalse(self.gateway.releases[(self.repository, 'v1')]['draft'])
        self.assert_read_only()

    def test_published_paper_is_rejected_if_tag_source_has_different_pdf(self):
        source = self.gateway.sources[(self.repository, 'a' * 40)]
        source['paper/paper.pdf'] = b'DIFFERENT_SOURCE_PAPER'
        with self.assertRaisesRegex(ValueError, 'paper/paper.pdf'):
            self.run_verification()
        self.assertEqual(json.loads((self.out / 'verification-report.json').read_text())['status'], 'FAIL')
        self.assert_read_only()

    def test_published_paper_is_rejected_if_source_analysis_is_different(self):
        # The first-paper acceptance bundle contains analysis code; a release
        # can be internally sound and still lie about its Git source commit.
        self.assertTrue(any(path.startswith('analysis/') for path in
                            self.gateway.sources[(self.repository, 'a' * 40)]))
        source = self.gateway.sources[(self.repository, 'a' * 40)]
        target = next(path for path in sorted(source) if path.startswith('analysis/'))
        source[target] = b'DIFFERENT_ANALYSIS_CODE'
        with self.assertRaisesRegex(ValueError, target):
            self.run_verification()
        self.assert_read_only()

    def test_missing_published_release_is_failure_not_new_publication(self):
        self.gateway.releases.clear()
        with self.assertRaisesRegex(ValueError, 'Release|release'):
            self.run_verification()
        self.assert_read_only()

    def test_archive_is_created_before_public_promotion(self):
        text = (ROOT / 'scripts/first_paper_publish.py').read_text()
        promotion = text.index("report['state'] = 'PROMOTION_REQUESTED'")
        self.assertLess(text.index('packed = pack('), promotion,
                        'a post-publication failure must already have portable recovery evidence')

    def test_template_origin_is_checked_before_real_creation(self):
        self.assertTrue(callable(getattr(publisher(), 'require_template_origin', None)),
                        'template origin/readback guard missing')
        repo = {'full_name': 'example/kit', 'private': False, 'is_template': False}
        with self.assertRaisesRegex(ValueError, 'template'):
            publisher().require_template_origin(repo, 'example/kit')
        repo['is_template'] = True
        publisher().require_template_origin(repo, 'example/kit')

    def test_creator_uses_template_without_mutating_the_toolkit(self):
        text = (ROOT / 'scripts/first_paper_publish.py').read_text()
        self.assertIn("'--template', template", text)
        self.assertIn('template_repository', text)
        self.assertNotIn("gateway.api('PATCH', 'repos/' + template", text)


if __name__ == '__main__':
    unittest.main()
