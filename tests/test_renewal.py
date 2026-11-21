"""Forward-only timestamp reattestation with real ephemeral OpenSSL TSA crypto.

Network transport is stubbed; TSA signing, CMS signature/chain/CRL/nonce/policy
verification and preservation ZIP roundtrips are not mocked.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

import test_release
import test_timestamp

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'renewal.py'
sys.path.insert(0, str(ROOT / 'scripts'))


class RenewalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='opk-renewal-tests-')
        cls.root = Path(cls.temp.name)
        cls.source_authority = test_timestamp.Authority(cls.root / 'old-authority')
        cls.new_authority_1 = test_timestamp.Authority(cls.root / 'new-authority-1')
        cls.new_authority_2 = test_timestamp.Authority(cls.root / 'new-authority-2')
        cls.builder = test_release.ReleaseBundleTests()
        cls.builder.setUp()
        cls.builder.make_bundle()
        cls.source_policy = cls.root / 'source-policy.json'
        cls.source_policy.write_text(json.dumps(cls.source_authority.policy()))
        cls.policy1 = cls.root / 'renew-policy-1.json'
        p1 = cls.new_authority_1.policy(); p1['tsa_url'] = 'https://tsa1.example.invalid/tsr'
        cls.policy1.write_text(json.dumps(p1))
        cls.policy2 = cls.root / 'renew-policy-2.json'
        p2 = cls.new_authority_2.policy(); p2['tsa_url'] = 'https://tsa2.example.invalid/tsr'
        cls.policy2.write_text(json.dumps(p2))
        q = cls.root / 'source.tsq'; r = cls.root / 'source.tsr'
        for args in (
            ('request', str(cls.builder.bundle), '--policy', str(cls.source_policy), '--out', str(q)),
        ):
            outcome = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'timestamp.py'), *args],
                                     capture_output=True, text=True, timeout=45)
            if outcome.returncode: raise RuntimeError(outcome.stderr)
        cls.source_authority.sign(q, r)
        outcome = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'timestamp.py'),
                                  'attach', str(cls.builder.bundle), '--policy', str(cls.source_policy),
                                  '--query', str(q), '--response', str(r)],
                                 capture_output=True, text=True, timeout=45)
        if outcome.returncode: raise RuntimeError(outcome.stderr)
        cls.archive = cls.root / 'source.opk.zip'
        outcome = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'preserve.py'), 'pack',
                                  str(cls.builder.bundle), '--out', str(cls.archive),
                                  '--policy', str(cls.source_policy)],
                                 capture_output=True, text=True, timeout=45)
        if outcome.returncode: raise RuntimeError(outcome.stderr)
        cls.archive_sha = hashlib.sha256(cls.archive.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.builder.tearDown()
        cls.temp.cleanup()

    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix='opk-renewal-case-')
        self.addCleanup(self.scratch.cleanup)
        self.work = Path(self.scratch.name)
        self.output = self.work / 'chain'
        self.recorded_requests = []

    def module(self):
        self.assertTrue(SCRIPT.is_file(), 'renewal implementation is missing')
        import renewal
        return renewal

    def responder(self, authority):
        def post(url, request, timeout):
            self.recorded_requests.append(url)
            with tempfile.TemporaryDirectory(prefix='opk-renew-response-') as tmp:
                q = Path(tmp) / 'request.tsq'; r = Path(tmp) / 'response.tsr'
                q.write_bytes(request)
                authority.sign(q, r)
                return r.read_bytes()
        return post

    def first(self):
        m = self.module()
        return m.issue_chain(self.archive, self.archive_sha, self.source_policy,
                             self.policy1, 'example/science-paper', 'v1', self.output,
                             post=self.responder(self.new_authority_1))

    def second(self):
        m = self.module()
        prior = self.first()
        output2 = self.work / 'chain2'
        result = m.issue_chain(self.archive, self.archive_sha, self.source_policy,
                               self.policy2, 'example/science-paper', 'v1', output2,
                               prior_chain=self.output, prior_sha256=prior['chain_sha256'],
                               prior_policies=[self.policy1],
                               post=self.responder(self.new_authority_2))
        return result, output2

    def verify(self, chain, pin, policies):
        return self.module().verify_chain(
            self.archive, self.archive_sha, self.source_policy, chain, pin,
            policies, 'example/science-paper', 'v1')

    def test_renewal_entrypoint_and_api_are_available(self):
        self.assertTrue(SCRIPT.is_file(), 'expected scripts/renewal.py entrypoint')
        self.assertTrue(hasattr(self.module(), 'issue_chain'))

    def test_signed_single_step_is_bound_to_exact_public_archive(self):
        result = self.first()
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['steps'], 1)
        self.assertEqual(len(self.recorded_requests), 1)
        self.assertEqual(result['archive_sha256'], self.archive_sha)
        self.assertFalse((self.output / 'source.opk.zip').exists())
        self.assertEqual(self.verify(self.output, result['chain_sha256'], [self.policy1])['steps'], 1)
        self.assertEqual(self.verify(self.output, result['chain_sha256'], [self.policy1])['historical_ltv'], 'NOT_ESTABLISHED')

    def test_two_real_distinct_tsa_roots_and_previous_digest(self):
        result, chain = self.second()
        self.assertEqual(result['steps'], 2)
        self.assertEqual(len(self.recorded_requests), 2)
        report = self.verify(chain, result['chain_sha256'], [self.policy1, self.policy2])
        self.assertEqual(report['status'], 'PASS')
        statement2 = json.loads((chain / 'step-0002' / 'statement.json').read_text(encoding='utf-8'))
        first_pin = self.module().step_digest(self.output / 'step-0001')
        self.assertEqual(statement2['previous_step_sha256'], first_pin)
        self.assertEqual(report['tsa_policies'], ['1.2.3.4.1', '1.2.3.4.1'])

    def test_wrong_pin_and_wrong_archive_are_rejected(self):
        result = self.first()
        with self.assertRaises(ValueError): self.verify(self.output, '0'*64, [self.policy1])
        with self.assertRaises(ValueError):
            self.module().verify_chain(self.archive, 'f'*64, self.source_policy,
                                       self.output, result['chain_sha256'], [self.policy1],
                                       'example/science-paper', 'v1')

    def test_statement_and_timestamp_mutation_rejected(self):
        result = self.first()
        for name in ('statement.json', 'timestamp.tsq', 'timestamp.tsr'):
            path = self.output / 'step-0001' / name
            old = path.read_bytes()
            path.write_bytes(old + b'altered')
            with self.assertRaises(ValueError, msg=name): self.verify(self.output, result['chain_sha256'], [self.policy1])
            path.write_bytes(old)

    def test_truncated_or_reordered_chain_rejected(self):
        result, chain = self.second()
        shutil.rmtree(chain / 'step-0001')
        with self.assertRaises(ValueError): self.verify(chain, result['chain_sha256'], [self.policy1, self.policy2])

    def test_wrong_second_policy_rejected(self):
        result, chain = self.second()
        with self.assertRaises(ValueError): self.verify(chain, result['chain_sha256'], [self.policy1, self.policy1])

    def test_wrong_source_identity_rejected_before_post(self):
        with self.assertRaises(ValueError):
            self.module().issue_chain(self.archive, self.archive_sha, self.source_policy,
                self.policy1, 'example/other-paper', 'v1', self.output,
                post=self.responder(self.new_authority_1))
        self.assertFalse(self.recorded_requests)
        self.assertFalse(self.output.exists())

    def test_prior_requires_external_sha_pin_and_policy(self):
        self.first()
        output2 = self.work / 'chain2'
        with self.assertRaises(ValueError):
            self.module().issue_chain(self.archive, self.archive_sha, self.source_policy,
                self.policy2, 'example/science-paper', 'v1', output2,
                prior_chain=self.output, post=self.responder(self.new_authority_2))
        self.assertFalse(output2.exists())

    def test_failed_tsa_reply_never_installs_partial_evidence(self):
        with self.assertRaises(ValueError):
            self.module().issue_chain(self.archive, self.archive_sha, self.source_policy,
                self.policy1, 'example/science-paper', 'v1', self.output,
                post=lambda *_: b'not a valid TSA reply')
        self.assertFalse(self.output.exists())

    def test_existing_destination_is_never_overwritten(self):
        self.output.mkdir(); (self.output / 'important').write_text('keep')
        with self.assertRaises(ValueError): self.first()
        self.assertEqual((self.output / 'important').read_text(encoding='utf-8'), 'keep')
        self.assertFalse(self.recorded_requests)

    def test_unknown_files_and_links_rejected(self):
        result = self.first()
        (self.output / 'private.key').write_text('never in public evidence')
        with self.assertRaises(ValueError): self.verify(self.output, result['chain_sha256'], [self.policy1])
        (self.output / 'private.key').unlink()
        (self.output / 'step-0001' / 'timestamp.tsq').unlink()
        try:
            (self.output / 'step-0001' / 'timestamp.tsq').symlink_to(self.source_policy)
        except OSError as exc:
            if os.name == 'nt' and getattr(exc, 'winerror', None) == 1314:
                self.skipTest('Windows symlink privilege unavailable')
            raise
        with self.assertRaises(ValueError): self.verify(self.output, result['chain_sha256'], [self.policy1])

    def test_issuer_never_accepts_missing_or_untrusted_source_timestamp(self):
        invalid = self.work / 'bad.zip'
        invalid.write_bytes(b'fake archive')
        with self.assertRaises(ValueError):
            self.module().issue_chain(invalid, hashlib.sha256(invalid.read_bytes()).hexdigest(),
                self.source_policy, self.policy1, 'example/science-paper', 'v1', self.output,
                post=self.responder(self.new_authority_1))
        self.assertFalse(self.recorded_requests)

    def test_revoked_origin_evidence_is_preserved_but_never_renewed(self):
        """Keep the old proof bytes, but fail closed once its signer is revoked."""
        authority = test_timestamp.Authority(self.work / 'revoked-source-authority')
        source_policy = self.work / 'revoked-source-policy.json'
        source_policy.write_text(json.dumps(authority.policy()), encoding='utf-8')
        builder = test_release.ReleaseBundleTests()
        builder.setUp()
        self.addCleanup(builder.tearDown)
        builder.make_bundle()
        bundle = builder.bundle

        query = self.work / 'revoked-source.tsq'
        response = self.work / 'revoked-source.tsr'
        requested = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'timestamp.py'), 'request',
             str(bundle), '--policy', str(source_policy), '--out', str(query)],
            capture_output=True, text=True, timeout=45)
        self.assertEqual(requested.returncode, 0, requested.stderr)
        authority.sign(query, response)
        attached = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'timestamp.py'), 'attach',
             str(bundle), '--policy', str(source_policy), '--query', str(query),
             '--response', str(response)],
            capture_output=True, text=True, timeout=45)
        self.assertEqual(attached.returncode, 0, attached.stderr)

        archive = self.work / 'revoked-source.opk.zip'
        packed = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'preserve.py'), 'pack',
             str(bundle), '--out', str(archive), '--policy', str(source_policy)],
            capture_output=True, text=True, timeout=45)
        self.assertEqual(packed.returncode, 0, packed.stderr)
        archive_before = archive.read_bytes()
        response_before = (bundle / 'timestamp.tsr').read_bytes()
        archive_sha = hashlib.sha256(archive_before).hexdigest()

        test_timestamp.ssl('ca', '-batch', '-config', authority.config,
                           '-revoke', authority.root / 'tsa.pem')
        authority.make_crl()
        test_timestamp.ssl('crl', '-in', authority.crl, '-noout', '-verify',
                           '-CAfile', authority.ca)

        verification = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'timestamp.py'), 'verify',
             str(bundle), '--policy', str(source_policy)],
            capture_output=True, text=True, timeout=45)
        self.assertNotEqual(verification.returncode, 0, 'revoked signer was accepted')

        restored = self.work / 'revoked-source-restored'
        restore = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'preserve.py'), 'restore',
             str(archive), '--out', str(restored), '--expected-sha256', archive_sha,
             '--policy', str(source_policy)],
            capture_output=True, text=True, timeout=45)
        self.assertNotEqual(restore.returncode, 0, 'revoked source archive restored as valid')
        self.assertFalse(restored.exists(), 'failed restore left a partial output')

        renewal_requests = []

        def unexpected_tsa_request(*args):
            renewal_requests.append(args)
            raise AssertionError('TSA must not be contacted for revoked source evidence')

        with self.assertRaises(ValueError):
            self.module().issue_chain(
                archive, archive_sha, source_policy, self.policy1,
                'example/science-paper', 'v1', self.output,
                post=unexpected_tsa_request)
        self.assertFalse(renewal_requests)
        self.assertFalse(self.output.exists(), 'failed renewal left partial evidence')
        self.assertEqual(archive.read_bytes(), archive_before,
                         'the original preservation archive must remain byte-identical')
        self.assertEqual((bundle / 'timestamp.tsr').read_bytes(), response_before,
                         'the original RFC 3161 response must remain preserved')

    def test_git_hub_release_zip_roundtrip_is_byte_exact(self):
        result = self.first()
        package = self.work / 'renewal-evidence.zip'
        packed = self.module().pack_chain(
            self.archive, self.archive_sha, self.source_policy,
            self.output, result['chain_sha256'], [self.policy1],
            'example/science-paper', 'v1', package)
        self.assertEqual(packed['status'], 'PASS')
        self.assertEqual(packed['package_sha256'], hashlib.sha256(package.read_bytes()).hexdigest())
        unpacked = self.work / 'recovered'
        report = self.module().restore_chain(
            self.archive, self.archive_sha, self.source_policy,
            package, packed['package_sha256'], result['chain_sha256'],
            [self.policy1], 'example/science-paper', 'v1', unpacked)
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual(report['steps'], 1)
        self.assertEqual((unpacked / 'step-0001' / 'statement.json').read_bytes(),
                         (self.output / 'step-0001' / 'statement.json').read_bytes())

    def test_package_wrong_external_pin_rejected_without_output(self):
        result = self.first()
        package = self.work / 'renewal-evidence.zip'
        packed = self.module().pack_chain(
            self.archive, self.archive_sha, self.source_policy,
            self.output, result['chain_sha256'], [self.policy1],
            'example/science-paper', 'v1', package)
        with self.assertRaises(ValueError):
            self.module().restore_chain(
                self.archive, self.archive_sha, self.source_policy, package,
                '0'*64, result['chain_sha256'], [self.policy1],
                'example/science-paper', 'v1', self.work / 'recovered')
        self.assertFalse((self.work / 'recovered').exists())

    def test_package_extra_traversal_and_duplicate_members_rejected(self):
        result = self.first()
        package = self.work / 'evidence.zip'
        self.module().pack_chain(self.archive, self.archive_sha, self.source_policy,
                                 self.output, result['chain_sha256'], [self.policy1],
                                 'example/science-paper', 'v1', package)
        original = package.read_bytes()
        for name in ('../escape', 'step-0001/statement.json', 'other/key.pem'):
            package.write_bytes(original)
            with zipfile.ZipFile(package, 'a') as z:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    z.writestr(name, 'unsafe')
            digest = hashlib.sha256(package.read_bytes()).hexdigest()
            with self.assertRaises(ValueError, msg=name):
                self.module().restore_chain(
                    self.archive, self.archive_sha, self.source_policy, package,
                    digest, result['chain_sha256'], [self.policy1],
                    'example/science-paper', 'v1', self.work / 'recovered')
            self.assertFalse((self.work / 'recovered').exists())
            self.assertFalse((self.work / 'escape').exists())

    def test_package_is_deterministic_and_never_overwrites(self):
        result = self.first()
        a = self.work / 'a.zip'
        b = self.work / 'b.zip'
        args = (self.archive, self.archive_sha, self.source_policy,
                self.output, result['chain_sha256'], [self.policy1],
                'example/science-paper', 'v1')
        self.module().pack_chain(*args, a)
        self.module().pack_chain(*args, b)
        self.assertEqual(a.read_bytes(), b.read_bytes())
        with self.assertRaises(ValueError): self.module().pack_chain(*args, a)

    def test_github_release_package_cli_roundtrip(self):
        result = self.first()
        package = self.work / 'release.zip'
        cmd = [sys.executable, str(SCRIPT), 'pack', str(self.archive),
               '--expected-archive-sha256', self.archive_sha,
               '--source-policy', str(self.source_policy),
               '--renewal-policy', str(self.policy1),
               '--repository', 'example/science-paper', '--version', 'v1',
               '--chain', str(self.output), '--expected-chain-sha256', result['chain_sha256'],
               '--out', str(package)]
        packed = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        self.assertEqual(packed.returncode, 0, packed.stderr)
        package_sha = json.loads(packed.stdout)['package_sha256']
        restored = subprocess.run([sys.executable, str(SCRIPT), 'restore', str(self.archive),
              '--expected-archive-sha256', self.archive_sha,
              '--source-policy', str(self.source_policy),
              '--renewal-policy', str(self.policy1),
              '--repository', 'example/science-paper', '--version', 'v1',
              '--package', str(package), '--expected-package-sha256', package_sha,
              '--expected-chain-sha256', result['chain_sha256'],
              '--out', str(self.work / 'downloaded')],
              capture_output=True, text=True, timeout=45)
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(json.loads(restored.stdout)['steps'], 1)

    def test_package_symlink_member_rejected(self):
        result = self.first()
        package = self.work / 'evidence.zip'
        self.module().pack_chain(self.archive, self.archive_sha, self.source_policy,
                                 self.output, result['chain_sha256'], [self.policy1],
                                 'example/science-paper', 'v1', package)
        with zipfile.ZipFile(package) as z:
            members = [(n, z.read(n)) for n in z.namelist()]
        with zipfile.ZipFile(package, 'w') as z:
            for name, raw in members:
                item = zipfile.ZipInfo(name)
                item.create_system = 3
                item.external_attr = (0o120777 if name.endswith('statement.json') else 0o100644) << 16
                z.writestr(item, raw)
        digest = hashlib.sha256(package.read_bytes()).hexdigest()
        with self.assertRaises(ValueError):
            self.module().restore_chain(self.archive, self.archive_sha, self.source_policy,
               package, digest, result['chain_sha256'], [self.policy1],
               'example/science-paper', 'v1', self.work / 'restored')
        self.assertFalse((self.work / 'restored').exists())

    def test_plan_only_cli_does_not_invoke_tsa_or_create_output(self):
        p = subprocess.run([sys.executable, str(SCRIPT), 'issue', str(self.archive),
             '--expected-archive-sha256', self.archive_sha,
             '--source-policy', str(self.source_policy), '--renewal-policy', str(self.policy1),
             '--repository', 'example/science-paper', '--version', 'v1',
             '--out', str(self.output)], capture_output=True, text=True, timeout=10)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)['status'], 'PLAN_ONLY')
        self.assertFalse(self.output.exists())

    # --- time-order rules for renewal chain signatures ---

    def _check(self, times, policies):
        m = self.module()
        return m._check_signed_time_order(times, policies)

    def test_same_policy_nondescresing_times_accepted(self):
        self.assertEqual(
            self._check(['2026-11-01T00:00:00+00:00',
                         '2026-11-01T00:00:00+00:00',
                         '2026-11-02T00:00:00+00:00'],
                        ['1.2.3.4.1', '1.2.3.4.1', '1.2.3.4.1']),
            'NON_DECREASING_SAME_TSA_POLICY')

    def test_same_policy_out_of_order_times_rejected(self):
        with self.assertRaisesRegex(ValueError, 'went backwards'):
            self._check(['2026-11-02T00:00:00+00:00',
                         '2026-11-01T00:00:00+00:00'],
                        ['1.2.3.4.1', '1.2.3.4.1'])

    def test_cross_policy_strictly_increasing_accepted(self):
        self.assertEqual(
            self._check(['2026-11-01T00:00:00+00:00',
                         '2026-11-01T00:00:01+00:00'],
                        ['1.2.3.4.1', '1.2.3.4.2']),
            'STRICTLY_INCREASING_CROSS_TSA_POLICY')

    def test_cross_policy_equal_times_rejected(self):
        with self.assertRaisesRegex(ValueError, 'strictly increasing'):
            self._check(['2026-11-01T00:00:00+00:00',
                         '2026-11-01T00:00:00+00:00'],
                        ['1.2.3.4.1', '1.2.3.4.2'])

    def test_cross_policy_out_of_order_times_rejected(self):
        with self.assertRaisesRegex(ValueError, 'strictly increasing'):
            self._check(['2026-11-02T00:00:00+00:00',
                         '2026-11-01T00:00:00+00:00'],
                        ['1.2.3.4.1', '1.2.3.4.2'])

    def _origin_check(self, origin, first_time, first_policy, first_accuracy=0):
        return self.module()._check_origin_to_first_renewal(
            origin, first_time, first_policy, first_accuracy)

    def test_origin_to_first_backward_rejected(self):
        # A renewal timestamp strictly earlier than the original existence
        # stamp cannot extend existence forward: accepting it misrepresents
        # the evidence, even if renewal-to-renewal times look ordered.
        origin = {'tsa_time_utc': '2026-11-02T00:00:00+00:00',
                  'policy_oid': '1.2.3.4.1', 'accuracy_microseconds': 0}
        with self.assertRaisesRegex(ValueError, 'precedes the original existence stamp'):
            self._origin_check(origin, '2026-11-01T00:00:00+00:00', '1.2.3.4.1', 0)

    def test_origin_to_first_cross_tsa_equal_time_reports_uncertainty(self):
        # Different TSAs do not share a clock. Equal or overlapping signed
        # times must NOT be reported as a proven strict order.
        origin = {'tsa_time_utc': '2026-11-01T00:00:00+00:00',
                  'policy_oid': '1.2.3.4.1', 'accuracy_microseconds': 1_000_000}
        verdict = self._origin_check(origin, '2026-11-01T00:00:00+00:00',
                                     '1.2.3.4.2', 1_000_000)
        self.assertEqual(verdict, 'CROSS_TSA_ORDER_NOT_PROVEN_CLOCK_SKEW')

    def test_origin_to_first_clear_forward_same_policy(self):
        origin = {'tsa_time_utc': '2026-11-01T00:00:00+00:00',
                  'policy_oid': '1.2.3.4.1', 'accuracy_microseconds': 0}
        verdict = self._origin_check(origin, '2026-11-02T00:00:00+00:00',
                                     '1.2.3.4.1', 0)
        self.assertEqual(verdict, 'FORWARD_SAME_TSA_POLICY_FROM_ORIGIN')

    def test_verify_chain_reports_origin_existence_stamp(self):
        result = self.first()
        report = self.verify(self.output, result['chain_sha256'], [self.policy1])
        stamp = report['origin_existence_stamp']
        self.assertTrue(isinstance(stamp.get('policy_oid'), str) and stamp['policy_oid'])
        self.assertIn('tsa_time_utc', stamp)
        self.assertIn('accuracy_microseconds', stamp)
        self.assertIn(report['time_order_origin_to_first'],
                      ('FORWARD_SAME_TSA_POLICY_FROM_ORIGIN',
                       'CROSS_TSA_ORDER_NOT_PROVEN_CLOCK_SKEW',
                       'NON_DECREASING_SAME_TSA_POLICY_FROM_ORIGIN'))

    def test_unparseable_or_naive_time_rejected(self):
        with self.assertRaisesRegex(ValueError, 'timezone-aware|ISO-8601'):
            self._check(['not-a-time', '2026-11-01T00:00:00+00:00'],
                        ['1.2.3.4.1', '1.2.3.4.1'])
        with self.assertRaisesRegex(ValueError, 'timezone-aware|ISO-8601'):
            self._check(['2026-11-01 00:00:00'],
                        ['1.2.3.4.1'])

