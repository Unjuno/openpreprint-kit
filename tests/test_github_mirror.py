"""GitHub-only immutable mirror: preserve out-of-band integrity & TSA evidence."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import custody
import test_custody


class FakeGitHub:
    """Fake GitHub API/CLI only. Real SHA-256, archive restore and TSA still run."""
    def __init__(self, mirror='archiver/evidence', immutable=True):
        self.mirror = mirror
        self.immutable = immutable
        self.created = None
        self.files = {}
        self.draft = False
        self.published = False
        self.calls = []
        self.block_create = False
        self.corrupt_public = False
        self.extra_asset = False
        self.change_tag = False
        self.mirror_sha = 'a' * 40
        self.source = None
        self.source_assets = {}
        self.source_missing = False
        self.source_corrupt = False
        self.source_immutable = True

    def tools(self):
        self.calls.append(('tools',))

    def api(self, method, path, data=None, *, allow_missing=False):
        self.calls.append((method, path))
        main = 'repos/' + self.mirror
        if self.source and path == 'repos/' + self.source:
            return {'full_name': self.source, 'private': False}
        if self.source and path.startswith('repos/' + self.source + '/releases/tags/'):
            version=path.rsplit('/',1)[-1]
            if self.source_missing: return None
            return {'tag_name':version,'draft':False,'immutable':self.source_immutable,
                    'assets':[{'name':n} for n in self.source_assets[version]]}
        if method != 'GET':
            raise AssertionError('unexpected mutable GitHub API call: ' + method)
        if path == main:
            return {'full_name':self.mirror, 'private':False,
                    'permissions':{'admin':True}, 'default_branch':'main'}
        if path == main+'/immutable-releases':
            return {'enabled':self.immutable}
        if path == main+'/git/ref/heads/main':
            return {'object':{'sha':self.mirror_sha}}
        if path.startswith(main+'/git/ref/tags/'):
            return {'object':{'sha':self.mirror_sha}} if self.created else None
        if path.startswith(main+'/releases/tags/'):
            if self.created is None: return None
            return {'tag_name':('incorrect' if self.change_tag else self.created),
                    'immutable':self.immutable and self.published,
                    'draft':self.draft, 'assets':[{'name':name} for name in self.files] +
                    ([{'name':'unlisted.secret'}] if self.extra_asset else [])}
        raise AssertionError('unknown API path '+path)

    def command(self, args):
        self.calls.append(('command',args[:3]))
        if args[:2] == ['release','create']:
            if self.block_create: raise ValueError('simulated upload failure')
            self.created = args[2]
            self.draft = True
            self.files = {Path(p).name:Path(p).read_bytes()
                          for p in args[3:args.index('--repo')]}
            return ''
        if args[:2] == ['release','download']:
            folder=Path(args[args.index('--dir')+1])
            folder.mkdir(parents=True)
            for name, data in self.files.items():
                (folder/name).write_bytes(data)
            return ''
        if args[:2] == ['release','edit']:
            self.draft=False
            self.published=True
            return ''
        if args[:2] == ['release','verify']:
            if not self.published and '--repo' in args and args[args.index('--repo')+1] != self.source:
                raise ValueError('attestation not available')
            return '{"verified":true}'
        if args[:2] == ['release','verify-asset']:
            target=args[args.index('--repo')+1]
            expected=(self.source_assets.get(args[2],{}) if target == self.source else self.files)
            if expected.get(Path(args[3]).name) != Path(args[3]).read_bytes():
                raise ValueError('asset attestation failed')
            return '{"verified":true}'
        raise AssertionError('unknown command '+str(args))

    def anonymous(self, repository, tag, name):
        if repository == self.source:
            data=self.source_assets[tag][name]
            return data + (b'TAMPER' if self.source_corrupt and name=='paper.pdf' else b'')
        if repository != self.mirror or tag != self.created:
            raise ValueError('wrong publicly requested release')
        if self.corrupt_public and name.endswith('.zip'):
            return b'fake archive replacement'
        return self.files[name]


class GithubMirrorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_custody.CustodyTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        test_custody.CustodyTests.tearDownClass.__func__(cls)

    def setUp(self):
        test_custody.CustodyTests.setUp(self)
        self.mirror = 'archiver/evidence'
        self.source = 'example/science-paper'
        self.output = self.work/'mirror-journal'
        self.fetched = self.work/'retrieved'
        self.remote = FakeGitHub(self.mirror)
        self.remote.source = self.source
        for version, archive, _ in self.entries:
            with zipfile.ZipFile(archive) as z:
                self.remote.source_assets[version] = {
                    name[len('bundle/'):]:z.read(name) for name in z.namelist()
                    if name.startswith('bundle/') and not name.endswith('/')
                }
        self.deposited = custody.deposit(self.source,self.entries,self.store,self.policy)
        self.catalog_pin = self.deposited['catalog_sha256']

    def module(self):
        import github_mirror
        return github_mirror

    def publish(self):
        return self.module().publish(self.source,self.mirror,self.store,self.catalog_pin,
                                     self.policy,self.output,self.remote)

    def verify(self,pin=None,tag=None,require_source_release=False):
        receipt_pin=pin if pin is not None else hashlib.sha256(self.remote.files['github-mirror-receipt.json']).hexdigest()
        tag=tag if tag is not None else self.remote.created
        return self.module().verify_mirror(self.source,self.mirror,tag,self.catalog_pin,
                         receipt_pin,self.policy,self.fetched,self.remote,
                         require_source_release=require_source_release)

    def test_offline_plan_does_not_need_network_and_is_deterministic(self):
        m=self.module()
        result=m.plan(self.source,self.mirror,self.catalog_pin)
        self.assertEqual(result['mode'],'PLAN_ONLY')
        self.assertEqual(result['status'],'PLAN_ONLY')
        self.assertFalse(result['github_changes'])
        self.assertEqual(result['tag'],m.plan(self.source,self.mirror,self.catalog_pin)['tag'])
        self.assertTrue(result['tag'].startswith('opk-custody-'))
        self.assertEqual(result['cloud_provider'],'GitHub Releases')

    def test_same_repository_cannot_be_storage_mirror(self):
        with self.assertRaisesRegex(ValueError,'distinct'):
            self.module().plan(self.source,self.source,self.catalog_pin)

    def test_valid_two_version_mirror_roundtrip_verifies_real_timestamps(self):
        report=self.publish()
        self.assertEqual(report['status'],'PASS')
        self.assertEqual(report['archive_count'],2)
        self.assertEqual(set(self.remote.files),{'custody.json','v1.opk.zip','v2.opk.zip','github-mirror-receipt.json'})
        result=self.verify(pin=report['receipt_sha256'],tag=report['tag'])
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(result['timestamp'],'VERIFIED_USING_CURRENT_POLICY')
        self.assertEqual(result['archive_count'],2)
        self.assertEqual(result['durability'],'NOT_PROVEN')
        self.assertEqual(result['operator_independence'],'NOT_PROVEN')
        self.assertEqual((self.fetched/'v1.opk.zip').read_bytes(),self.entries[0][1].read_bytes())
        self.assertEqual((self.fetched/'v2.opk.zip').read_bytes(),self.entries[1][1].read_bytes())

    def test_strict_verify_checks_actual_public_source_bytes(self):
        report = self.publish()
        before_verify = len(self.remote.calls)
        result = self.verify(pin=report['receipt_sha256'], require_source_release=True)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['source_publication'], 'PUBLIC_IMMUTABLE_ASSETS_MATCH')
        self.assertEqual(result['github_attestation'], 'NOT_VERIFIED_BY_ANONYMOUS_MODE')
        self.assertFalse(any(c[0] == 'command' for c in self.remote.calls[before_verify:]))

    def test_strict_verify_rejects_deleted_public_source_release(self):
        report = self.publish()
        self.remote.source_missing = True
        with self.assertRaisesRegex(ValueError, 'source Release'):
            self.verify(pin=report['receipt_sha256'], require_source_release=True)
        self.assertFalse(self.fetched.exists())
        result = self.verify(pin=report['receipt_sha256'], require_source_release=False)
        self.assertEqual(result['source_publication'], 'NOT_CHECKED')

    def test_strict_verify_rejects_wrong_source_payload(self):
        report = self.publish()
        self.remote.source_corrupt = True
        with self.assertRaisesRegex(ValueError, 'source Release asset mismatch'):
            self.verify(pin=report['receipt_sha256'], require_source_release=True)
        self.assertFalse(self.fetched.exists())

    def test_strict_verify_rejects_mutable_source_release(self):
        report = self.publish()
        self.remote.source_immutable = False
        with self.assertRaisesRegex(ValueError, 'source Release'):
            self.verify(pin=report['receipt_sha256'], require_source_release=True)
        self.assertFalse(self.fetched.exists())

    def test_wrong_catalog_pin_stops_before_any_write(self):
        with self.assertRaisesRegex(ValueError,'catalog SHA-256'):
            self.module().publish(self.source,self.mirror,self.store,'0'*64,self.policy,
                                  self.output,self.remote)
        self.assertIsNone(self.remote.created)

    def test_disabled_immutable_releases_refuse_publication(self):
        self.remote.immutable=False
        with self.assertRaisesRegex(ValueError,'immutable'):
            self.publish()
        self.assertIsNone(self.remote.created)

    def test_old_release_tag_collision_stops_before_mutation(self):
        m=self.module(); self.remote.created=m.plan(self.source,self.mirror,self.catalog_pin)['tag']
        with self.assertRaisesRegex(ValueError,'already exists'):
            self.publish()
        self.assertFalse(any(c[0]=='command' and c[1][:2]==['release','create'] for c in self.remote.calls))

    def test_mirror_requires_real_public_source_release(self):
        self.remote.source_missing=True
        with self.assertRaisesRegex(ValueError,'source Release|source release'):
            self.publish()
        self.assertIsNone(self.remote.created)

    def test_mirror_rejects_source_release_payload_disagreement(self):
        self.remote.source_corrupt=True
        with self.assertRaisesRegex(ValueError,'source Release|source release|mismatch'):
            self.publish()
        self.assertIsNone(self.remote.created)

    def test_public_archive_byte_mutation_rejected(self):
        report=self.publish()
        self.remote.corrupt_public=True
        with self.assertRaisesRegex(ValueError,'SHA-256|mismatch'):
            self.verify(report['receipt_sha256'])
        self.assertFalse(self.fetched.exists())

    def test_receipt_pin_cannot_be_derived_only_from_mirror(self):
        self.publish()
        with self.assertRaisesRegex(ValueError,'receipt SHA-256'):
            self.verify(pin='0'*64)
        self.assertFalse(self.fetched.exists())

    def test_a_valid_receipt_for_another_source_is_rejected(self):
        self.publish()
        with self.assertRaisesRegex(ValueError,'source|repository'):
            self.module().verify_mirror('example/not-source',self.mirror,self.remote.created,
                self.catalog_pin,hashlib.sha256(self.remote.files['github-mirror-receipt.json']).hexdigest(),
                self.policy,self.fetched,self.remote)
        self.assertFalse(self.fetched.exists())

    def test_bad_release_attestation_state_blocks_audit(self):
        self.publish()
        self.remote.immutable=False
        with self.assertRaisesRegex(ValueError,'immutable'):
            self.verify()
        self.assertFalse(self.fetched.exists())

    def test_extra_remote_asset_is_rejected(self):
        self.publish()
        self.remote.extra_asset=True
        with self.assertRaisesRegex(ValueError,'assets|asset'):
            self.verify()
        self.assertFalse(self.fetched.exists())

    def test_failed_remote_public_step_leaves_partial_journal_without_rollback_claim(self):
        self.remote.corrupt_public=True
        with self.assertRaisesRegex(ValueError,'SHA-256|mismatch'):
            self.publish()
        report=json.loads((self.output/'mirror-report.json').read_text())
        self.assertEqual(report['status'],'FAIL')
        self.assertIn(report['stage'],('PUBLISHED_PENDING_AUDIT','PUBLIC_AUDIT'))
        self.assertEqual(report['rollback'],'NOT_PERFORMED')
        self.assertTrue(self.remote.published)

    def test_redirect_policy_refuses_credentials_and_other_hosts(self):
        m=self.module()
        for url in ['https://evil.com/a','http://github.com/a',
                    'https://github.com.evil.com/x','https://user:token@github.com/a',
                    'https://github.com:444/x']:
            self.assertFalse(m.safe_github_url(url),url)
        self.assertTrue(m.safe_github_url('https://release-assets.githubusercontent.com/a'))

    def test_anonymous_public_api_needs_no_gh_or_owner_token(self):
        m=self.module()
        class FakeReply:
            status=200
            url='https://api.github.com/repos/archiver/evidence'
            def __init__(self, content): self.stream=io.BytesIO(content)
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self,n=-1): return self.stream.read(n)
        class FakeOpener:
            def open(self,request,timeout=None):
                self.url=request.full_url
                return FakeReply(json.dumps({'full_name':'archiver/evidence','private':False,
                            'default_branch':'main'}).encode())
        with patch('urllib.request.build_opener',return_value=FakeOpener()), \
             patch('subprocess.run',side_effect=AssertionError('gh must not be called')):
            response=m.AnonymousGateway().api('GET','repos/archiver/evidence')
        self.assertEqual(response['full_name'],self.mirror)

    def test_external_verify_does_not_query_admin_immutable_setting(self):
        self.publish()
        initial=list(self.remote.calls)
        result=self.verify()
        self.assertEqual(result['status'],'PASS')
        commands=self.remote.calls[len(initial):]
        self.assertFalse(any(k=='command' for k,*_ in commands))
        self.assertFalse(any(k=='GET' and item.endswith('/immutable-releases') for k,item in commands))

    def test_same_owner_is_never_called_independent_custody(self):
        m=self.module()
        self.assertEqual(m.plan('example/paper','example/archive','a'*64)['operator_independence'],'NOT_PROVEN')
        self.assertEqual(m.plan('example/paper','other/archive','a'*64)['operator_independence'],'NOT_PROVEN')

    def test_public_output_never_contains_a_secret_key(self):
        report=self.publish()
        self.assertFalse(any(x.endswith(('.key','.pem','.p12')) for x in self.remote.files))
        self.assertNotIn('INDEPENDENT',json.dumps(report))
