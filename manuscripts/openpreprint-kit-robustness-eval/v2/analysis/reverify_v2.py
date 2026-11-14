#!/usr/bin/env python3
"""Recompute Paper B v2's claimed experiment results from the recorded data.

No network. Standard library except for the project's verify_evidence/
timestamp helpers on the optional --verify-timestamps path (not used here).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
DATA = HERE / "data"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main() -> int:
    errors = []

    e1 = load("e-v2-1-crl-lifecycle.json")
    if not (e1["crl_fresh"]["result"]["verdict"] == "VERIFIED"
            and e1["crl_stale"]["result"]["verdict"] == "REJECTED"
            and "CRL has expired" in e1["crl_stale"]["result"].get("error", "")):
        errors.append("E-V2-1 results do not match the paper's claims")

    renew = load("renewal-experiment.json")
    if not (renew["issue_status"] == "PASS" and renew["verify_status"] == "PASS"
            and renew["tsa_policies"] == ["1.2.3.4.1"]
            and renew["archive_sha256"] == "106d536371c9286952eca1cf96fff542cc5de949c0673956818f52f13cffa26c"
            and renew["chain_sha256"] == "1eaae7e2ad3239a516b4731d14515be6bd5748caa45a038a59aebcdea2a6f993"):
        errors.append("E-V2-2 results do not match the paper's claims")

    neg = load("negative-suite-results.json")
    if neg["false_accepts"] != 0 or neg["passes"] != 23:
        errors.append("negative-suite totals not 23/0 false accepts")

    summary = {"E-V2-1_fresh": e1["crl_fresh"]["result"]["verdict"],
               "E-V2-1_stale": e1["crl_stale"]["result"]["verdict"],
               "E-V2-2_verify": renew["verify_status"],
               "negative_suite_false_accepts": neg["false_accepts"]}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if errors:
        for e in errors:
            print("FAIL:", e, file=sys.stderr)
        return 1
    print("PASS: v2 experiment records are internally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
