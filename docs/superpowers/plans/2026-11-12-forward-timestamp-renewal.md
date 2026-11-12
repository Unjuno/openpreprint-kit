# Forward RFC 3161 timestamp renewal implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add source-bound, linked and separately pinned RFC 3161 renewal sidecars without claiming historical LTV.

**Architecture:** The verified original preservation ZIP is the fixed source. Each step timestamps a canonical JSON statement that includes the archive digest and digest of the complete prior step. Verification recomputes all bindings and independently validates all trust policies.

**Tech Stack:** Python 3.10+, existing asn1crypto / OpenSSL 3 / standard-library GitHub publishing workflow.

**Spec:** `docs/superpowers/specs/2026-11-12-forward-timestamp-renewal.md`

## Global constraints
- No secrets/medical originals in public output; no edits to the source ZIP.
- At most 16 renewal steps, no unknown files or symlinks.
- No insecure trust fallback, no certificate-validity bypass or historical LTV claim.

## Review focus
- Source ZIP swapped after issuance: reject via archived SHA-256.
- Old renewal changed/reordered/deleted: reject via prior-step hash or external terminal pin.
- Bad extra files/symlinks: reject prior to verification.
- Different TSA trust policies per step: verify with explicit per-step policy.
- Partially completed or failed TSA exchange: never publish a destination directory.

---

### Task 1: Tests first
- [ ] Add `tests/test_renewal.py` with two-CA real RFC 3161 signatures; cover valid one/two-step chain, negative cases, source restoration.
- [ ] Run focused test to observe expected failure (missing renewal API).

### Task 2: Implement `scripts/renewal.py`
- [ ] Add `step_digest` and strict `verify_chain` with exact file inventories and out-of-band final fingerprint.
- [ ] Add `issue_chain` that verifies source and previous chain first, posts RFC 3161 only under opt-in, verifies reply, atomically publishes new directory.
- [ ] Add `verify`/`issue` CLI with explicit repository, version, source/renewal trust and output/pin requirements.
- [ ] Run focused tests to green and whole suite to green.

### Task 3: Docs and GitHub integration
- [ ] Document separate immutable GitHub Release for renewed evidence and independent SHA pin, with exact operational boundaries.
- [ ] Ensure no regression to publication or mirror workflows; run Python 3.10/3.12 CI on branch.
- [ ] Review and merge after CI green; keep G7 external human audit and long-term validation blocked.
