#!/usr/bin/env python3
"""Python-vs-Lean differential test on the shared vectors.

The Lean model and the production Python code are DIFFERENT implementations.
This harness runs both on formal/vectors.json and requires identical verdicts.

For two areas it calls production code directly:
  * state transitions -> preflight.preflight() with an injected read-only API
  * receipt binding   -> observation.receipt_digest()
For the remaining two areas it re-expresses the exact production decision rule
over pure inputs (no filesystem/network), with source references in comments.

Exit 0 = all verdicts agree; exit 1 = a divergence (printed to stderr).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))

import preflight  # noqa: E402
import observation  # noqa: E402
import verify_release  # noqa: E402

ASSET_TO_FILE = {
    "citation": "CITATION.cff",
    "notes": "RELEASE_NOTES.md",
    "bibtex": "citation.bib",
    "paper": "paper.pdf",
    "metadata": "preprint-metadata.json",
    "manifest": "manifest.json",
    "sums": "SHA256SUMS",
    "researchJson": "research-assets.json",
    "researchTar": "research-assets.tar",
    "tsq": "timestamp.tsq",
    "tsr": "timestamp.tsr",
}
PAYLOAD = set(verify_release.PAYLOAD_FILES)
EXPECTED = set(verify_release.EXPECTED_FILES)
RESEARCH = set(verify_release.RESEARCH_FILES)
EVIDENCE = set(verify_release.EVIDENCE_FILES)


def _names(flagmap):
    return {ASSET_TO_FILE[k] for k, v in flagmap.items() if v}


def release_verdict(case):
    """Re-expresses verify_release.verify()+preflight.validate_repository()
    set/identity rules from formal vectors. No I/O."""
    _, r, trusted_repo, trusted_ver, _ = case
    actual = _names(r["assets"])
    research_present = bool(actual & RESEARCH)
    expected = EXPECTED | (RESEARCH if research_present else set())
    # verify_release.verify asset allowlist
    if actual not in (expected, expected | EVIDENCE):
        return False
    manifest = _names(r["manifestFiles"])
    if manifest != PAYLOAD | (RESEARCH if research_present else set()):
        return False
    repo = f'{r["repo"]["owner"]}/{r["repo"]["name"]}'
    try:
        preflight.validate_repository(repo)
    except ValueError:
        return False
    if r["repo"] != trusted_repo or r["version"] != trusted_ver:
        return False
    version = "v" + ".".join(str(x) for x in r["version"])
    if not re.fullmatch(r"v(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*)){0,2}", version):
        return False
    if not any(int(x) for x in r["version"]):
        return False
    if not re.fullmatch(r"[0-9a-f]{64}", r["paperDigest"]):
        return False
    if r["pinnedPaperDigest"] is not None and r["paperDigest"] != r["pinnedPaperDigest"]:
        return False
    return True


def state_verdict(case):
    """Calls PRODUCTION preflight.preflight() with an injected read-only
    GitHub GET. A PASS maps to the 'verified' model phase."""
    _, ctx, view, _ = case
    version = ctx["version"]

    def get(path):
        if path == "":
            return 200, {"private": not view["isPublic"], "default_branch": "main"}
        if path == "/immutable-releases":
            return 200, {"enabled": view["immutableEnabled"]}
        if path == "/commits/main":
            return 200, {"sha": view["headSha"]}
        if path in (f"/releases/tags/{version}", f"/git/ref/tags/{version}"):
            occupied = view["releaseTagExists"] if "releases/tags" in path else view["tagRefExists"]
            return (200, {"x": 1}) if occupied else (404, {})
        return 404, {}

    old_sleep = preflight.time.sleep
    preflight.time.sleep = lambda _seconds: None
    try:
        result = preflight.preflight(ctx["repository"], version, ctx["commit"], get)
    except ValueError:
        return "draft"
    finally:
        preflight.time.sleep = old_sleep
    return "verified" if result["status"] == "PASS" else "draft"


def evidence_verdict(case):
    """Calls PRODUCTION observation.receipt_digest() on both pairs."""
    _, d1, s1, d2, s2, _ = case
    a = observation.receipt_digest(d1.encode("utf-8"), s1.encode("utf-8"))
    b = observation.receipt_digest(d2.encode("utf-8"), s2.encode("utf-8"))
    return a == b


def claim_verdict(case):
    """Re-expresses the exact bounded claim vocabulary from
    observation.py verify_public() expected_claims (lines 242-252)."""
    _, rc, _ = case
    return (
        rc["publicAvailability"] == "WITNESS_ASSERTS_ANONYMOUS_RETRIEVAL"
        and rc["firstPublication"] == "NOT_PROVEN"
        and rc["authorship"] == "NOT_PROVEN"
        and rc["witnessClock"] == "SELF_REPORTED_NOT_A_TRUSTED_TIMESTAMP"
        and rc["anonymousHttps"] is True
        and rc["timestampVerified"] is True
    )


def main() -> int:
    vectors = json.loads((HERE / "vectors.json").read_text(encoding="utf-8"))
    lean = {}
    for line in (HERE / "lean_results.txt").read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            lean[parts[0]] = parts[1]

    rows = []
    for case in vectors["release_assets"]:
        rows.append((case[0], "true" if release_verdict(case) else "false"))
    for case in vectors["state_transition"]:
        rows.append((case[0], state_verdict(case)))
    for case in vectors["evidence_binding"]:
        rows.append((case[0], "true" if evidence_verdict(case) else "false"))
    for case in vectors["claims"]:
        rows.append((case[0], "true" if claim_verdict(case) else "false"))

    failures = []
    for cid, py in rows:
        lv = lean.get(cid)
        ok = lv == py
        print(f"{cid}\tpython={py}\tlean={lv}\t{'MATCH' if ok else 'DIVERGENCE'}")
        if not ok:
            failures.append((cid, py, lv))
    print(f"\n{len(rows) - len(failures)}/{len(rows)} vectors agree across Python and Lean")
    if failures:
        print("DIVERGENCES:", failures, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
