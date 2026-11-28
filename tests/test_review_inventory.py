import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.verify_review_inventory import verify_inventory


class ReviewInventoryTests(unittest.TestCase):
    def make_repo(self, root: Path) -> tuple[Path, str, bytes]:
        repo = root / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
        original = b"# Review input\nline two\n"
        (repo / "paper.md").write_bytes(original)
        subprocess.run(["git", "-C", str(repo), "add", "paper.md"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "fixture"], check=True, capture_output=True)
        sha = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
        return repo, sha, original

    def test_uses_committed_blob_bytes_not_windows_checkout_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, sha, committed = self.make_repo(root)
            inventory = root / "inventory.json"
            entry = {"path": "paper.md", "bytes": len(committed), "sha256": hashlib.sha256(committed).hexdigest()}
            inventory.write_text(json.dumps({"fixed_main_sha": sha, "manuscript_sources": [entry]}), encoding="utf-8")
            (repo / "paper.md").write_bytes(committed.replace(b"\n", b"\r\n"))

            _, count, failures, _ = verify_inventory(repo, inventory)

        self.assertEqual(count, 1)
        self.assertEqual(failures, [])

    def test_reports_a_wrong_fingerprint(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, sha, _ = self.make_repo(root)
            inventory = root / "inventory.json"
            inventory.write_text(json.dumps({
                "fixed_main_sha": sha,
                "manuscript_sources": [{"path": "paper.md", "bytes": 1, "sha256": "0" * 64}],
            }), encoding="utf-8")

            _, _, failures, _ = verify_inventory(repo, inventory)

        self.assertEqual(len(failures), 1)
        self.assertIn("Git blob has", failures[0])


if __name__ == "__main__":
    unittest.main()
