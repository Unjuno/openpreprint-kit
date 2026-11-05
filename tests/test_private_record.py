"""Synthetic-only tests. Real private records must never enter a Git tree."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/private_record.py'


class PrivateRecordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.source = self.root / 'SYNTHETIC-health.csv'
        self.source.write_bytes(b'synthetic_id,synthetic_value\nexample,36.5\n')
        self.receipt = self.root / 'opening.opk-private.json'
    def tearDown(self): self.tmp.cleanup()
    def module(self):
        self.assertTrue(SCRIPT.is_file(), 'private local commitment command not implemented')
        sys.path.insert(0, str(ROOT / 'scripts'))
        spec = importlib.util.spec_from_file_location('opk_private_test', SCRIPT)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
    def commit(self): return self.module().commit_record(self.source, self.receipt)
    def test_opening_matches_original(self):
        public = self.commit()
        self.module().verify_record(self.source, self.receipt, public['commitment']['digest'])
    def test_same_file_gets_distinct_randomized_commitments(self):
        first = self.commit(); self.receipt = self.root / 'second.opk-private.json'; second = self.commit()
        self.assertNotEqual(first['commitment']['digest'], second['commitment']['digest'])
        self.assertNotEqual(first['id'], second['id'])
    def test_changed_record_is_rejected(self):
        public = self.commit(); self.source.write_bytes(b'changed')
        with self.assertRaises(ValueError):
            self.module().verify_record(self.source, self.receipt, public['commitment']['digest'])
    def test_wrong_external_commitment_is_rejected(self):
        self.commit()
        with self.assertRaises(ValueError): self.module().verify_record(self.source, self.receipt, '0'*64)
    def test_changed_secret_is_rejected(self):
        public = self.commit(); r = json.loads(self.receipt.read_text()); r['nonce'] = '0'*64
        self.receipt.write_text(json.dumps(r))
        with self.assertRaises(ValueError):
            self.module().verify_record(self.source, self.receipt, public['commitment']['digest'])
    def test_changed_receipt_identifier_is_rejected(self):
        public = self.commit(); r = json.loads(self.receipt.read_text()); r['id'] = 'pr-' + 'a'*32
        self.receipt.write_text(json.dumps(r))
        with self.assertRaises(ValueError):
            self.module().verify_record(self.source, self.receipt, public['commitment']['digest'])
    def test_opening_is_created_private_and_not_overwritten(self):
        self.commit(); original = self.receipt.read_bytes()
        if os.name == 'posix': self.assertEqual(self.receipt.stat().st_mode & 0o777, 0o600)
        with self.assertRaises((ValueError, FileExistsError)): self.commit()
        self.assertEqual(original, self.receipt.read_bytes())
    def test_no_names_raw_digest_or_secret_in_public_artifact(self):
        public = self.commit(); encoded = json.dumps(public)
        private = json.loads(self.receipt.read_text())
        for value in (self.source.name, '36.5', private['nonce'], hashlib.sha256(self.source.read_bytes()).hexdigest()):
            self.assertNotIn(value, encoded)
        self.assertEqual(set(public), {'id','kind','visibility','commitment'})
    def test_original_in_git_tree_is_rejected(self):
        (self.root / '.git').mkdir()
        with self.assertRaises(ValueError): self.commit()
        self.assertFalse(self.receipt.exists())
    def test_receipt_in_git_tree_is_rejected(self):
        d = self.root / 'repo'; d.mkdir(); (d / '.git').write_text('gitdir: ../actual')
        self.receipt = d / 'opening.opk-private.json'
        with self.assertRaises(ValueError): self.commit()
    def test_source_symlink_is_rejected(self):
        link = self.root / 'link'; link.symlink_to(self.source); self.source = link
        with self.assertRaises(ValueError): self.commit()
    def test_receipt_symlink_is_rejected(self):
        self.receipt.symlink_to(self.root / 'missing')
        with self.assertRaises((ValueError, FileExistsError)): self.commit()
    def test_cli_emits_only_public_artifact(self):
        self.module()
        r = subprocess.run([sys.executable, str(SCRIPT), 'commit', str(self.source), '--receipt', str(self.receipt)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)['visibility'], 'private')
        self.assertNotIn(self.source.name, r.stdout+r.stderr)
        self.assertNotIn(json.loads(self.receipt.read_text())['nonce'], r.stdout+r.stderr)
    def test_cli_requires_an_external_commitment(self):
        self.commit()
        r = subprocess.run([sys.executable, str(SCRIPT), 'verify', str(self.source), '--receipt', str(self.receipt)], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)


if __name__ == '__main__': unittest.main()
