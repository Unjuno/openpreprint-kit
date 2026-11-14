"""Regression guard: owner handover docs must match canonical acceptance and runtime.

These are documentation/schema contract checks only, not independent human
acceptance, a real witness signature, or a public-release security assessment.
"""
from __future__ import annotations

import ast
from pathlib import Path
import re
import shlex
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "operator-packages"


class OperatorAcceptanceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canonical = (ROOT / "docs" / "V1_ACCEPTANCE.md").read_text("utf-8")
        cls.g2 = (DOCS / "G2-optionA-publication.md").read_text("utf-8")
        cls.g4 = (DOCS / "G4-independent-observer.md").read_text("utf-8")
        cls.g5 = (DOCS / "G5-custodian-handover.md").read_text("utf-8")
        cls.g7 = (DOCS / "G7-external-audit.md").read_text("utf-8")
        cls.observation_source = (ROOT / "scripts" / "observation.py").read_text("utf-8")
        cls.observation_tree = ast.parse(cls.observation_source)

    def test_g2_option_a_is_two_real_papers_with_two_versions_each(self):
        self.assertIn("2論文リポジトリに各2版", self.canonical)
        self.assertIn("第1論文v2", self.g2)
        self.assertIn("第2実論文v1・v2", self.g2)
        self.assertIn("両方必須", self.g2)
        self.assertIn("計3件", self.g2)
        self.assertIn("Synthetic", self.g2)
        self.assertIn("第1論文v2", self.g5)
        self.assertIn("第2実論文", self.g5)

    def test_observer_example_uses_implemented_cli_flags(self):
        defined = set()
        for node in ast.walk(self.observation_tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "add_argument":
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            if arg.value.startswith("--"):
                                defined.add(arg.value)
        fence = chr(96) * 3
        examples = re.findall(re.escape(fence) + r"bash\n(.*?)\n" +
                              re.escape(fence), self.g4, re.S)
        self.assertEqual(len(examples), 2, "one exact record and verify example")
        commands = []
        for example in examples:
            argv = shlex.split(example.replace("\\\n", " "))
            self.assertEqual(argv[:2], ["python", "scripts/observation.py"])
            self.assertTrue(set(a for a in argv if a.startswith("--")) <= defined)
            commands.append(argv)
        record, verify = commands
        self.assertEqual(record[2], "record")
        self.assertEqual(verify[2], "verify")
        for argument in ("--repository", "--version", "--out", "--policy",
                         "--signing-key", "--timestamp-observation"):
            self.assertIn(argument, record)
        for argument in ("--observation", "--public-key", "--expected-public-key-sha256",
                         "--expected-repository", "--expected-version", "--policy",
                         "--require-observation-timestamp"):
            self.assertIn(argument, verify)

    def test_observer_docs_match_strict_schema_and_signed_receipt(self):
        field_node = next(
            n for n in self.observation_tree.body
            if isinstance(n, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "OBSERVATION_FIELDS"
                for t in n.targets)
        )
        fields = ast.literal_eval(field_node.value)
        self.assertNotIn("signed_by", fields)
        self.assertNotIn("source_commit", fields)
        self.assertIn("signature_algorithm", fields)
        self.assertIn("timestamp_verified", fields)
        self.assertIn("signed_by", self.g4)
        self.assertIn("source_commit", self.g4)
        self.assertIn("任意追加は禁止", self.g4)
        for artifact in ("observation.json", "observation.sig",
                         "observation.tsq", "observation.tsr", "bundle/"):
            self.assertIn(artifact, self.g4)
        for important in ("receipt_digest(", "len(data).to_bytes(8, 'big')",
                          "len(signature).to_bytes(8, 'big')", "observation.sig"):
            self.assertIn(important, self.observation_source)
        self.assertIn("両方", self.g4)

    def test_external_audit_cannot_waive_open_high_risk_findings(self):
        self.assertIn("重大・高リスク未解決0", self.canonical)
        verdict = self.g7.split("## PASS 条件", 1)[1]
        self.assertIn("未解決が0件", verdict)
        self.assertIn("所有者が例外を承認してもG7をPASSにできない", verdict)
        self.assertNotIn("（または未解決リストと Owner 承認）", verdict)
        self.assertIn("実測した試験結果", verdict)


if __name__ == "__main__":
    unittest.main()
