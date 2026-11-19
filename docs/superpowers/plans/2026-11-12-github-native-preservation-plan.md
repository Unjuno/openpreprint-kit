# GitHub-native preservation implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development and executing-plans; self-review all work because no independent agent dispatch exists.

**Goal:** GitHub Releases are the sole online publication/replication backend, with explicit cryptographic audit of mirrored archives and no Google Drive runtime.
**Architecture:** Reuse existing custody ZIP+catalog verification. Add a GitHub mirror CLI that never accepts its own receipt as an external trust root and requires immutable releases and pinned digests.
**Tech Stack:** Python 3.10+, OpenSSL 3, `gh` CLI at operator side; built-in urllib for anonymous retrieval.
**Spec:** `docs/superpowers/specs/2026-11-12-github-native-preservation-design.md`

## Global constraints
Never publish real/patient materials from test fixtures. No remote mutation without explicit `--apply`. Existing tags and output paths are never overwritten. GitHub-only replication is not independent infrastructure custody.

## Review focus
1. Wrong source repo/tag in a valid custody catalog must fail.
2. Corrupted ZIP/receipt and swapped Release must fail even if remote metadata reports immutable.
3. Missing asset, extra asset, or unsafe URL redirects must fail.
4. Same GitHub owner must not be falsely reported independently controlled.
5. Failure after draft/publication must leave journal with no rollback claim.

### Task 1: Offline and remote mirror transport
**Files:** `scripts/github_mirror.py`, `tests/test_github_mirror.py`.
**Interfaces:** `plan(source,mirror,catalog_pin) -> dict`; `publish(source,mirror,store,catalog_pin,policy,output,gateway) -> dict`; `verify_mirror(source,mirror,tag,catalog_pin,receipt_pin,policy,output,gateway) -> dict`.
- [ ] Write failing tests for plan, wrong pins, immutable preflight, successful two-archive transport, swapped assets, unsafe URLs and metadata drift.
- [ ] Run test suite to establish RED for missing implementation.
- [ ] Implement explicit GitHub mirror draft/promotion with readback; no clobber/deletion; anonymous audit.
- [ ] Run new tests to GREEN, then full suite.

### Task 2: GitHub-only operator documentation
**Files:** `README.md`, `docs/GITHUB_PRESERVATION.md`, `docs/STATUS_2026-11-12.md`, `docs/V1_ACCEPTANCE.md`, `docs/OPERATIONAL_PILOT.md`.
- [ ] Document exact owner-action commands and short-term/long-term caveats; no cloud storage dependency.
- [ ] Ensure source history facts are not falsified: past Drive experiment was performed, but no longer prescribed or required.
- [ ] Verify docs and compile, then CI on GitHub branch; preserve evidence.
