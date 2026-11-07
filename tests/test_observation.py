"""An independent observer's signature must bind anonymous public retrieval, not pretend first publication."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import verify_release
import test_release
import test_timestamp


class ObserverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(); cls.top=Path(cls.temp.name)
        cls.authority=test_timestamp.Authority(cls.top/'ca')
        cls.paper=test_release.ReleaseBundleTests(); cls.paper.setUp(); cls.paper.make_bundle()
        cls.policy=cls.top/'policy.json'; cls.policy.write_text(json.dumps(cls.authority.policy()))
        query=cls.top/'query.tsq'; reply=cls.top/'reply.tsr'
        for args in [ ('request',str(cls.paper.bundle),'--policy',str(cls.policy),'--out',str(query)) ]:
            r=subprocess.run([sys.executable,str(ROOT/'scripts/timestamp.py'),*args],capture_output=True,text=True)
            if r.returncode: raise RuntimeError(r.stderr)
        cls.authority.sign(query,reply)
        r=subprocess.run([sys.executable,str(ROOT/'scripts/timestamp.py'),'attach',str(cls.paper.bundle),'--policy',str(cls.policy),'--query',str(query),'--response',str(reply)],capture_output=True,text=True)
        if r.returncode: raise RuntimeError(r.stderr)
        cls.key=cls.top/'signer.key'; cls.pub=cls.top/'signer.pub'
        for cmd in [ ['openssl','genpkey','-algorithm','ED25519','-out',str(cls.key)],['openssl','pkey','-in',str(cls.key),'-pubout','-out',str(cls.pub)] ]:
            r=subprocess.run(cmd,capture_output=True,text=True)
            if r.returncode: raise RuntimeError(r.stderr)
        cls.pubhash=hashlib.sha256(cls.pub.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.paper.tearDown(); cls.temp.cleanup()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.out=self.base/'observed'
        self.assets={p.name:p.read_bytes() for p in self.paper.bundle.iterdir()}

    def fetcher(self,name):
        return self.assets[name]

    def module(self):
        import observation
        return observation

    def record(self):
        return self.module().record_public('example/science-paper','v1',self.out,self.policy,self.key,self.fetcher)

    def check(self):
        return self.module().verify_public(self.out,self.pub,self.pubhash,self.policy)

    def test_verified_observation_is_version_and_hash_bound(self):
        report=self.record(); self.assertEqual(report['timestamp_verified'],True)
        result=self.check(); self.assertEqual(result['signature'],'VERIFIED')
        self.assertEqual(result['public_observation'],'WITNESS_CLAIM_NOT_FIRST_PUBLICATION_PROOF')
        self.assertEqual(result['repository'],'example/science-paper'); self.assertEqual(result['version'],'v1')

    def test_wrong_pinned_observer_key_rejected(self):
        self.record()
        with self.assertRaises(ValueError):
            self.module().verify_public(self.out,self.pub,'0'*64,self.policy)

    def test_rewritten_claim_rejected(self):
        self.record()
        record=self.out/'observation.json'; data=json.loads(record.read_text()); data['version']='v2'; record.write_text(json.dumps(data))
        with self.assertRaises(ValueError): self.check()

    def test_tampered_download_rejected(self):
        self.record(); (self.out/'bundle'/'paper.pdf').write_bytes(b'bad')
        with self.assertRaises(ValueError): self.check()

    def test_missing_asset_prevents_signing(self):
        del self.assets['timestamp.tsr']
        with self.assertRaises(ValueError): self.record()
        self.assertFalse(self.out.exists())

    def test_external_key_and_fake_url_refused(self):
        o=self.module()
        for repo in ('http://example/research','../../bad','example/research/extra'):
            with self.assertRaises(ValueError): o.record_public(repo,'v1',self.out,self.policy,self.key,self.fetcher)
        self.assertFalse(self.out.exists())

    def test_existing_output_preserved(self):
        self.out.mkdir(); (self.out/'keep').write_text('untouched')
        with self.assertRaises(ValueError): self.record()
        self.assertEqual((self.out/'keep').read_text(),'untouched')

    def test_signed_observation_rejects_overstated_public_availability(self):
        # A compromised or careless signer must not be able to promote an
        # assertion of retrieval into a stronger, unsupported claim.
        self.record()
        observation = self.out / 'observation.json'
        data = json.loads(observation.read_text(encoding='utf-8'))
        data['public_availability'] = 'INDEPENDENTLY_PROVEN'
        observation.write_text(json.dumps(data, sort_keys=True, indent=2) + '\n', encoding='utf-8')
        self.module().sign(self.key, observation, self.out / 'observation.sig')
        with self.assertRaisesRegex(ValueError, 'overstates proof'):
            self.check()

    def test_signed_observation_rejects_false_timestamp_verified(self):
        self.record()
        observation = self.out / 'observation.json'
        data = json.loads(observation.read_text(encoding='utf-8'))
        data['timestamp_verified'] = False
        observation.write_text(json.dumps(data, sort_keys=True, indent=2) + '\n', encoding='utf-8')
        self.module().sign(self.key, observation, self.out / 'observation.sig')
        with self.assertRaisesRegex(ValueError, 'overstates proof'):
            self.check()

    def test_signed_observation_rejects_clock_precision_overclaim(self):
        self.record()
        observation = self.out / 'observation.json'
        data = json.loads(observation.read_text(encoding='utf-8'))
        data['witness_clock'] = 'TRUSTED_ATOMIC_CLOCK'
        observation.write_text(json.dumps(data, sort_keys=True, indent=2) + '\n', encoding='utf-8')
        self.module().sign(self.key, observation, self.out / 'observation.sig')
        with self.assertRaisesRegex(ValueError, 'overstates proof'):
            self.check()

    def issue_observation_timestamp(self, query: bytes) -> bytes:
        request, response = self.base / "observer.tsq", self.base / "observer.tsr"
        request.write_bytes(query)
        self.authority.sign(request, response)
        return response.read_bytes()

    def stamp_record(self):
        return self.module().record_public(
            'example/science-paper', 'v1', self.out, self.policy, self.key, self.fetcher,
            stamp_observation=True, tsa_exchange=self.issue_observation_timestamp,
        )

    def check_stamped(self):
        return self.module().verify_public(
            self.out, self.pub, self.pubhash, self.policy,
            require_observation_timestamp=True,
            expected_repository='example/science-paper', expected_version='v1',
        )

    def test_observer_receipt_digest_is_domain_separated_and_signs_signature_bytes(self):
        obs = self.module()
        first = obs.receipt_digest(b'{}', b'original signature')
        self.assertEqual(len(first), 32)
        self.assertNotEqual(first, obs.receipt_digest(b'{}', b'changed signature'))
        self.assertNotEqual(first, hashlib.sha256(b'{}' + b'original signature').digest())

    def test_timestamped_signed_receipt_verifies_under_explicit_external_policy(self):
        report = self.stamp_record()
        self.assertEqual(report['observation_timestamp'], 'VERIFIED')
        verified = self.check_stamped()
        self.assertEqual(verified['observation_timestamp'], 'VERIFIED')
        self.assertIn('observation_tsa_time_utc', verified)
        self.assertEqual(verified['public_observation'], 'WITNESS_CLAIM_NOT_FIRST_PUBLICATION_PROOF')
        self.assertTrue((self.out / 'observation.tsq').is_file())
        self.assertTrue((self.out / 'observation.tsr').is_file())

    def test_missing_timestamp_is_allowed_only_in_legacy_mode(self):
        self.record()
        plain = self.check()
        self.assertEqual(plain['observation_timestamp'], 'NOT_PRESENT')
        with self.assertRaisesRegex(ValueError, 'timestamp is required'):
            self.check_stamped()

    def test_partial_witness_timestamp_pair_rejected(self):
        self.stamp_record()
        (self.out / 'observation.tsr').unlink()
        with self.assertRaises(ValueError):
            self.check_stamped()

    def test_tampered_witness_timestamp_response_rejected(self):
        self.stamp_record()
        (self.out / 'observation.tsr').write_bytes(b'not a CMS timestamp')
        with self.assertRaises(ValueError):
            self.check_stamped()

    def test_replacing_signed_observation_after_timestamp_is_detected(self):
        self.stamp_record()
        record = self.out / 'observation.json'
        data = json.loads(record.read_text(encoding='utf-8'))
        data['observed_interval_start_utc'] = '2025-01-01T00:00:00+00:00'
        record.write_text(json.dumps(data,sort_keys=True,indent=2)+'\n',encoding='utf-8')
        self.module().sign(self.key, record, self.out / 'observation.sig')
        with self.assertRaises(ValueError):
            self.check_stamped()

    def test_wrong_expected_repository_and_version_are_rejected(self):
        self.record()
        for kwargs in ({'expected_repository': 'other/research'},
                       {'expected_version': 'v2'}):
            with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                self.module().verify_public(self.out, self.pub, self.pubhash, self.policy, **kwargs)

    def test_observer_cannot_relabel_signed_bundle_from_other_repository(self):
        with self.assertRaisesRegex(ValueError, 'source identity mismatch'):
            self.module().record_public('example/research', 'v1', self.out, self.policy,
                                        self.key, self.fetcher)
        self.assertFalse(self.out.exists())

    def test_tsa_failure_does_not_publish_partial_witness(self):
        with self.assertRaises(ValueError):
            self.module().record_public(
                'example/science-paper', 'v1', self.out, self.policy,
                self.key, self.fetcher, stamp_observation=True,
                tsa_exchange=lambda _query: b'not a timestamp',
            )
        self.assertFalse(self.out.exists())

    def test_wrong_timestamp_query_nonce_rejected(self):
        self.stamp_record()
        from timestamp import make_query_for_digest, load_policy
        digest = self.module().receipt_digest(
            (self.out / 'observation.json').read_bytes(),
            (self.out / 'observation.sig').read_bytes(),
        )
        (self.out / 'observation.tsq').write_bytes(
            make_query_for_digest(digest, load_policy(self.policy)))
        with self.assertRaises(ValueError):
            self.check_stamped()

    def test_signed_unknown_security_claim_rejected(self):
        self.record()
        path = self.out / 'observation.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        data['author_identity_verified'] = True
        path.write_text(json.dumps(data, sort_keys=True, indent=2) + '\n', encoding='utf-8')
        self.module().sign(self.key, path, self.out / 'observation.sig')
        with self.assertRaises(ValueError):
            self.check()

    def test_cli_requires_out_of_band_expected_source_identity(self):
        self.record()
        command = [sys.executable, str(ROOT / 'scripts' / 'observation.py'),
                   'verify', '--observation', str(self.out),
                   '--policy', str(self.policy), '--public-key', str(self.pub),
                   '--expected-public-key-sha256', self.pubhash]
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 1)
        self.assertIn('--expected-repository', result.stderr)
        self.assertIn('--expected-version', result.stderr)

    def test_no_authorship_claim(self):
        self.record(); data=json.loads((self.out/'observation.json').read_text())
        self.assertEqual(data['authorship'],'NOT_PROVEN')
        self.assertEqual(data['first_publication'],'NOT_PROVEN')
        self.assertFalse((self.out/'signer.key').exists())
