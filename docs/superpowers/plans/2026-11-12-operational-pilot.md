# Operational pilot implementation plan

**Goal:** Close the gap between kit CI and using the kit: give the owner one explicit synthetic-only operation that creates two template repositories, publishes v1/v2, anonymously re-downloads, verifies GitHub attestations and RFC 3161 evidence, and restores all four archives.
**Authority:** Existing `docs/V1_ACCEPTANCE.md`, user instruction to execute through completion. No new production guarantee or changed release gate.
**Architecture:** Reuse the existing fixture, timestamp, offline verifier, owner setup and preservation modules. Use the owner's already authenticated `gh` CLI; never request/export secrets. Default is a read-only plan. The mutation flag is explicit and destination names must start `opk-demo-`. No overwrite, deletion, disabling protections, or real data publication.
**Environment:** Python >=3.10, OpenSSL 3, supported hash-locked dependencies, GitHub CLI supporting release verification; public GitHub.com only.
**Execution constraint:** Connector cannot administer/create repos; no authenticated browser or remote computer available. Never work around an authorization denial with a different identity. Engineering and test work continues locally; live owner actions require owner auth.

## Tasks
- [x] Reproduce/repair CI test fixture coupling to the author's live preprint.yaml; validate with a copied template containing changed metadata.
- [x] Extend synthetic fixture with explicitly allowlisted source export; test private bytes/keys are absent and source identity binds to repo + commit.
- [x] Build plan/apply synthetic pilot; real GitHub I/O isolated behind `gh`. Explicit mutation gate, failure journal, immutable/attestation checks, anonymous download, old-version retention, archive restore. API permission/network failures are never treated as absence.
- [ ] Run real cryptographic local integration tests and all regression tests; run CI on exact pushed commit. Do not label mocked GitHub tests as real Releases.
- [x] Record commands, partial-recovery behavior, blocked owner step, and unchanged independent operator/security/clinical gates.

## Review focus
Default command performs no external writes; preexisting or unrelated repos are never modified; no originals/keys in export; HTTP auth errors stop; published-but-unverified state retained in report; actual independent observer/custodian is never simulated as independent.

## Verification record
Local full suite: 230 tests, exit 0, Python 3.13.5/OpenSSL 3.5.5; hash-locked dependencies. Public TSA evidence was not reissued in this step. Actual private Drive upload/download/restoration of earlier synthetic v1/v2 archives passed; retained unexpired signed CRL, no fresh CRL retrieval. Owner-authenticated GitHub publication remains unexecuted. Final remote CI on pushed content is required.
