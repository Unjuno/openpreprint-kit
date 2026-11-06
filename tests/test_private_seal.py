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
        self.assertFalse(self.key.stat().st_mode & 0o077)
        self.assertNotIn(str(self.original), receipts[0].read_text())
        self.assertNotIn('synthetic', receipts[0].read_text())
        self.assertNotIn(self.key.read_bytes().hex(), receipts[0].read_text())
        self.assertEqual(self.run_cli('verify', self.original, '--key', self.key, '--receipt', receipts[0]).returncode, 0)

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
