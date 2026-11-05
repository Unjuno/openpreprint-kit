"""Public data are selected explicitly; integrity is not an external trust anchor."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import zipfile

import test_release

SOURCE = Path(__file__).resolve().parents[1]


def public_artifact(identifier='measurements', path='data/measurements.csv', kind='dataset'):
    return dict(id=identifier, kind=kind, visibility='public', path=path, version='1',
                title='Synthetic measurements', description='time_s [s], value [1]. Synthetic only.',
                license='CC0-1.0', sensitivity='non-sensitive', publication_approved=True)


def rehash(folder):
    p = folder / 'manifest.json'; data = json.loads(p.read_text())
    for name in data['files']:
        raw = (folder / name).read_bytes()
        data['files'][name] = dict(sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))
    p.write_text(json.dumps(data, sort_keys=True))
    (folder / 'SHA256SUMS').write_text(''.join(
        hashlib.sha256((folder / n).read_bytes()).hexdigest() + '  ' + n + '\n'
        for n in sorted(set(data['files']) | {'manifest.json'})))


class ResearchBundleTests(unittest.TestCase):
    def setUp(self):
        self.h = test_release.ReleaseBundleTests(); self.h.setUp()
        self.root, self.bundle = self.h.root, self.h.bundle
        for p in (SOURCE / 'scripts').glob('*.py'):
            shutil.copy2(p, self.root / 'scripts' / p.name)
        (self.root / 'data').mkdir()
        (self.root / 'data/measurements.csv').write_bytes(b'time_s,value\n0,12\n1,13\n')
        self.spec = dict(schema_version=1, artifacts=[public_artifact()], activities=[])
        self.save()

    def tearDown(self): self.h.tearDown()
    def save(self): (self.root / 'research.json').write_text(json.dumps(self.spec), encoding='utf-8')
    def build(self):
        self.save(); self.h.make_bundle()
        self.assertTrue((self.bundle / 'research-manifest.json').is_file(), 'research inventory not packaged')
        return json.loads((self.bundle / 'research-manifest.json').read_text())
    def reject(self):
        self.save(); r = self.h.run_script('prepare_release.py', '--output', self.bundle)
        self.assertEqual(r.returncode, 1, r.stdout); self.assertNotIn('Traceback', r.stderr)
    def verify(self, *args): return self.h.run_script('verify_release.py', self.bundle, *args)
    def index_save(self, index):
        (self.bundle / 'research-manifest.json').write_text(json.dumps(index)); rehash(self.bundle)

    def test_roundtrip_binds_exact_paper_and_data(self):
        index = self.build(); item = index['artifacts'][0]
        self.assertEqual(index['paper_sha256'], hashlib.sha256(self.h.paper.read_bytes()).hexdigest())
        self.assertEqual(index['paper_version'], 'v1')
        with zipfile.ZipFile(self.bundle / 'research-data.zip') as z:
            self.assertEqual(z.read(item['archive_path']), (self.root / 'data/measurements.csv').read_bytes())
        self.assertEqual(json.loads((self.bundle / 'manifest.json').read_text())['schema_version'], 2)
        self.assertEqual(self.verify().returncode, 0)

    def test_same_inputs_produce_identical_snapshot(self):
        self.build(); before = {p.name: p.read_bytes() for p in self.bundle.iterdir()}
        shutil.rmtree(self.bundle); self.build()
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.bundle.iterdir()})

    def test_health_classified_public_file_is_rejected(self):
        self.spec['artifacts'][0]['sensitivity'] = 'health'; self.reject()
    def test_missing_explicit_publication_approval_is_rejected(self):
        self.spec['artifacts'][0]['publication_approved'] = False; self.reject()
    def test_string_approval_is_not_boolean(self):
        self.spec['artifacts'][0]['publication_approved'] = 'true'; self.reject()
    def test_duplicate_ids_are_rejected(self):
        self.spec['artifacts'] *= 2; self.reject()
    def test_boolean_schema_is_rejected(self): self.spec['schema_version'] = True; self.reject()
    def test_unknown_fields_are_rejected(self): self.spec['artifacts'][0]['patient_name'] = 'SYNTHETIC'; self.reject()
    def test_parent_path_is_rejected(self): self.spec['artifacts'][0]['path'] = '../outside.csv'; self.reject()
    def test_hidden_path_is_rejected(self): self.spec['artifacts'][0]['path'] = '.env'; self.reject()
    def test_missing_data_is_rejected(self): self.spec['artifacts'][0]['path'] = 'data/absent.csv'; self.reject()
    def test_internal_symlink_is_rejected(self):
        p = self.root / 'data/link.csv'; p.symlink_to(self.root / 'data/measurements.csv')
        self.spec['artifacts'][0]['path'] = 'data/link.csv'; self.reject()
    def test_symlink_parent_is_rejected(self):
        (self.root / 'alias').symlink_to(self.root / 'data', target_is_directory=True)
        self.spec['artifacts'][0]['path'] = 'alias/measurements.csv'; self.reject()
    def test_oversized_data_is_rejected(self):
        with (self.root / 'data/measurements.csv').open('wb') as f: f.truncate(25*1024*1024+1)
        self.reject()
    def test_duplicate_json_is_rejected(self):
        (self.root / 'research.json').write_text('{"schema_version":1,"schema_version":1,"artifacts":[],"activities":[]}')
        r = self.h.run_script('prepare_release.py', '--output', self.bundle)
        self.assertEqual(r.returncode, 1)

    def activity(self, inputs, outputs):
        return dict(id='analysis', inputs=inputs, outputs=outputs, code=[], environment=[],
                    command='No code is executed by the kit', description='Author-declared derivation')
    def test_declared_lineage_is_recorded_not_executed(self):
        self.spec['activities'] = [self.activity(['measurements'], ['paper'])]
        index = self.build(); self.assertEqual(index['provenance_status'], 'DECLARED_NOT_EXECUTED')
        self.assertEqual(index['activities'][0]['outputs'], ['paper'])
    def test_unknown_input_reference_is_rejected(self):
        self.spec['activities'] = [self.activity(['missing'], ['paper'])]; self.reject()
    def test_self_cycle_is_rejected(self):
        self.spec['activities'] = [self.activity(['measurements'], ['measurements'])]; self.reject()
    def test_data_cannot_impersonate_code(self):
        a = self.activity(['measurements'], ['paper']); a['code'] = ['measurements']
        self.spec['activities'] = [a]; self.reject()
    def test_removed_research_asset_is_rejected(self):
        self.build(); (self.bundle / 'research-data.zip').unlink(); self.assertEqual(self.verify().returncode, 1)
    def test_changed_data_is_rejected_even_after_outer_rehash(self):
        index = self.build()
        with zipfile.ZipFile(self.bundle / 'research-data.zip', 'w') as z:
            z.writestr(index['artifacts'][0]['archive_path'], b'changed')
        rehash(self.bundle); self.assertEqual(self.verify().returncode, 1)
    def test_unlisted_zip_member_is_rejected(self):
        self.build()
        with zipfile.ZipFile(self.bundle / 'research-data.zip', 'a') as z: z.writestr('../secret', b'not allowed')
        rehash(self.bundle); self.assertEqual(self.verify().returncode, 1)
    def test_wrong_paper_binding_is_rejected_after_rehash(self):
        index = self.build(); index['paper_sha256'] = '0'*64; self.index_save(index)
        self.assertEqual(self.verify().returncode, 1)
    def test_wrong_version_binding_is_rejected_after_rehash(self):
        index = self.build(); index['paper_version'] = 'v999'; self.index_save(index)
        self.assertEqual(self.verify().returncode, 1)
    def test_external_manifest_pin_detects_complete_rewrite(self):
        index = self.build(); pin = hashlib.sha256((self.bundle / 'manifest.json').read_bytes()).hexdigest()
        self.assertEqual(self.verify('--expected-manifest-sha256', pin).returncode, 0)
        index['artifacts'][0]['description'] = 'changed'; self.index_save(index)
        self.assertEqual(self.verify().returncode, 0)
        self.assertEqual(self.verify('--expected-manifest-sha256', pin).returncode, 1)
    def test_verifier_uses_only_standard_library(self):
        self.build()
        r = subprocess.run([sys.executable, '-S', str(self.root / 'scripts/verify_release.py'), str(self.bundle)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == '__main__': unittest.main()
