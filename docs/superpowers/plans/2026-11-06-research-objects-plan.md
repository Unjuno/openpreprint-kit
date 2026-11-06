# Research Objects and Confidential Record Commitments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bind paper, public data/code and confidential-record commitments under one RFC 3161-verifiable release manifest.

**Architecture:** Existing deterministic bundle remains backwards compatible. Add an opt-in research archive/catalog and a local-only private HMAC receipt command. The offline verifier validates TAR members and catalog without extracting.

**Tech Stack:** Python 3.10+, PyYAML 6.0.3, stdlib hashlib/hmac/tarfile, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-06-research-objects-design.md`

## Global Constraints
- No raw confidential data or keys under the GitHub repository.
- Every public asset explicitly confirmed and individually hashed.
- Prior seven-asset releases remain verifiable.
- Never call internal hash consistency an independent timestamp or proof of public access.

## Review Focus
- Misleading private key disclosure, untracked or symlinked data, TAR traversal, unauthorized files, release regressions.

---

### Task 1: Specify behavior with failing tests
**Files:** `tests/test_research_package.py`, `tests/test_private_seal.py`
- [ ] Write tests for schema/path/relations, deterministic data archive, confidential receipts, wrong key and tampering.
- [ ] Run tests before implementation: expect failures because feature is missing.

### Task 2: Build deterministic research archive/catalog
**Files:** `scripts/research_package.py`, `scripts/prepare_release.py`, `research-assets.yaml`
- [ ] Implement strict opt-in schema and hard publication caps.
- [ ] Deterministically create TAR+JSON catalog and bind to main Release manifest.
- [ ] Run new and existing release tests.

### Task 3: Verify research archive offline
**Files:** `scripts/verify_research.py`, `scripts/verify_release.py`
- [ ] Reject undeclared TAR entries, symlinks, malicious paths, mismatched bytes and malformed receipts.
- [ ] Preserve legacy verification behavior and verify research bundles.
- [ ] Run new and existing offline/timestamp tests.

### Task 4: Implement confidential record commitments
**Files:** `scripts/private_seal.py`, `tests/test_private_seal.py`, `.gitignore`
- [ ] Create a fresh 256-bit secret per private original, store it owner-side outside repo with mode 0600, emit a non-identifying JSON receipt only.
- [ ] Verify with original+secret+receipt and reject modifications, incorrect keys and overwrites.
- [ ] Run privacy regression tests.

### Task 5: Wire CI/publication and document limitations
**Files:** `.github/workflows/publish.yml`, `README.md`, `docs/ROADMAP.md`, `docs/THREAT_MODEL.md`, `docs/RESEARCH_OBJECTS.md`, `tests/test_workflows.py`
- [ ] Upload additional Release assets only when present and validate downloaded TAR and catalog.
- [ ] Describe safe private handling, archive semantics, verification and evidence limits.
- [ ] Test on GitHub Actions; maintain explicit outstanding work (live TSA, independent observation, independent security review).
