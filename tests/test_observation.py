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
        return self.module().record_public('example/research','v1',self.out,self.policy,self.key,self.fetcher)

    def check(self):
        return self.module().verify_public(self.out,self.pub,self.pubhash,self.policy)

    def test_verified_observation_is_version_and_hash_bound(self):
        report=self.record(); self.assertEqual(report['timestamp_verified'],True)
        result=self.check(); self.assertEqual(result['signature'],'VERIFIED')
        self.assertEqual(result['public_observation'],'WITNESS_CLAIM_NOT_FIRST_PUBLICATION_PROOF')
        self.assertEqual(result['repository'],'example/research'); self.assertEqual(result['version'],'v1')

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

    def test_no_authorship_claim(self):
        self.record(); data=json.loads((self.out/'observation.json').read_text())
        self.assertEqual(data['authorship'],'NOT_PROVEN')
        self.assertEqual(data['first_publication'],'NOT_PROVEN')
        self.assertFalse((self.out/'signer.key').exists())
