# First-paper Public Git Source Provenance — Implementation Plan

> **For agentic workers:** Follow test-first implementation and verify against the exact PR head in supported GitHub CI.

**Goal:** Reject any public first-paper release whose tag identifies the expected commit but whose paper/data/code bytes at that commit differ from the validated Release archive.

**Architecture:** Keep `publication_recovery` as the verification coordinator. A separate `source_provenance.py` extracts the paper and declared research members from the previously verified bundle, fetches the corresponding public Git source files at a fixed commit, and compares exact bytes. Publication enforces this check prior to promotion and during post-publication verification. The GitHub adapter adds an anonymous source GET, not a write operation.

**Tech stack:** Python 3.10+, standard-library tarfile, hashlib, urllib, existing `verify_release` and research catalog; HTTP transport mocked in automated tests.

**Spec:** `docs/V1_ACCEPTANCE.md`, especially G2, and `docs/FIRST_PAPER_PUBLICATION.md`.

## Tasks and evidence

- [x] RED: Add regression tests for differing public Git PDF and analysis source with an otherwise valid Release bundle. Observe failure before implementation.
- [x] GREEN: Implement exact source-byte comparison and use a fresh bounded anonymous HTTPS GET of the pinned commit, without proxies or redirects.
- [x] RED/GREEN: Cover empty declared research inputs, missing paths, malformed commit/repository, oversized or non-byte source responses and untrusted redirects.
- [x] Wire source verification before public promotion, and into read-only post-publication recovery; add source snapshot information to resulting reports.
- [x] Verify focused local tests (source provenance and recovery). Full integration tests require the project-locked CFF/BibTeX validators and are delegated to CI.
- [ ] Require full Python 3.10/3.12 PR CI, quality and CodeQL checks, then merge only on success.
- [ ] Verify new main SHA and main-branch CI, then record that this does **not** prove a real Release was published.

## Security/operational limits

An already published immutable Release is never rewritten on failure. A missing Git source, including an eventually consistent GitHub CDN result, is NOT a PASS. Both source and Release data are fetched from GitHub, so this is independent retrieval of two endpoints rather than independent hosting/operator control. No external witness, human security sign-off or certificate lifecycle claim is made.
