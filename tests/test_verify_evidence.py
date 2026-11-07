"""End-to-end verification tests with real ephemeral TSA and Ed25519 signatures."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import observation
import test_release
import test_timestamp
import timestamp
import verify_evidence


class UnifiedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.root_tmp.name)
        cls.authority = test_timestamp.Authority(cls.root / 'authority')
        cls.policy = cls.root / 'trust.json'
        cls.policy.write_text(json.dumps(cls.authority.policy()), encoding='utf-8')
        cls.paper = test_release.ReleaseBundleTests()
        cls.paper.setUp()
        cls.paper.make_bundle()
        request = timestamp.make_query(cls.paper.bundle, timestamp.load_policy(cls.policy))
        request_file = cls.root / 'paper.tsq'
        response_file = cls.root / 'paper.tsr'
        request_file.write_bytes(request)
        cls.authority.sign(request_file, response_file)
        timestamp.attach(cls.paper.bundle, request, response_file.read_bytes(), timestamp.load_policy(cls.policy))
        cls.private_key = cls.root / 'observer.key'
        cls.public_key = cls.root / 'observer.pub'
        for cmd in (
            ['openssl', 'genpkey', '-algorithm', 'ED25519', '-out', str(cls.private_key)],
            ['openssl', 'pkey', '-in', str(cls.private_key), '-pubout', '-out', str(cls.public_key)],
        ):
            p = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=20)
            if p.returncode:
                raise RuntimeError(p.stderr)
        cls.key_hash = hashlib.sha256(cls.public_key.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.paper.tearDown()
        cls.root_tmp.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bundle = self.root / 'bundle'
        shutil.copytree(self.paper.bundle, self.bundle)
        self.witness = self.root / 'witness'
        self.downloaded = {p.name: p.read_bytes() for p in self.paper.bundle.iterdir()}

    def verify(self, scope='existence', **kw):
        return verify_evidence.verify_all(
            self.bundle, self.policy, 'example/science-paper', 'v1', scope, **kw,
        )

    def stamp_witness(self):
        def exchange(query):
            req = self.root / 'witness.tsq'
            resp = self.root / 'witness.tsr'
            req.write_bytes(query)
            self.authority.sign(req, resp)
            return resp.read_bytes()

        observation.record_public(
            'example/science-paper', 'v1', self.witness, self.policy,
            self.private_key, fetcher=lambda name: self.downloaded[name],
            stamp_observation=True, tsa_exchange=exchange,
        )

    def witness_args(self):
        return dict(witness=self.witness, public_key=self.public_key,
                    public_key_sha256=self.key_hash)

    def test_existence_scope_is_explicit_and_does_not_claim_public_access(self):
        result = self.verify('existence')
        self.assertEqual(result['verdict'], 'PASS')
        self.assertEqual(result['content_integrity'], 'VERIFIED')
        self.assertEqual(result['existence_time'], 'VERIFIED_BY_SELECTED_TSA')
        self.assertEqual(result['public_observation'], 'NOT_CHECKED')
        self.assertEqual(result['first_publication'], 'NOT_PROVEN')
        self.assertEqual(result['operator_independence'], 'NOT_VERIFIED')

    def test_paper_sha256_pin_is_enforced(self):
        with self.assertRaisesRegex(ValueError, 'paper'):
            self.verify('existence', expected_paper_sha256='0'*64)

    def test_expected_repository_and_version_must_match_metadata(self):
        with self.assertRaisesRegex(ValueError, 'source identity'):
            verify_evidence.verify_all(self.bundle, self.policy, 'other/paper', 'v1', 'existence')
        with self.assertRaisesRegex(ValueError, 'source identity'):
            verify_evidence.verify_all(self.bundle, self.policy, 'example/science-paper', 'v2', 'existence')

    def test_missing_timestamp_is_never_existence_pass(self):
        (self.bundle / 'timestamp.tsq').unlink()
        (self.bundle / 'timestamp.tsr').unlink()
        with self.assertRaises(ValueError):
            self.verify('existence')

    def test_stamped_witness_scope_binds_all_evidence(self):
        self.stamp_witness()
        result = self.verify('public-observation', **self.witness_args())
        self.assertEqual(result['verdict'], 'PASS')
        self.assertEqual(result['observation_timestamp'], 'VERIFIED')
        self.assertEqual(result['public_observation'], 'SIGNED_WITNESS_ASSERTION')
        self.assertEqual(result['first_publication'], 'NOT_PROVEN')
        self.assertEqual(result['operator_independence'], 'NOT_VERIFIED')

    def test_public_scope_requires_witness_and_independent_key(self):
        with self.assertRaises(ValueError):
            self.verify('public-observation')
        self.stamp_witness()
        with self.assertRaises(ValueError):
            self.verify('public-observation', witness=self.witness)

    def test_public_scope_rejects_wrong_witness_key_pin(self):
        self.stamp_witness()
        with self.assertRaisesRegex(ValueError, 'pin'):
            self.verify('public-observation', witness=self.witness,
                        public_key=self.public_key, public_key_sha256='0'*64)

    def test_public_scope_requires_timestamped_witness_receipt(self):
        observation.record_public(
            'example/science-paper', 'v1', self.witness, self.policy,
            self.private_key, fetcher=lambda name: self.downloaded[name],
        )
        with self.assertRaisesRegex(ValueError, 'timestamp is required'):
            self.verify('public-observation', **self.witness_args())

    def test_different_valid_timestamp_over_same_paper_is_not_same_release(self):
        self.stamp_witness()
        # The content manifest is unchanged, but a different valid timestamp
        # alters the Release evidence bytes. A public witness did not fetch those bytes.
        request = timestamp.make_query(self.bundle, timestamp.load_policy(self.policy))
        req = self.root / 'new.tsq'
        resp = self.root / 'new.tsr'
        req.write_bytes(request)
        self.authority.sign(req, resp)
        (self.bundle / 'timestamp.tsq').write_bytes(request)
        (self.bundle / 'timestamp.tsr').write_bytes(resp.read_bytes())
        with self.assertRaisesRegex(ValueError, 'different release bytes'):
            self.verify('public-observation', **self.witness_args())

    def test_scope_is_required_and_partial_observer_args_rejected(self):
        for bad in ('all', '', None):
            with self.assertRaises(ValueError):
                self.verify(bad)
        with self.assertRaises(ValueError):
            self.verify('existence', witness=self.root / 'other')

    def test_cli_requires_explicit_scope_and_expected_identity(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/verify_evidence.py')],
                                capture_output=True, text=True, timeout=15, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('--scope', result.stderr)


if __name__ == '__main__':
    unittest.main()
