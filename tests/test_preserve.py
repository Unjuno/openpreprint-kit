"""Recovery must never trust archive paths, its embedded CA, or a self-supplied digest."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

import test_release

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'preserve.py'

class PreserveTests(unittest.TestCase):
    def setUp(self):
        self.helper = test_release.ReleaseBundleTests(); self.helper.setUp(); self.helper.make_bundle()
        self.addCleanup(self.helper.tearDown)
        self.root = self.helper.root
        self.archive = self.root / 'portable.zip'
        self.target = self.root / 'recovered'

    def call(self, *args):
        self.assertTrue(SCRIPT.is_file(), 'preservation command missing')
        return subprocess.run([sys.executable, str(SCRIPT), *map(str,args)], capture_output=True, text=True, timeout=20)

    def create(self):
        r = self.call('pack',self.helper.bundle,'--out',self.archive,'--integrity-only')
        self.assertEqual(r.returncode,0,r.stderr)
        return hashlib.sha256(self.archive.read_bytes()).hexdigest()

    def restore(self, digest):
        return self.call('restore',self.archive,'--out',self.target,'--expected-sha256',digest,'--integrity-only')

    def test_roundtrip_preserves_bytes(self):
        digest=self.create(); r=self.restore(digest)
        self.assertEqual(r.returncode,0,r.stderr)
        for p in self.helper.bundle.iterdir():
            self.assertEqual(p.read_bytes(),(self.target/'bundle'/p.name).read_bytes())
        self.assertEqual(json.loads(r.stdout)['timestamp'],'NOT_VERIFIED')

    def test_default_requires_timestamp_policy(self):
        r=self.call('pack',self.helper.bundle,'--out',self.archive)
        self.assertNotEqual(r.returncode,0)
        self.assertFalse(self.archive.exists())

    def test_wrong_pin_prevents_restoration(self):
        self.create(); r=self.restore('0'*64)
        self.assertNotEqual(r.returncode,0); self.assertFalse(self.target.exists())

    def test_no_overwrite(self):
        digest=self.create(); self.target.mkdir(); (self.target/'important').write_text('keep')
        r=self.restore(digest)
        self.assertNotEqual(r.returncode,0); self.assertEqual((self.target/'important').read_text(),'keep')

    def test_unexpected_secret_is_not_archived(self):
        (self.helper.bundle/'secret.key').write_text('PRIVATE')
        r=self.call('pack',self.helper.bundle,'--out',self.archive,'--integrity-only')
        self.assertNotEqual(r.returncode,0); self.assertFalse(self.archive.exists())

    def mutate_zip(self,name,content,symlink=False):
        with zipfile.ZipFile(self.archive,'a') as z:
            item=zipfile.ZipInfo(name)
            if symlink:
                item.create_system=3; item.external_attr=(0o120777<<16)
            z.writestr(item,content)
        return hashlib.sha256(self.archive.read_bytes()).hexdigest()

    def test_path_traversal_rejected_even_with_matching_pin(self):
        self.create(); r=self.restore(self.mutate_zip('../escape',b'danger'))
        self.assertNotEqual(r.returncode,0); self.assertFalse((self.root/'escape').exists()); self.assertFalse(self.target.exists())

    def test_duplicate_member_is_rejected(self):
        import warnings
        self.create()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            digest=self.mutate_zip('bundle/paper.pdf',b'changed')
        self.assertNotEqual(self.restore(digest).returncode,0); self.assertFalse(self.target.exists())

    def test_link_member_is_rejected(self):
        self.create(); r=self.restore(self.mutate_zip('extra.link',b'../../etc/passwd',True))
        self.assertNotEqual(r.returncode,0); self.assertFalse(self.target.exists())

    def test_changed_member_rejected_even_with_matching_archive_pin(self):
        self.create()
        with zipfile.ZipFile(self.archive) as z: items={n:z.read(n) for n in z.namelist()}
        items['bundle/paper.pdf'] += b'changed'
        with zipfile.ZipFile(self.archive,'w') as z:
            for n,b in items.items(): z.writestr(n,b)
        r=self.restore(hashlib.sha256(self.archive.read_bytes()).hexdigest())
        self.assertNotEqual(r.returncode,0); self.assertFalse(self.target.exists())

    def test_pack_is_deterministic_and_does_not_overwrite(self):
        digest=self.create(); r=self.call('pack',self.helper.bundle,'--out',self.archive,'--integrity-only')
        self.assertNotEqual(r.returncode,0); self.assertEqual(digest,hashlib.sha256(self.archive.read_bytes()).hexdigest())
        other=self.root/'other.zip'
        self.assertEqual(self.call('pack',self.helper.bundle,'--out',other,'--integrity-only').returncode,0)
        self.assertEqual(self.archive.read_bytes(),other.read_bytes())

    def test_incomplete_evidence_is_rejected(self):
        (self.helper.bundle/'timestamp.tsq').write_bytes(b'test')
        self.assertNotEqual(self.call('pack',self.helper.bundle,'--out',self.archive,'--integrity-only').returncode,0)
        self.assertFalse(self.archive.exists())

class SignedPreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import test_timestamp
        cls.temp=tempfile.TemporaryDirectory(); cls.root=Path(cls.temp.name)
        cls.authority=test_timestamp.Authority(cls.root/'authority')
        cls.helper=test_release.ReleaseBundleTests(); cls.helper.setUp(); cls.helper.make_bundle()
        cls.policy=cls.root/'policy.json'; cls.policy.write_text(json.dumps(cls.authority.policy()))
        query=cls.root/'query.tsq'; reply=cls.root/'reply.tsr'
        def command(*args):
            r=subprocess.run([sys.executable,str(ROOT/'scripts/timestamp.py'),*map(str,args)],capture_output=True,text=True,timeout=30)
            if r.returncode: raise RuntimeError(r.stderr)
        command('request',cls.helper.bundle,'--policy',cls.policy,'--out',query)
        cls.authority.sign(query,reply)
        command('attach',cls.helper.bundle,'--policy',cls.policy,'--query',query,'--response',reply)

    @classmethod
    def tearDownClass(cls):
        cls.helper.tearDown(); cls.temp.cleanup()

    def test_signed_roundtrip_requires_current_external_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); archive=root/'evidence.zip'
            r=subprocess.run([sys.executable,str(SCRIPT),'pack',str(self.helper.bundle),'--out',str(archive),'--policy',str(self.policy)],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            digest=hashlib.sha256(archive.read_bytes()).hexdigest()
            bad=subprocess.run([sys.executable,str(SCRIPT),'restore',str(archive),'--out',str(root/'bad'),'--expected-sha256',digest],capture_output=True,text=True)
            self.assertNotEqual(bad.returncode,0); self.assertFalse((root/'bad').exists())
            good=subprocess.run([sys.executable,str(SCRIPT),'restore',str(archive),'--out',str(root/'restored'),'--expected-sha256',digest,'--policy',str(self.policy)],capture_output=True,text=True)
            self.assertEqual(good.returncode,0,good.stderr)
            self.assertEqual(json.loads(good.stdout)['timestamp'],'VERIFIED')
            self.assertEqual(json.loads(good.stdout)['bundled_trust'],'NOT_AUTOMATICALLY_TRUSTED')
