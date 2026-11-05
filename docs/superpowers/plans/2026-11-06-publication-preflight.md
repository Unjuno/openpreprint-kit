# Publication Preflight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject structurally invalid or interactive PDFs and malformed generated citation assets before a GitHub Release can be published.

**Architecture:** Extend the existing strict validator through a focused PDF preflight module and publish-only citation schema checks. Keep normal draft validation non-blocking and the offline hash verifier independent of citation/PDF parsing.

**Tech Stack:** Python ≥3.10, pypdf 6.21.4, PyYAML 6.0.3, asn1crypto 1.5.1, cffconvert 2.0.0, bibtexparser 1.4.3, GitHub Actions Ubuntu 24.04.

**Spec:** docs/superpowers/specs/2026-11-06-publication-preflight-design.md

## Global Constraints
- Fail closed for strict publication. No automatic publication of template v0.
- Limit PDF to 25 MiB, 1–500 pages. Reject encryption and interactive actions.
- No real-paper Release creation during unit/integration tests.

## Review Focus
- Files with forged `%PDF-` headers are rejected (Task 1).
- Encrypted or interactive PDFs are rejected (Task 1).
- Valid PDF with one page is accepted, never rejected merely because a parser is strict (Task 1).
- A malformed generated CFF or BibTeX cannot pass final release checks (Task 2).
- No change is made to the cryptographic timestamp schema or existing release asset names (Task 2).

### Task 1: Strict PDF validation
**Files:** Create `scripts/pdf_validation.py`, `tests/pdf_fixture.py`, `tests/test_pdf_validation.py`; modify `scripts/validate.py`, `tests/test_release.py`, `requirements.txt`.
**Interfaces:** `inspect_pdf(path: Path) -> tuple[int, int]` returns bytes and page count on success; raises ValueError on invalid data.
- [ ] Add failing invalid/active/oversized/encrypted/valid PDF tests and run them.
- [ ] Implement inspection with pypdf strict reading, bounded traversal and page count, integrate into strict validator.
- [ ] Replace legacy magic-only synthetic PDF test fixture with minimal structurally valid PDF.
- [ ] Run complete test suite with 0 failures and commit.

### Task 2: Independent citation format check
**Files:** Create `scripts/citation_validation.py`, `tests/test_citation_validation.py`; modify `scripts/prepare_release.py`, `.github/workflows/validate.yml`, `.github/workflows/publish.yml`, `requirements.txt`, `docs/ROADMAP.md`.
**Interfaces:** `validate_citations(folder: Path) -> None` raises ValueError for invalid CFF or BibTeX. Invoke only for complete publishable output.
- [ ] Add failing tests for malformed CFF/BibTeX and valid citations (unit+CLI).
- [ ] Invoke cffconvert v2.0.0 and bibtexparser v1.4.3 in validation module, with clear errors.
- [ ] Run bundle-generation and GitHub workflow tests, document exact environment and code limitations.
- [ ] Run full suite and commit; create a GitHub PR and await CI before merge.
