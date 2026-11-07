"""Independent archive custody must fail closed on missing or replaced records."""
from __future__ import annotations

import hashlib
import json
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
sys.path.insert(0, str(ROOT / 'scripts'))


class CustodyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.authority = test_timestamp.Authority(cls.root / 'authority')
        cls.policy = cls.root / 'policy.json'
        cls.policy.write_text(json.dumps(cls.authority.policy()), encoding='utf-8')
        cls.helpers = []
        cls.signed_archives = {}
        for version in ('v1', 'v2'):
            helper = test_release.ReleaseBundleTests()
            helper.setUp()
            cls.helpers.append(helper)
            helper.metadata['version'] = version
            helper.write_metadata()
            helper.make_bundle()
            query = cls.root / (version + '.tsq')
            response = cls.root / (version + '.tsr')
            for args in (('request', helper.bundle, '--policy', cls.policy, '--out', query),):
                result = subprocess.run([sys.executable, str(ROOT / 'scripts/timestamp.py'), *map(str, args)],
                                        capture_output=True, text=True, timeout=30)
                if result.returncode:
                    raise RuntimeError(result.stderr)
            cls.authority.sign(query, response)
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/timestamp.py'),
                                     'attach', str(helper.bundle), '--policy', str(cls.policy),
                                     '--query', str(query), '--response', str(response)],
                                    capture_output=True, text=True, timeout=30)
            if result.returncode:
                raise RuntimeError(result.stderr)
            import preserve
            archive = cls.root / (version + '.opk.zip')
            preserve.pack(helper.bundle, archive, cls.policy)
            cls.signed_archives[version] = archive

    @classmethod
    def tearDownClass(cls):
        for helper in cls.helpers:
            helper.tearDown()
        cls.temp.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.sources = self.work / 'incoming'
        self.sources.mkdir()
        self.entries = []
        for version, original in self.signed_archives.items():
            copy = self.sources / original.name
            shutil.copyfile(original, copy)
            self.entries.append((version, copy, hashlib.sha256(copy.read_bytes()).hexdigest()))
        self.store = self.work / 'custodian'
        import custody
        self.custody = custody

    def deposit(self, entries=None):
        return self.custody.deposit('example/science-paper', self.entries if entries is None else entries,
                                    self.store, self.policy)

    def audit(self, catalog_sha):
        return self.custody.audit('example/science-paper', self.store, catalog_sha, self.policy)

    def test_two_versions_deposit_and_audit_full_rfc3161(self):
        receipt = self.deposit()
        self.assertEqual(receipt['status'], 'PASS')
        self.assertEqual(receipt['archive_count'], 2)
        self.assertEqual(receipt['offsite_custody'], 'NOT_ATTESTED')
        catalog = json.loads((self.store / 'custody.json').read_text())
        self.assertEqual([x['version'] for x in catalog['entries']], ['v1', 'v2'])
        result = self.audit(receipt['catalog_sha256'])
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['timestamp'], 'VERIFIED_USING_CURRENT_POLICY')
        self.assertEqual(result['durability'], 'NOT_PROVEN')
        self.assertEqual(result['repository'], 'example/science-paper')

    def test_deposit_requires_known_archive_hash(self):
        rows = list(self.entries)
        rows[0] = (rows[0][0], rows[0][1], '0' * 64)
        with self.assertRaisesRegex(ValueError, 'archive SHA-256 mismatch'):
            self.deposit(rows)
        self.assertFalse(self.store.exists())

    def test_deposit_rejects_wrong_repository(self):
        with self.assertRaisesRegex(ValueError, 'source identity mismatch'):
            self.custody.deposit('example/another-paper', self.entries, self.store, self.policy)
        self.assertFalse(self.store.exists())

    def test_deposit_rejects_mislabeled_version(self):
        row = self.entries[0]
        with self.assertRaisesRegex(ValueError, 'source identity mismatch'):
            self.deposit([('v99', row[1], row[2])])
        self.assertFalse(self.store.exists())

    def test_deposit_refuses_duplicate_versions(self):
        with self.assertRaisesRegex(ValueError, 'duplicate version'):
            self.deposit([self.entries[0], self.entries[0]])
        self.assertFalse(self.store.exists())

    def test_deposit_never_overwrites_existing_store(self):
        self.store.mkdir()
        (self.store / 'important').write_text('keep', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.deposit()
        self.assertEqual((self.store / 'important').read_text(), 'keep')

    def test_audit_rejects_replaced_or_deleted_archive(self):
        receipt = self.deposit()
        (self.store / 'v1.opk.zip').write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'archive SHA-256 mismatch'):
            self.audit(receipt['catalog_sha256'])
        (self.store / 'v1.opk.zip').unlink()
        with self.assertRaisesRegex(ValueError, 'missing|contents'):
            self.audit(receipt['catalog_sha256'])

    def test_audit_rejects_catalog_rewrite_even_with_mirroring_attack(self):
        receipt = self.deposit()
        catalog = self.store / 'custody.json'
        data = json.loads(catalog.read_text())
        data['entries'][0]['archive_sha256'] = '0' * 64
        catalog.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'catalog SHA-256 mismatch'):
            self.audit(receipt['catalog_sha256'])

    def test_audit_rejects_unlisted_file(self):
        receipt = self.deposit()
        (self.store / 'secret.key').write_bytes(b'UNEXPECTED')
        with self.assertRaisesRegex(ValueError, 'unexpected|contents'):
            self.audit(receipt['catalog_sha256'])

    def test_audit_rejects_symlink(self):
        receipt = self.deposit()
        (self.store / 'v1.opk.zip').unlink()
        (self.store / 'v1.opk.zip').symlink_to(self.sources / 'v1.opk.zip')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.audit(receipt['catalog_sha256'])

    def test_audit_requires_externally_pinned_catalog(self):
        receipt = self.deposit()
        with self.assertRaisesRegex(ValueError, 'catalog SHA-256'):
            self.audit('not a hash')
        self.assertTrue(receipt['catalog_sha256'])

    def test_modified_zip_internal_manifest_rejected_even_with_new_archive_pin(self):
        row = self.entries[0]
        filename = row[1]
        with zipfile.ZipFile(filename) as zip_file:
            contents = {name: zip_file.read(name) for name in zip_file.namelist()}
        contents['bundle/paper.pdf'] += b'EDITED'
        with zipfile.ZipFile(filename, 'w', compression=zipfile.ZIP_STORED) as zip_file:
            for name, content in contents.items():
                zip_file.writestr(name, content)
        new_pin = hashlib.sha256(filename.read_bytes()).hexdigest()
        with self.assertRaises((ValueError, zipfile.BadZipFile)):
            self.deposit([(row[0], filename, new_pin)])
        self.assertFalse(self.store.exists())

    def test_audit_fails_closed_on_wrong_repository_type(self):
        receipt = self.deposit()
        catalog_file = self.store / 'custody.json'
        payload = json.loads(catalog_file.read_text())
        payload['repository'] = 12
        catalog_file.write_text(json.dumps(payload), encoding='utf-8')
        altered_pin = hashlib.sha256(catalog_file.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, 'repository identity mismatch'):
            self.audit(altered_pin)

    def test_current_crl_expiry_blocks_audit(self):
        receipt = self.deposit()
        self.authority.make_crl(stale=True)
        try:
            with self.assertRaises(ValueError):
                self.audit(receipt['catalog_sha256'])
        finally:
            self.authority.make_crl()

    def test_cli_deposit_and_audit_report_explicit_limits(self):
        command = [sys.executable, str(ROOT / 'scripts/custody.py'), 'deposit',
                   '--repository', 'example/science-paper', '--out', str(self.store),
                   '--policy', str(self.policy)]
        for version, archive, expected in self.entries:
            command += ['--entry', version, str(archive), expected]
        result = subprocess.run(command, capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['offsite_custody'], 'NOT_ATTESTED')
        audit = subprocess.run([sys.executable, str(ROOT / 'scripts/custody.py'), 'audit',
                                '--repository', 'example/science-paper', '--store', str(self.store),
                                '--catalog-sha256', report['catalog_sha256'],
                                '--policy', str(self.policy)],
                               capture_output=True, text=True, timeout=45)
        self.assertEqual(audit.returncode, 0, audit.stderr)
        checked = json.loads(audit.stdout)
        self.assertEqual(checked['archive_count'], 2)
        self.assertEqual(checked['durability'], 'NOT_PROVEN')

    def test_audit_does_not_modify_store(self):
        receipt = self.deposit()
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.store.iterdir()}
        self.audit(receipt['catalog_sha256'])
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.store.iterdir()}
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
