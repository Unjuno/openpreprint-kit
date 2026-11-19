# Independent Witness Receipt Timestamp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional trusted existence-time proof for the signed independent public-observation receipt, with fail-closed verification and explicit identity expectations.

**Architecture:** Reuse RFC 3161 validation code by exposing digest-based query/verification methods. Timestamp a domain-separated hash of `observation.json` and `observation.sig`, not a merely self-reported clock. Keep the existing unsigned-time witness flow for backward compatibility.

**Tech Stack:** Python >=3.10, OpenSSL 3, asn1crypto, unittest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-08-witness-timestamp-design.md`

## Global Constraints
- No automatic new GitHub Releases, permissions changes or private material in public bundles.
- Explicit CA/CRL pin, no independently verified first-publication claim.
- No network calls in offline verification.

## Review Focus
- A signature created after TSA time on the same claim must not pass timestamp check: bind signature bytes.
- Partial or malformed TSA sidecars must fail even when Ed25519 signature is valid.
- Different repository/version observation must not pass when caller supplies expected values.
- Forged response / stale CRL must fail under the same RFC 3161 verification rules as original bundle.
- Zero accuracy field must not be invented when not signed.

---

### Task 1: Digest-level RFC 3161 primitives
**Files:** `scripts/timestamp.py`, `tests/test_timestamp.py`
**Interfaces:** `make_query_for_digest(digest: bytes, policy: dict) -> bytes`; `verify_digest(digest: bytes, query: bytes, response: bytes, policy: dict) -> dict`.
- [ ] Add failing tests: digest request matches SHA-256 imprint; wrong digest fails a real test TSA response; existing bundle flow unaffected.
- [ ] Run targeted tests (expected failure).
- [ ] Implement primitives by extracting existing verification logic, preserving `verify_proof()` result.
- [ ] Run targeted and original timestamp tests to green.
- [ ] Commit.

### Task 2: Bound signed witness receipt to timestamp
**Files:** `scripts/observation.py`, `tests/test_observation.py`
**Interfaces:** `receipt_digest(data: bytes, signature: bytes) -> bytes`; `record_public(..., stamp_observation=False, tsa_exchange=None)`; `verify_public(..., require_observation_timestamp=False, expected_repository=None, expected_version=None)`.
- [ ] Add failing signed-receipt TSA test with temporary CA; bad bytes/digest, missing pair, strict non-attested record and context mismatch.
- [ ] Run targeted tests (expected failure).
- [ ] Implement optional request/response sidecar, CLI switches, verification and conservative output without claiming first publication.
- [ ] Test old fixture compatibility and new regression cases.
- [ ] Commit.

### Task 3: Instructions and verification
**Files:** `docs/PRESERVATION_AND_WITNESS.md`, `docs/ROADMAP.md`, `docs/RELEASE_READINESS.md`, `README.md`.
- [ ] Document operational separation of witness keys and trust policy, sample CLI and threat boundary.
- [ ] Run full existing suite in representative CI matrix and record any environment mismatches.
- [ ] Open PR; merge after CI success; verify `main` run.
