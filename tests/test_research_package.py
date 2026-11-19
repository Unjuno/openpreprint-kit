"""Research object tests use entirely synthetic, non-health data."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

import yaml
import test_release as release_fixture
SOURCE_ROOT = release_fixture.SOURCE_ROOT


class ResearchBundleTests(unittest.TestCase):
    def setUp(self):
        # Reuse fixture construction without repeating every legacy test case.
        self.helper = release_fixture.ReleaseBundleTests()
        self.helper.setUp()
        self.root = self.helper.root
        self.bundle = self.helper.bundle
        for filename in ('research_package.py', 'verify_research.py'):
            src = SOURCE_ROOT / 'scripts' / filename
            if src.exists():
                shutil.copy2(src, self.root / 'scripts' / filename)
        (self.root / 'data').mkdir()
        (self.root / 'analysis').mkdir()
        (self.root / 'data' / 'synthetic.csv').write_text('x,y\n1,2\n', encoding='utf-8')
        (self.root / 'analysis' / 'fit.py').write_text('print(2)\n', encoding='utf-8')
        self.configuration = {
            'schema_version': 1,
            'public_assets': [
                {'path': 'data/synthetic.csv', 'role': 'dataset', 'description': 'Synthetic data only', 'license': 'CC0-1.0', 'public_confirmed': True},
                {'path': 'analysis/fit.py', 'role': 'analysis_code', 'description': 'Reproduction script', 'license': 'MIT', 'public_confirmed': True},
            ],
            'relations': [{'source': 'analysis/fit.py', 'target': 'data/synthetic.csv', 'kind': 'analyzes'}],
        }
        self.save_config()

    def tearDown(self):
        self.helper.tearDown()

    def run_script(self, name, *args):
        return self.helper.run_script(name, *args)

    def make_bundle(self):
        result = self.run_script('prepare_release.py', '--output', self.bundle,
                                 '--repository', 'example/science-paper',
                                 '--commit', 'a' * 40)
        self.assertEqual(result.returncode, 0, result.stderr)

    def save_config(self):
        (self.root / 'research-assets.yaml').write_text(yaml.safe_dump(self.configuration), encoding='utf-8')

    def test_public_files_bundle_and_verify(self):
        self.make_bundle()
        manifest = json.loads((self.bundle / 'manifest.json').read_text(encoding='utf-8'))
        self.assertIn('research-assets.tar', manifest['files'])
        self.assertIn('research-assets.json', manifest['files'])
        catalog = json.loads((self.bundle / 'research-assets.json').read_text(encoding='utf-8'))
        self.assertEqual([x['path'] for x in catalog['entries']], ['analysis/fit.py', 'data/synthetic.csv'])
        self.assertEqual(catalog['relations'][0]['kind'], 'analyzes')
        with tarfile.open(self.bundle / 'research-assets.tar', mode='r:') as archive:
            self.assertEqual(sorted(m.name for m in archive.getmembers()), ['analysis/fit.py', 'data/synthetic.csv'])
        result = self.run_script('verify_release.py', self.bundle)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_research_bundle_is_deterministic(self):
        self.make_bundle()
        first = (self.bundle / 'research-assets.tar').read_bytes()
        first_json = (self.bundle / 'research-assets.json').read_bytes()
        shutil.rmtree(self.bundle)
        self.make_bundle()
        self.assertEqual(first, (self.bundle / 'research-assets.tar').read_bytes())
        self.assertEqual(first_json, (self.bundle / 'research-assets.json').read_bytes())

    def test_changed_data_is_detected(self):
        self.make_bundle()
        with (self.bundle / 'research-assets.tar').open('ab') as out:
            out.write(b'ADDED')
        result = self.run_script('verify_release.py', self.bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('checksum', result.stderr)

    def test_missing_public_file_fails_closed(self):
        (self.root / 'analysis' / 'fit.py').unlink()
        result = self.run_script('prepare_release.py', '--output', self.bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.bundle / 'manifest.json').exists())

    def test_private_file_path_is_rejected(self):
        self.configuration['public_assets'][0]['path'] = '../private/patient.json'
        self.save_config()
        result = self.run_script('prepare_release.py', '--output', self.bundle)
        self.assertNotEqual(result.returncode, 0)

    def test_ci_can_check_research_manifest_without_publishing(self):
        check = self.run_script('research_package.py', '--check')
        self.assertEqual(check.returncode, 0, check.stderr)
        (self.root / 'data' / 'synthetic.csv').unlink()
        bad = self.run_script('research_package.py', '--check')
        self.assertNotEqual(bad.returncode, 0)

    def test_unconfirmed_public_data_is_rejected(self):
        self.configuration['public_assets'][0]['public_confirmed'] = False
        self.save_config()
        result = self.run_script('prepare_release.py', '--output', self.bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('public_confirmed', result.stderr)

    def test_duplicate_public_confirmation_is_rejected(self):
        path = self.root / "research-assets.yaml"
        source = path.read_text(encoding="utf-8")
        self.assertIn("public_confirmed: true", source)
        source = source.replace("  public_confirmed: true", "  public_confirmed: false\n  public_confirmed: true", 1)
        path.write_text(source, encoding="utf-8")
        result = self.run_script("research_package.py", "--check")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("duplicate", result.stderr.lower())

    def test_unlisted_data_is_rejected_to_prevent_incomplete_catalog(self):
        (self.root / 'data' / 'unlisted.csv').write_text('secret?\n', encoding='utf-8')
        result = self.run_script('prepare_release.py', '--output', self.bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('undeclared research file', result.stderr)

    def test_invalid_relation_fails(self):
        self.configuration['relations'][0]['target'] = 'data/not-there.csv'
        self.save_config()
        self.assertNotEqual(self.run_script('prepare_release.py', '--output', self.bundle).returncode, 0)

    def test_symlinked_dataset_is_rejected(self):
        if os.name == 'nt' and not os.environ.get('OPK_WINDOWS_SYMLINK_TESTS'):
            self.skipTest('enable OPK_WINDOWS_SYMLINK_TESTS on a Windows runner with symlink privilege')
        (self.root / 'data' / 'synthetic.csv').unlink()
        external = self.root.parent / (self.root.name + '-outside.csv')
        external.write_bytes(b'not-public')
        try:
            try:
                (self.root / 'data' / 'synthetic.csv').symlink_to(external)
            except OSError as exc:
                if os.name == 'nt' and getattr(exc, 'winerror', None) == 1314:
                    self.skipTest('Windows symlink privilege unavailable')
                raise
            self.assertNotEqual(self.run_script('prepare_release.py', '--output', self.bundle).returncode, 0)
        finally:
            external.unlink()

    # --- safe_read_bytes unit tests (POSIX containment walking + Windows handle check) ---

    def _import_rp(self):
        import importlib
        return importlib.import_module('research_package')

    def test_safe_read_returns_regular_file_bytes(self):
        rp = self._import_rp()
        target = self.root / 'data' / 'synthetic.csv'
        self.assertEqual(rp.safe_read_bytes(self.root, 'data/synthetic.csv'),
                         target.read_bytes())

    def test_safe_read_rejects_leaf_symlink(self):
        if not hasattr(os, 'symlink'):
            self.skipTest('no symlink support on this host')
        rp = self._import_rp()
        (self.root / 'data' / 'synthetic.csv').unlink()
        external = self.root.parent / (self.root.name + '-outside.csv')
        external.write_bytes(b'secret')
        try:
            try:
                (self.root / 'data' / 'synthetic.csv').symlink_to(external)
            except OSError as exc:
                if getattr(exc, 'winerror', None) == 1314:
                    self.skipTest('Windows symlink privilege unavailable')
                raise
            with self.assertRaises((OSError, ValueError)):
                rp.safe_read_bytes(self.root, 'data/synthetic.csv')
        finally:
            (self.root / 'data').mkdir(exist_ok=True) if not (self.root / 'data').exists() else None
            (self.root / 'data' / 'synthetic.csv').unlink(missing_ok=True)
            external.unlink()

    def test_safe_read_rejects_ancestor_junction(self):
        if sys.platform != 'win32':
            self.skipTest('junction check is Windows-specific')
        rp = self._import_rp()
        outside = self.root.parent / (self.root.name + '-ancestor')
        outside.mkdir()
        (outside / 'synthetic.csv').write_bytes(b'outsider')
        original = self.root / 'data'
        target = outside
        try:
            import shutil as _shutil
            _shutil.move(str(original), str(target / 'data-moved'))
            res = subprocess.run(['cmd', '/c', 'mklink', '/J', str(original), str(target)],
                                 capture_output=True)
            if res.returncode:
                self.skipTest('junction creation unavailable on this host')
            with self.assertRaises((OSError, ValueError)):
                rp.safe_read_bytes(self.root, 'data/synthetic.csv')
        finally:
            (self.root / 'data').unlink() if (self.root / 'data').is_symlink() or getattr(self.root / 'data', 'is_junction', lambda: False)() else None
            # restore original directory
            if not (self.root / 'data').exists():
                (target / 'data-moved').rename(original)

    def test_forged_tar_member_rejected_even_after_manifest_rehash(self):
        # Rehashing outer checksums cannot make an extra undeclared TAR member valid.
        self.make_bundle()
        from io import BytesIO
        with tarfile.open(self.bundle / 'research-assets.tar', mode='a') as tar:
            info = tarfile.TarInfo('data/undeclared.csv')
            payload = b'forged'
            info.size = len(payload)
            tar.addfile(info, BytesIO(payload))
        # A malicious actor can update every ordinary SHA digest, but not a prior RFC 3161 stamp.
        manifest_file = self.bundle / 'manifest.json'
        manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
        archive = self.bundle / 'research-assets.tar'
        manifest['files'][archive.name]['sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
        manifest['files'][archive.name]['size_bytes'] = archive.stat().st_size
        manifest_file.write_text(json.dumps(manifest, sort_keys=True, indent=2) + '\n')
        sums = [f'{hashlib.sha256((self.bundle / p).read_bytes()).hexdigest()}  {p}\n'
                for p in sorted(set(manifest['files']) | {'manifest.json'})]
        (self.bundle / 'SHA256SUMS').write_text(''.join(sums))
        result = self.run_script('verify_release.py', self.bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('undeclared', result.stderr)

    def test_private_commitment_included_but_no_secret(self):
        receipts = self.root / 'evidence' / 'commitments'
        receipts.mkdir(parents=True)
        rid = 'a' * 32
        receipt = {'schema_version': 1, 'record_id': rid, 'algorithm': 'HMAC-SHA256', 'commitment': 'b' * 64}
        (receipts / (rid + '.json')).write_text(json.dumps(receipt))
        self.make_bundle()
        catalog = json.loads((self.bundle / 'research-assets.json').read_text(encoding='utf-8'))
        private = [e for e in catalog['entries'] if e['role'] == 'private_commitment']
        self.assertEqual(len(private), 1)
        archive_data = (self.bundle / 'research-assets.tar').read_bytes()
        self.assertNotIn(b'patient', archive_data)
        self.assertNotIn(b'private-secret', archive_data)
        self.assertEqual(self.run_script('verify_release.py', self.bundle).returncode, 0)

    def test_malformed_private_commitment_rejected(self):
        receipts = self.root / 'evidence' / 'commitments'
        receipts.mkdir(parents=True)
        (receipts / ('a' * 32 + '.json')).write_text('{"patient_name":"PRIVATE"}')
        self.assertNotEqual(self.run_script('prepare_release.py', '--output', self.bundle).returncode, 0)


if __name__ == '__main__':
    unittest.main()

