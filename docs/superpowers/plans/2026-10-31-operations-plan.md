# Operational Readiness Implementation Plan

> For agentic workers: use superpowers:executing-plans when no dispatch tool exists.

**Goal:** close publication safety gaps and add reproducible human review/correction records.
**Architecture:** additive standard-library CLIs and static HTML over the existing bundle.
**Tech Stack:** Python >=3.10, GitHub REST/Actions, existing OpenSSL3/asn1crypto/PyYAML.
**Spec:** ../specs/2026-10-31-operations-design.md

## Global Constraints
No real paper publication, paid enrollment or automatic administrative setting changes.
Never equate review records with independent peer-review certification.

## Review Focus
API error handling; history rewrites; version/hash substitution; unsafe generated HTML;
secrets and token permissions. Preserve backward compatibility of nine-asset bundles.

### Task 1: Fail-closed GitHub preflight
Files: scripts/preflight.py, tests/test_preflight.py, .github/workflows/publish.yml.
- [x] Write failing tests for disabled/unknown immutability, tag conflicts and API outages.
- [x] Implement GitHub read-only API client and preflight(repository, version, commit, get).
- [x] Run tests; wire checks before stamping and immediately before draft promotion.

### Task 2: Review and correction evidence
Files: scripts/research_record.py, tests/test_research_record.py, reviews/record.json.
- [x] Write failing tests for append-only evolution, evidence hash/path and version binding.
- [x] Implement validate_record(data, root, baseline=None) and status_for(data, version, digest).
- [x] Run tests; validate records and compare against PR base in CI.

### Task 3: Safe static reader view
Files: scripts/build_site.py, tests/test_site.py.
- [x] Write failing tests for tampered bundles, escaping and prominent retraction status.
- [x] Implement build_site(bundle, root, output, repository) with no JavaScript execution.
- [x] Run tests; include site-generation tests and tested-source artifact in CI.

### Task 4: Auditable operation and completion gates
Files: docs/REVIEW_POLICY.md, docs/RELEASE_READINESS.md, docs/OPERATIONS.md,
SECURITY.md, CONTRIBUTING.md, .github/ISSUE_TEMPLATE/*, README.md, docs/ROADMAP.md.
- [x] Document who must act, required permissions, acceptance evidence, recovery, and limits.
- [x] Run full local suite (88 tests pass) and source checks.
- [ ] Verify final remote CI and integrate only passing changes.

## Execution ledger
Baseline: GitHub bdfe0d5, parent RFC3161 commit 27a8d9f. Existing remote CI passed.
Local initial full-suite attempts exceeded execution timeout; not reported as passes.
Ruling: use CI-produced source archive because this container cannot resolve github.com.
Ruling: keep reviews as a separately validated, append-only operational record; do not
change existing timestamp bundle format or imply records are signed by the original TSA.

Local evidence: /mnt/data/opk-final-tests.txt, 88/88 PASS; Python3.13.5 / OpenSSL3.5.5. No public TSA or actual paper was used. Independent reviewer unavailable; handoff in RELEASE_READINESS.md.
