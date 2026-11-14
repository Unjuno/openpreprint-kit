#!/usr/bin/env python3
"""Recompute key facts of paper A v2 from data files. Standard library only.

Usage: python summarize_releases.py
Exits non-zero on inconsistency. Does not touch the network.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
DATA = HERE / "data"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main() -> int:
    releases = load("release-matrix.json")
    tsa = load("tsa-reverification.json")
    incidents = load("incident-analysis.json")

    errors = []
    if len(releases) != 5:
        errors.append(f"expected 5 releases, got {len(releases)}")
    if sum(1 for r in releases if r["is_immutable"]) != 5:
        errors.append("all 5 releases must be immutable")
    if sum(1 for r in releases if not r["is_draft"]) != 5:
        errors.append("all 5 releases must be public (not draft)")
    if sum(1 for r in releases if r["asset_digests_match_anonymous_download"]) != 5:
        errors.append("all releases must re-download to identical bytes")
    if any(r["target_commit"] is None for r in releases):
        errors.append("release target commit missing")

    if sum(1 for t in tsa if t.get("verdict") == "PASS") != len(tsa):
        errors.append("TSA re-verification must be PASS for all examined versions")

    if len(incidents["incidents"]) < 2:
        errors.append("expected at least the two recorded incidents INC-1 and INC-2")

    summary = {
        "release_count": len(releases),
        "immutable_releases": sum(1 for r in releases if r["is_immutable"]),
        "attestation_verified_releases": len(tsa),
        "asset_digests_match_anonymous_download": sum(
            1 for r in releases if r["asset_digests_match_anonymous_download"]),
        "tsa_reverify_pass": sum(1 for t in tsa if t.get("verdict") == "PASS"),
        "incidents_recorded": len(incidents["incidents"]),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if errors:
        for error in errors:
            print("FAIL:", error, file=sys.stderr)
        return 1
    print("PASS: release/TSA/incident evidence is internally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
