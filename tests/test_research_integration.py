"""Mixed public/private evidence, actual test-TSA signatures and reader semantics."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import warnings
import zipfile

import test_research_bundle
import test_timestamp

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    sys.path.insert(0, str(ROOT / 'scripts'))
    spec = importlib.util.spec_from_file_location('opk_' + name, ROOT / 'scripts' / (name+'.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


class ResearchIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.h = test_research_bundle.ResearchBundleTests(); self.h.setUp()
        self.private = tempfile.TemporaryDirectory(); self.secure = Path(self.private.name)
        self.original = self.secure / 'synthetic-health.csv'
        self.original.write_bytes(b'SYNTHETIC_ONLY,36.5\n')
        self.receipt = self.secure / 'opening.opk-private.json'
        self.private_item = module('private_record').commit_record(self.original, self.receipt)
        self.h.spec['artifacts'].append(self.private_item)
    def tearDown(self): self.h.tearDown(); self.private.cleanup()

    def test_public_snapshot_contains_no_private_opening_or_health_bytes(self):
        index = self.h.build()
        blob = b''.join(p.read_bytes() for p in self.h.bundle.iterdir())
        nonce = json.loads(self.receipt.read_text())['nonce']
        for secret in (self.original.name.encode(), self.original.read_bytes(), nonce.encode(),
                       hashlib.sha256(self.original.read_bytes()).hexdigest().encode()):
            self.assertNotIn(secret, blob)
        self.assertEqual(index['artifacts'][1]['visibility'], 'private')
        self.assertEqual(self.h.verify().returncode, 0)

    def test_private_entry_cannot_smuggle_source_path(self):
        self.private_item['path'] = str(self.original); self.h.reject()

    def test_reader_shows_inventory_lineage_and_private_boundary(self):
        self.h.spec['artifacts'][0]['title'] = '<script>SYNTHETIC</script>'
        self.h.spec['activities'] = [self.h.activity(['measurements', self.private_item['id']], ['paper'])]
        self.h.build()
        (self.h.root / 'reviews').mkdir()
        (self.h.root / 'reviews/record.json').write_text('{"schema_version":1,"events":[]}')
        out = self.h.root / 'site'
        module('build_site').build_site(self.h.bundle, self.h.root, out, 'example/paper')
        text = (out / 'index.html').read_text()
        self.assertIn('Research data and declared provenance', text)
        self.assertIn('NOT_PUBLIC', text)
        self.assertIn('DECLARED_NOT_EXECUTED', text)
        self.assertIn('&lt;script&gt;SYNTHETIC&lt;/script&gt;', text)
        self.assertNotIn('<script>', text)
        self.assertNotIn(self.original.name, text)

    def test_actual_timestamp_rejects_rehashed_data_index(self):
        self.h.build()
        authority = test_timestamp.Authority(self.secure / 'authority')
        policy_path = self.secure / 'policy.json'; policy_path.write_text(json.dumps(authority.policy()))
        tsa = module('timestamp'); policy = tsa.load_policy(policy_path)
        query = tsa.make_query(self.h.bundle, policy)
        query_path = self.secure / 'query.tsq'; query_path.write_bytes(query)
        response = self.secure / 'response.tsr'; authority.sign(query_path, response)
        tsa.attach(self.h.bundle, query, response.read_bytes(), policy)
        report = tsa.verify_proof(self.h.bundle, query, response.read_bytes(), policy)
        self.assertEqual(report['status'], 'VERIFIED')
        item = json.loads((self.h.bundle / 'research-manifest.json').read_text())
        replacement = b'time_s,value\n0,999\n1,999\n'
        artifact = item['artifacts'][0]
        with zipfile.ZipFile(self.h.bundle / 'research-data.zip', 'w') as archive:
            archive.writestr(artifact['archive_path'], replacement)
        artifact['sha256'] = hashlib.sha256(replacement).hexdigest()
        artifact['size_bytes'] = len(replacement)
        self.h.index_save(item)
        self.assertEqual(self.h.verify().returncode, 0)
        with self.assertRaises(ValueError): tsa.verify_proof(self.h.bundle, query, response.read_bytes(), policy)

    def test_duplicate_zip_entries_are_rejected_after_outer_rehash(self):
        index = self.h.build()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with zipfile.ZipFile(self.h.bundle / 'research-data.zip', 'a') as z:
                z.writestr(index['artifacts'][0]['archive_path'], b'bad duplicate')
        test_research_bundle.rehash(self.h.bundle)
        self.assertEqual(self.h.verify().returncode, 1)

    def test_compressed_zip_entry_is_rejected(self):
        index = self.h.build()
        with zipfile.ZipFile(self.h.bundle / 'research-data.zip', 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(index['artifacts'][0]['archive_path'], (self.h.root / 'data/measurements.csv').read_bytes())
        test_research_bundle.rehash(self.h.bundle)
        self.assertEqual(self.h.verify().returncode, 1)

    def test_downgraded_manifest_rejected_by_independent_pin(self):
        self.h.build(); pin = hashlib.sha256((self.h.bundle / 'manifest.json').read_bytes()).hexdigest()
        m = json.loads((self.h.bundle / 'manifest.json').read_text()); m['schema_version'] = 1
        for name in ('research-manifest.json','research-data.zip'):
            del m['files'][name]; (self.h.bundle / name).unlink()
        (self.h.bundle / 'manifest.json').write_text(json.dumps(m)); test_research_bundle.rehash(self.h.bundle)
        self.assertEqual(self.h.verify().returncode, 0)  # Unanchored legacy integrity is not authenticity.
        self.assertEqual(self.h.verify('--expected-manifest-sha256', pin).returncode, 1)

    def test_publication_uploads_both_research_assets_and_reverifies(self):
        text = (ROOT / '.github/workflows/publish.yml').read_text()
        self.assertIn('dist/research-manifest.json', text)
        self.assertIn('dist/research-data.zip', text)
        self.assertIn('"${ASSETS[@]}"', text)
        self.assertLess(text.index('verify_release.py downloaded-release'), text.index('gh release edit'))

    def test_ci_checks_research_inventory(self):
        text = (ROOT / '.github/workflows/validate.yml').read_text()
        self.assertIn('python scripts/research_bundle.py', text)


if __name__ == '__main__': unittest.main()
