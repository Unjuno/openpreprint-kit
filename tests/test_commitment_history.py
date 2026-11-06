"""Git history guard for public anonymous commitment receipts."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'scripts' / 'commitment_history.py'
RID = 'f' * 32


class CommitmentHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Synthetic Test')
        self.folder = self.root / 'evidence' / 'commitments'
        self.folder.mkdir(parents=True)
        self.receipt = self.folder / (RID + '.json')
        self.receipt.write_text(json.dumps({'schema_version': 1, 'record_id': RID,
                                            'algorithm': 'HMAC-SHA256', 'commitment': 'a' * 64}))
        self.commit()
        self.base = self.git('rev-parse', 'HEAD').stdout.strip()

    def tearDown(self): self.tmp.cleanup()

    def git(self, *cmd):
        return subprocess.run(['git', '-C', str(self.root), *cmd], text=True, capture_output=True, check=True)

    def commit(self):
        self.git('add', '-A')
        self.git('commit', '-qm', 'synthetic snapshot')

    def check(self):
        return subprocess.run([sys.executable, str(SOURCE), '--root', str(self.root), '--base-sha', self.base], capture_output=True, text=True)

    def test_new_anonymous_receipt_allowed(self):
        (self.folder / ('e' * 32 + '.json')).write_text(self.receipt.read_text().replace(RID, 'e' * 32))
        self.commit()
        self.assertEqual(self.check().returncode, 0)

    def test_edit_existing_receipt_rejected(self):
        self.receipt.write_text(self.receipt.read_text().replace('a'*64, 'b'*64))
        self.commit()
        self.assertNotEqual(self.check().returncode, 0)

    def test_delete_existing_receipt_rejected(self):
        self.receipt.unlink()
        self.commit()
        self.assertNotEqual(self.check().returncode, 0)


if __name__ == '__main__': unittest.main()
