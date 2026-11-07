# Unified Offline Evidence Verifier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide fail-closed one-command verification with explicit evidence scope.

**Architecture:** Reuse the immutable bundle verifier, RFC 3161 verifier and independent witness verifier; bind source identity and exact bytes. Reports use typed, machine-readable status labels without claiming human independence or first publication.

**Tech Stack:** Python >=3.10, standard library, OpenSSL 3, asn1crypto via existing timestamp module, unittest.

**Spec:** `docs/superpowers/specs/2026-11-08-unified-verifier-design.md`

## Global Constraints
- No network or new publications during verification. All trust inputs supplied out of band.
- Both scopes require a caller-selected TSA policy and expected repository/tag.
- Observation mode requires an independent public-key pin and an RFC 3161-stamped signed witness receipt.

## Review Focus
- Bundle with internally consistent but attacker-rewritten SHA checksums still fails trusted timestamp.
- Witness source identity mismatch fails even with valid signatures.
- A different valid TSA timestamp over the same paper cannot be substituted for the witness-downloaded Release bytes.
- Explicit existence scope never emits an asserted public-access success.
- Error messages and normal return values must never elevate signed author/clock assertions into proof.

---

### Task 1: Test-first unified verification
**Files:** `tests/test_verify_evidence.py` (create), `scripts/verify_evidence.py` (create)
**Interface:** `verify_all(bundle: Path, policy_path: Path, repository: str, version: str, scope: str, *, witness: Path | None = None, public_key: Path | None = None, public_key_sha256: str | None = None, expected_paper_sha256: str | None = None) -> dict`
- [ ] Write failure-first tests for valid existence scope, valid public-observation scope, missing/wrong evidence, wrong identity, tampered byte comparisons and strict witness timestamp requirement.
- [ ] Run tests to red (missing `verify_evidence` module).
- [ ] Implement the minimal composition, source binding, byte equality and bounded report.
- [ ] Run targeted tests and regressions to green.
- [ ] Commit.

### Task 2: User-facing operation and CI
**Files:** `README.md`, `docs/PRESERVATION_AND_WITNESS.md`, `docs/ROADMAP.md` (modify).
- [ ] Document both scopes, supported evidence and trust boundaries.
- [ ] Run full test suite in Python 3.10/3.12 GitHub CI; check expected cases.
- [ ] Stage a PR and merge only when validations pass, then verify main.
