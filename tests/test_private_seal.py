"""Only synthetic bytes are used as stand-ins for private records."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import private_seal as private_seal_module


class PrivateSealTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'repo'
        self.outside = Path(self.tmp.name) / 'private'
        self.root.mkdir();self.outside.mkdir()
        (self.root / 'scripts').mkdir()
        source = ROOT / 'scripts' / 'private_seal.py'
        if source.exists():
            shutil.copy2(source, self.root / 'scripts' / 'private_seal.py')
        self.original = self.outside / 'synthetic-not-real.txt'
        self.original.write_bytes(b'completely synthetic data\n')
        self.key = self.outside / 'key.bin'
        self.win_acl = os.name == 'nt'
        self.acl_root = Path(self.tmp.name) / 'private-acl'
        if self.win_acl:
            self.acl_root.mkdir()
            snapshot = private_seal_module._windows_acl_snapshot(self.acl_root)
            self.windows_user_sid = snapshot['currentUserSid']
            self._set_test_acl(self.acl_root)
            os.replace(self.original, self.acl_root / self.original.name)
            self.original = self.acl_root / self.original.name
            self.outside.rmdir()
            self.outside = self.acl_root
            self.key = self.outside / 'key.bin'

    def _set_test_acl(self, path, *, inheritable=False, extra_sids=()):
        if not self.win_acl:
            self.skipTest('Windows DACL test requires Windows')
        inherit = 'OICI' if inheritable else ''
        rules = [f'(A;{inherit};FA;;;{self.windows_user_sid})',
                 f'(A;{inherit};FA;;;S-1-5-18)', f'(A;{inherit};FA;;;S-1-5-32-544)']
        for sid, rights in extra_sids:
            if rights != 'RX':
                raise ValueError(f'unsupported synthetic Windows ACL rights: {rights}')
            rules.append(f'(A;{inherit};0x1200a9;;;{sid})')
        sddl = f'O:{self.windows_user_sid}G:{self.windows_user_sid}D:P' + ''.join(rules)
        private_seal_module._windows_replace_acl(path, sddl)
        snapshot = private_seal_module._windows_acl_snapshot(path)
        self.assertEqual(snapshot['ownerSid'], self.windows_user_sid, snapshot)

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(self.root / 'scripts' / 'private_seal.py'), *map(str,args)],
                              capture_output=True, text=True, check=False)

    def seal(self):
        return self.run_cli('seal', self.original, '--key-output', self.key)

    def test_seal_creates_anonymous_receipt_and_private_key(self):
        result = self.seal()
        self.assertEqual(result.returncode, 0, result.stderr)
        receipts = list((self.root / 'evidence' / 'commitments').glob('*.json'))
        self.assertEqual(len(receipts), 1)
        receipt = json.loads(receipts[0].read_text())
        self.assertEqual(len(receipt['record_id']), 32)
        self.assertEqual(len(receipt['commitment']), 64)
        self.assertEqual(len(self.key.read_bytes()), 32)
        if os.name == 'posix':
            self.assertFalse(self.key.stat().st_mode & 0o077)
        elif not self.win_acl:
            self.skipTest('private key permission semantics are platform-specific')
        else:
            snapshot = private_seal_module._windows_acl_snapshot(self.key)
            self.assertTrue(private_seal_module._windows_acl_is_private(snapshot), snapshot)
        self.assertNotIn(str(self.original), receipts[0].read_text())
        self.assertNotIn('synthetic', receipts[0].read_text())
        self.assertNotIn(self.key.read_bytes().hex(), receipts[0].read_text())
        self.assertEqual(self.run_cli('verify', self.original, '--key', self.key, '--receipt', receipts[0]).returncode, 0)

    def test_localized_group_display_names_cannot_bypass_wide_read_sid(self):
        if not self.win_acl:
            self.skipTest('Windows localized trustee-name scenario requires Windows')
        # Display labels deliberately vary; the actual DACL trustee stays the
        # stable Builtin Users SID, which is what the implementation inspects.
        labels = ('BUILTIN\\Users [en-US]', 'BUILTIN\\Benutzer [de-DE]',
                  'BUILTIN\\利用者 [ja-JP]', 'BUILTIN\\Utilisateurs [fr-FR]')
        for label in labels:
            with self.subTest(display_name=label):
                self._set_test_acl(self.acl_root, extra_sids=(('S-1-5-32-545', 'RX'),))
                with self.assertRaisesRegex(ValueError, 'Windows ACL is unsafe or unknown'):
                    private_seal_module._require_windows_private_acl(
                        self.acl_root, allow_trusted_inheritance=True)
                result = self.seal()
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('ValueError', result.stderr)
                self.assertFalse(self.key.exists(), 'secret key must not be created under a broad read ACE')
                self.assertFalse((self.root / 'evidence' / 'commitments').exists())

    def test_inherited_broad_read_ace_is_rejected_before_key_creation(self):
        if not self.win_acl:
            self.skipTest('Windows inherited DACL test requires Windows')
        inherited = self.acl_root / 'inherited'
        self._set_test_acl(self.acl_root, inheritable=True,
                           extra_sids=(('S-1-5-32-545', 'RX'),))
        inherited.mkdir()
        original = inherited / 'synthetic-not-real.txt'
        original.write_bytes(b'completely synthetic inherited-DACL fixture\n')
        key = inherited / 'key.bin'
        with self.assertRaisesRegex(ValueError, 'Windows ACL is unsafe or unknown'):
            private_seal_module._require_windows_private_acl(
                inherited, allow_trusted_inheritance=True)
        result = self.run_cli('seal', original, '--key-output', key)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('ValueError', result.stderr)
        self.assertFalse(key.exists(), 'secret key must not be created with inherited broad read')
        self.assertFalse((self.root / 'evidence' / 'commitments').exists())

    def test_unknown_trustee_sid_is_rejected_before_key_creation(self):
        if not self.win_acl:
            self.skipTest('Windows unknown-trustee DACL test requires Windows')
        self._set_test_acl(self.acl_root, extra_sids=(('S-1-5-4', 'RX'),))
        with self.assertRaisesRegex(ValueError, 'Windows ACL is unsafe or unknown'):
            private_seal_module._require_windows_private_acl(
                self.acl_root, allow_trusted_inheritance=True)
        result = self.seal()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse(self.key.exists(), 'unknown trustee must not receive access to a new secret key')
        self.assertFalse((self.root / 'evidence' / 'commitments').exists())

    def test_modified_record_is_rejected(self):
        self.assertEqual(self.seal().returncode, 0)
        receipt = next((self.root / 'evidence' / 'commitments').glob('*.json'))
        self.original.write_bytes(b'modified\n')
        result = self.run_cli('verify', self.original, '--key', self.key, '--receipt', receipt)
        self.assertNotEqual(result.returncode, 0)

    def test_wrong_key_is_rejected(self):
        self.assertEqual(self.seal().returncode, 0)
        receipt = next((self.root / 'evidence' / 'commitments').glob('*.json'))
        self.key.write_bytes(b'Z' * 32)
        self.assertNotEqual(self.run_cli('verify', self.original, '--key', self.key, '--receipt', receipt).returncode, 0)

    def test_source_and_key_must_be_outside_public_repo(self):
        in_repo = self.root / 'sensitive.txt'
        in_repo.write_bytes(b'private')
        self.assertNotEqual(self.run_cli('seal', in_repo, '--key-output', self.key).returncode, 0)
        self.assertNotEqual(self.run_cli('seal', self.original, '--key-output', self.root/'secret.key').returncode, 0)

    def test_key_is_never_overwritten(self):
        self.key.write_bytes(b'existing')
        result = self.seal()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.key.read_bytes(), b'existing')


if __name__ == '__main__': unittest.main()
