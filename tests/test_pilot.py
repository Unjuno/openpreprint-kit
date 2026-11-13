"""Owner-only operational acceptance: network mocked, bytes and cryptography real."""
from pathlib import Path
import hashlib
import base64
import importlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def module():
    return importlib.import_module('pilot')


class PlanTests(unittest.TestCase):
    def test_read_only_plan_requires_no_credentials_or_network(self):
        command = ROOT / 'scripts/pilot.py'
        self.assertTrue(command.is_file(), 'operational acceptance CLI missing')
        r = subprocess.run([sys.executable, str(command), '--template', 'example/kit', '--repos',
                            'example/opk-demo-one', 'example/opk-demo-two'], capture_output=True, text=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        report = json.loads(r.stdout)
        self.assertEqual(report['mode'], 'PLAN_ONLY')
        self.assertEqual(report['release_count'], 4)
        self.assertFalse(report['publication_performed'])

    def test_reject_real_or_duplicate_destination(self):
        self.assertTrue((ROOT/'scripts/pilot.py').exists(), 'pilot missing')
        for targets in (['example/real-paper', 'example/opk-demo-two'],
                        ['example/opk-demo-one', 'EXAMPLE/opk-demo-one'],
                        ['example/opk-demo-one', 'https://evil.invalid/bad']):
            with self.subTest(targets=targets), self.assertRaises(ValueError):
                module().plan('example/kit', targets)

    def test_source_cannot_be_a_destination(self):
        self.assertTrue((ROOT/'scripts/pilot.py').exists(), 'pilot missing')
        with self.assertRaises(ValueError):
            module().plan('example/opk-demo-one', ['example/opk-demo-one', 'example/opk-demo-two'])

    def test_http_auth_failure_is_not_absence_or_secret_output(self):
        self.assertTrue((ROOT/'scripts/pilot.py').exists(), 'pilot missing')
        reply = subprocess.CompletedProcess([], 1, 'HTTP/2.0 403 Forbidden\ncontent-type: application/json\n\n{"message":"denied"}', 'secret-token-DO-NOT-PRINT')
        with patch('subprocess.run', return_value=reply), self.assertRaisesRegex(ValueError, 'HTTP 403') as caught:
            module().GitHub().api('GET', 'repos/example/missing', allow_missing=True)
        self.assertNotIn('secret-token', str(caught.exception))

    def test_404_is_only_allowed_missing_status(self):
        self.assertTrue((ROOT/'scripts/pilot.py').exists(), 'pilot missing')
        for status in (404, 500):
            reply = subprocess.CompletedProcess([], 1, f'HTTP/2.0 {status} Error\n\n{{}}', '')
            with patch('subprocess.run', return_value=reply):
                if status == 404:
                    self.assertIsNone(module().GitHub().api('GET', 'repos/example/missing', allow_missing=True))
                else:
                    with self.assertRaises(ValueError):
                        module().GitHub().api('GET', 'repos/example/missing', allow_missing=True)


class FakeGitHub:
    """Only GitHub network effects are simulated; toolkit checks still execute."""
    def __init__(self, temp):
        self.temp = temp
        self.template = {'full_name':'example/kit','private':False,'is_template':False,'permissions':{'admin':True},'default_branch':'main'}
        self.repos = {}
        self.releases = {}
        self.calls = []
        self.counter = 0
        self.corrupt_draft = False
        self.fail_attestation = False
        self.disable_immutable = False
        self.drift_v1 = False
        self.corrupt_source = False
        self._blobs = {}
        self._pending_source = {}
        self.sources = {}

    def tools(self):
        self.calls.append(('tools',))

    def api(self, method, path, data=None, *, allow_missing=False):
        self.calls.append((method, path, data))
        bits = path.split('/')
        repo = '/'.join(bits[1:3])
        suffix = '/'.join(bits[3:])
        if repo == 'example/kit' and not suffix:
            if method == 'PATCH': self.template.update(data)
            return dict(self.template)
        if not suffix:
            value = self.repos.get(repo)
            if value is None and not allow_missing: raise ValueError('repository missing')
            return dict(value) if value else None
        if suffix == 'immutable-releases':
            if method == 'PUT': self.repos[repo]['immutable'] = not self.disable_immutable
            return {'enabled': self.repos[repo].get('immutable',False)}
        if suffix == 'commits/main': return {'sha':self.repos[repo]['head']}
        if suffix == 'git/ref/heads/main': return {'object':{'sha':self.repos[repo]['head'],'type':'commit'}}
        if suffix.startswith('git/commits/') and method == 'GET': return {'tree':{'sha':'b'*40}}
        if suffix == 'git/blobs':
            oid=hashlib.sha1(json.dumps(data).encode()).hexdigest()
            self._blobs[oid]=base64.b64decode(data['content'])
            return {'sha':oid}
        if suffix == 'git/trees':
            self._pending_source[repo]={entry['path']:self._blobs[entry['sha']]
                                        for entry in data['tree']}
            if self.corrupt_source:
                self._pending_source[repo]['paper/paper.pdf']=b'TAMPERED_SOURCE'
            return {'sha':'c'*40}
        if suffix == 'git/commits' and method == 'POST':
            self.counter += 1
            commit=f'{self.counter:040x}'
            self.sources[(repo,commit)]=dict(self._pending_source[repo])
            return {'sha':commit}
        if suffix == 'git/refs/heads/main' and method == 'PATCH':
            assert data['force'] is False
            self.repos[repo]['head'] = data['sha']
            return {'object':{'sha':data['sha']}}
        if suffix.startswith('releases/tags/'):
            tag=bits[-1]; value=self.releases.get((repo,tag))
            if not value: return None
            return {'id':value['id'],'tag_name':tag,'draft':value['draft'],'immutable':not value['draft'],
                    'assets':[{'name':n} for n in value['assets']],
                    'html_url':f'https://github.com/{repo}/releases/tag/{tag}'}
        if suffix.startswith('git/ref/tags/'):
            value=self.releases.get((repo,bits[-1]))
            return None if value is None else {'object':{'sha':value['commit'],'type':'commit'}}
        raise AssertionError((method,path,data))

    def command(self, args):
        self.calls.append(('gh', *args))
        if args[:2] == ['repo','create']:
            repo=args[2]
            if repo in self.repos: raise ValueError('existing repository')
            self.repos[repo]={'full_name':repo,'private':False,'permissions':{'admin':True},'default_branch':'main','head':'a'*40,'template_repository':{'full_name':'example/kit'}}
            return ''
        repo=args[args.index('--repo')+1]
        tag=args[2]
        if args[:2] == ['release','create']:
            assets={}
            for item in args[3:]:
                p=Path(item)
                if p.is_file() and p.parent.name == 'bundle': assets[p.name]=p.read_bytes()
            self.releases[(repo,tag)]={'draft':True,'assets':assets,'id':len(self.releases)+1,'commit':args[args.index('--target')+1]}
            return ''
        if args[:2] == ['release','download']:
            dest=Path(args[args.index('--dir')+1])
            dest.mkdir(parents=True,exist_ok=True)
            for name, content in self.releases[(repo,tag)]['assets'].items(): (dest/name).write_bytes(content)
            if self.corrupt_draft: (dest/'paper.pdf').write_bytes(b'BROKEN')
            return ''
        if args[:2] == ['release','edit']:
            self.releases[(repo,tag)]['draft']=False
            if self.drift_v1 and tag=='v2': self.releases[(repo,'v1')]['assets']['paper.pdf']+=b'changed later'
            return ''
        if args[:2] == ['release','verify']:
            if self.fail_attestation: raise ValueError('attestation unavailable')
            return json.dumps({'synthetic_mock_attestation':True})
        if args[:2] == ['release','verify-asset']: return 'mock GitHub attestation checked'
        raise AssertionError(args)

    def anonymous_source(self, repository, commit, path):
        self.calls.append(('anonymous_source',repository,commit,path))
        return self.sources[(repository,commit)][path]

    def anonymous(self, repository, version, name):
        value=self.releases[(repository,version)]
        if value['draft']: raise ValueError('draft not public')
        return value['assets'][name]


@unittest.skipUnless((ROOT/'scripts/pilot.py').exists(), 'pilot implementation not yet present')
class OperationalPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import test_timestamp
        cls.authority_temp=tempfile.TemporaryDirectory()
        cls.base=Path(cls.authority_temp.name)
        cls.authority=test_timestamp.Authority(cls.base/'tsa')
        cls.policy=cls.base/'policy.json'; cls.policy.write_text(json.dumps(cls.authority.policy()))

    @classmethod
    def tearDownClass(cls): cls.authority_temp.cleanup()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.gateway=FakeGitHub(self.root)

    def local_tsa(self, url, query, timeout):
        # A real CMS/RFC3161 response from a test CA; only HTTP is replaced.
        with tempfile.TemporaryDirectory() as tmp:
            q=Path(tmp)/'request.tsq'; r=Path(tmp)/'response.tsr'
            q.write_bytes(query); self.authority.sign(q,r); return r.read_bytes()

    def apply(self):
        with patch('timestamp.post_query', side_effect=self.local_tsa):
            return module().execute('example/kit', ['example/opk-demo-one','example/opk-demo-two'], self.policy, self.root/'run', gateway=self.gateway)

    def test_four_release_roundtrip_uses_real_crypto_and_preserves_old_versions(self):
        r=self.apply()
        self.assertEqual(r['status'],'PASS')
        self.assertEqual(len(r['releases']),4)
        self.assertTrue(all(x['anonymous_integrity']=='VERIFIED' and x['restore_byte_equality'] for x in r['releases']))
        self.assertEqual(r['independent_witness'],'NOT_PERFORMED')
        self.assertEqual(r['production_readiness'],'NOT_ESTABLISHED')
        self.assertEqual(len(list((self.root/'run').glob('*/v*/evidence.opk.zip'))),4)
        self.assertFalse(list((self.root/'run').rglob('*.key')))

    def test_existing_repository_is_never_modified(self):
        self.gateway.repos['example/opk-demo-two']={'full_name':'example/opk-demo-two','private':False}
        with self.assertRaisesRegex(ValueError,'already exists'): self.apply()
        self.assertFalse(any(c[0] in ('POST','PATCH','PUT','gh') for c in self.gateway.calls))

    def test_draft_corruption_stops_before_publication(self):
        self.gateway.corrupt_draft=True
        with self.assertRaises(ValueError): self.apply()
        self.assertTrue(all(v['draft'] for v in self.gateway.releases.values()))
        r=json.loads((self.root/'run'/'pilot-report.json').read_text())
        self.assertEqual(r['status'],'FAIL')
        self.assertEqual(r['releases'][0]['state'],'DRAFT_CREATED')

    def test_unconfirmed_immutable_setting_stops_publication(self):
        self.gateway.disable_immutable=True
        with self.assertRaisesRegex(ValueError,'immutab'): self.apply()
        self.assertEqual(len(self.gateway.releases),0)

    def test_post_publication_failure_is_not_reported_as_rollback(self):
        self.gateway.fail_attestation=True
        with self.assertRaises(ValueError): self.apply()
        r=json.loads((self.root/'run'/'pilot-report.json').read_text())
        self.assertEqual(r['status'],'FAIL')
        self.assertEqual(r['releases'][0]['state'],'PUBLIC_VERIFICATION_PENDING')
        self.assertFalse(next(iter(self.gateway.releases.values()))['draft'])

    def test_old_version_mutation_is_detected_after_v2(self):
        self.gateway.drift_v1=True
        with self.assertRaises(ValueError): self.apply()
        r=json.loads((self.root/'run'/'pilot-report.json').read_text())
        self.assertEqual(r['status'],'FAIL')

    def test_existing_output_is_not_touched(self):
        (self.root/'run').mkdir(); (self.root/'run'/'keep').write_text('unchanged')
        with self.assertRaisesRegex(ValueError,'output'): self.apply()
        self.assertEqual((self.root/'run'/'keep').read_text(),'unchanged')
        self.assertEqual(self.gateway.calls,[])
