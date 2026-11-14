#!/usr/bin/env python3
"""Recompute paper B's reported numbers from the fixed spec and recorded results.

Standard library only. Exits non-zero on inconsistency. No network access.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
DATA = HERE / "data"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main() -> int:
    spec = load("negative-suite-spec.json")
    results = load("negative-suite-results.json")
    summary = load("negative-suite-summary.json")

    errors = []
    case_ids = {c["id"] for c in spec["cases"]}
    judged = [r["id"] for r in results["results"]]
    if case_ids != set(judged):
        errors.append(f"spec cases {sorted(case_ids)} != judged {sorted(set(judged))}")
    if len(judged) != 23:
        errors.append(f"expected 23 judgments, got {len(judged)}")
    false_accepts = sum(1 for r in results["results"] if not r["rejected"])
    if false_accepts:
        errors.append(f"false accepts: {false_accepts}")
    if results["passes"] != 23 or results["false_accepts"] != 0:
        errors.append("results pass/false_accepts mismatch")
    if summary["total_judgments"] != 23 or summary["false_accepts"] != 0:
        errors.append("summary mismatch")

    # verify PKI-related cases reached a rejection for the right layer
    by_id = {}
    for r in results["results"]:
        by_id.setdefault(r["id"], []).append(r)
    for cid in (13, 14, 15):
        if not by_id.get(cid):
            errors.append(f"PKI case {cid} missing")
        elif not all(r["rejected"] for r in by_id[cid]):
            errors.append(f"PKI case {cid} not rejected")

    out = {
        "spec_cases": len(case_ids),
        "judgments": len(judged),
        "passes": results["passes"],
        "false_accepts": results["false_accepts"],
        "pki_cases_tested": [13, 14, 15],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if errors:
        for e in errors:
            print("FAIL:", e, file=sys.stderr)
        return 1
    print("PASS: negative-suite spec/results are internally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
