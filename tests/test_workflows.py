"""Static release gates; actual GitHub publication requires a separate E2E test."""
from pathlib import Path
import re
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]


class WorkflowTests(unittest.TestCase):
    def workflow(self):
        # BaseLoader preserves YAML 1.2-like 'on', unlike SafeLoader YAML 1.1 booleans.
        return yaml.load((ROOT / ".github/workflows/publish.yml").read_text(), Loader=yaml.BaseLoader)

    def test_timestamp_precedes_draft_creation(self):
        text = (ROOT / ".github/workflows/publish.yml").read_text()
        self.assertIn("timestamp.py stamp", text)
        self.assertLess(text.index("timestamp.py stamp"), text.index("gh release create"))
        self.assertIn("timestamp-policy.json", text)

    def test_downloaded_timestamp_is_verified_before_publication(self):
        text = (ROOT / ".github/workflows/publish.yml").read_text()
        needle = "timestamp.py verify downloaded-release"
        self.assertIn(needle, text)
        self.assertLess(text.index(needle), text.index("--draft=false"))
        self.assertIn("dist/timestamp.tsq dist/timestamp.tsr", text)

    def test_only_manual_dispatch_with_minimum_permissions(self):
        workflow = self.workflow()
        self.assertEqual(set(workflow["on"]), {"workflow_dispatch"})
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        self.assertEqual(workflow["jobs"]["publish"]["permissions"], {"contents": "write"})

    def test_actions_are_pinned_and_shell_inputs_are_not_interpolated(self):
        for file in (ROOT / ".github/workflows").glob("*.yml"):
            workflow = yaml.load(file.read_text(), Loader=yaml.BaseLoader)
            for job in workflow["jobs"].values():
                for step in job["steps"]:
                    if "uses" in step:
                        self.assertRegex(step["uses"], r"@[0-9a-f]{40}$")
                    if "run" in step:
                        self.assertNotIn("${{", step["run"])

    def test_example_policy_is_nonoperational_and_has_no_private_keys(self):
        example = ROOT / "timestamp-policy.example.json"
        self.assertTrue(example.is_file())
        self.assertIn(".invalid", example.read_text())
        for file in (ROOT / "trust").glob("*"):
            if file.is_file():
                self.assertNotIn("BEGIN PRIVATE KEY", file.read_text())


if __name__ == "__main__":
    unittest.main()
