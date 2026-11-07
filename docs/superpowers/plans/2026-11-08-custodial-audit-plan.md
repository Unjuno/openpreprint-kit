# Independent Custodian Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Support independent off-GitHub custody with pinned multi-version archives, exhaustive local audits, and explicit evidence limitations.

**Architecture:** Verify versioned release ZIPs with existing `preserve.restore`, assert repository identity with `observation.assert_source_identity`, and create a deterministic externally pinnable custody catalog. A later read-only audit verifies the supplied catalog digest and every archive using a separately chosen trust policy.

**Tech Stack:** Python 3.10+, stdlib, existing OpenSSL 3/RFC 3161 verifier and pinned library dependencies.

**Spec:** `docs/superpowers/specs/2026-11-08-custodial-audit-design.md`

## Global Constraints
- No patient originals, HMAC keys, signing keys or self-contained trusted CA pin in public assets.
- `deposit` fails rather than overwriting, `audit` never modifies the custody store.
- Both require independently supplied repository identity, timestamp trust policy and file/catalog SHA-256 pins.
- Neither operation asserts third-party independence, archival durability or first-publication time.

## Review Focus
1. Source is missing or replaced during deposit; a pinned archive hash must mismatch and block installation.
2. Wrong source repository or version hidden inside an otherwise valid signed archive must fail.
3. Catalog or ZIP modified together must still fail under independently pinned catalog SHA-256.
4. A symlink, extra file, missing old release or duplicate version must fail.
5. Incomplete/expired TSA trust policy or invalid signature must block both deposit and audit.

---

### Task 1: Fail-first custody interface and signing tests
**Files:** Create `tests/test_custody.py`; Create `scripts/custody.py`.
**Interfaces:** `deposit(repository: str, entries: list[tuple[str, Path, str]], output: Path, policy: Path) -> dict`; `audit(repository: str, storage: Path, catalog_hash: str, policy: Path) -> dict`.
- [ ] Write tests using temporary CA/TSA and `preserve.pack` fixtures for v1/v2, asserting deposit and audit success, source-version binding, no overwrite, and fail-closed cases.
- [ ] Run `python -m unittest discover -s tests -p 'test_custody.py' -v`, confirm expected failure from missing implementation.
- [ ] Implement deterministic catalog, atomic deposit and read-only audit using `preserve.restore` and `assert_source_identity`.
- [ ] Run test file, confirm PASS; run full `python -m unittest discover -s tests -v` and check results.
- [ ] Commit code and tests.

### Task 2: Custodian runbook and public contract
**Files:** Create `docs/CUSTODY.md`; Modify `README.md` and `docs/ROADMAP.md`; add CI regression checks only if needed.
**Interfaces:** CLI described in the spec and Task 1; no additional package dependencies.
- [ ] Write a runnable command sequence with out-of-band catalog pin, different custodian host, periodic manual audit and TSA policy renewal guidance.
- [ ] State operator independence / custody durability are NOT verified by the CLI.
- [ ] Run syntax/CLI checks and full test suite, inspect `git diff --check`.
- [ ] Commit docs.

### Task 3: GitHub integration and verification
**Files:** No new source; integrate existing commits via Git Data API/PR.
- [ ] Compare local tree to the remote base tree and inspect the diff for secrets.
- [ ] Create feature branch from exact `main` head, add only changed files and tests, open PR.
- [ ] Verify Python 3.10/3.12 GitHub Actions plus audit CI on feature head; fix any failures before merging.
- [ ] Merge using exact expected head SHA and verify `main` CI. Do not publish a research release.
