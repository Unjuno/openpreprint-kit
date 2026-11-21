# PR #70 post-merge quality and self-application evidence — 2026-11-22

## Fixed source

- Repository: `Unjuno/openpreprint-kit`
- PR #70 approved head: `85aa296088c3c3a4d30804c619c5375d74174647`
- Merge commit and tested main: `74f88fdb7942c793185600e4d2fcd076944596e1`
- Change: add a regression that preserves the original RFC 3161 response and preservation archive when a source signer is later revoked, while rejecting current verification/restoration/renewal.
- Scope: technical regression and approved-manuscript existence only. No toolkit or paper Release was created.
- Issue #5 ledger: [PR #70 fixed-main recheck](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7069164453); [current GitHub gate and security readback](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7069233390); [fixed-SHA human handoff package](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7069268972).

## Workflow runs

| Workflow/check family | Run ID | Result |
|---|---:|---|
| Validate Python 3.10 / 3.12 | 44948427823 | success |
| Quality, audit, Windows and macOS regression | 44948427820 | success |
| CodeQL Python | 44948427757 | success |
| Lean | 44948427755 | success |
| First-paper self-application | 44948654838 | success |
| Live RFC 3161 timestamp and fresh-runner restore | 44948658225 | success |

All seven required CI categories passed on exact main SHA `74f88fdb7942c793185600e4d2fcd076944596e1`.

## Test totals and skips

Each test job ran 441 tests; every job had 0 failures and 0 errors.

| Job | Total | Pass | Skip | Skip reason |
|---|---:|---:|---:|---|
| Python 3.10 validate | 441 | 428 | 13 | 7 optional Hypothesis properties not installed on 3.10; 6 Windows-specific tests |
| Python 3.12 validate | 441 | 435 | 6 | Windows-specific ACL/junction/Win32 tests |
| Ubuntu audit, Python 3.12 | 441 | 435 | 6 | Windows-specific ACL/junction/Win32 tests |
| Windows regression, Python 3.12 | 441 | 435 | 6 | POSIX shell integration tests |
| macOS regression, Python 3.12 | 441 | 435 | 6 | Windows-specific ACL/junction/Win32 tests |

All platform-specific cases ran on a supporting CI platform. The optional Hypothesis properties ran in each Python 3.12 test job.

## Cross-workflow PDF and RFC 3161 evidence

- Self-application and live timestamp workflow PDFs are byte-identical: 187,504 bytes; SHA-256 `d892d100ce5cbae994b7547570828eba280b62e716123e2ffd26edf56e0026bc`.
- PDF trailer ID `4f1af0bb11e0d8a63e5af4d2b706c225` is derived from the fixed source SHA.
- Four self-application negative cases were rejected.
- RFC 3161 status: `VERIFIED`, TSA time `2026-11-21T20:55:17Z`; manifest SHA-256 `511f5f30998f5a3974a58c6399d08155b0d59c216180699e4a21236c372d115d`; pinned CA SHA-256 `2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438`.
- Separate fresh runner restored the archive and passed bundle, citation, and timestamp verification. Preservation ZIP SHA-256: `276ef8dc02baf4d3ccb27f24749a2b7c464e16908e081fd8a90275af35063299`.
- TSA accuracy was not specified (`null`). The workflow proves approved-metadata evidence existence under the supplied trust policy; it does not prove authorship, public availability, independent observation or durable retention. Actions artifacts are retained for 14 days.

## Current public release and gate readback

- Public OpenPreprint search under the authenticated `Unjuno` account found `openpreprint-kit` and `openpreprint-kit-paper`. Search under the public profile of `TAKAYASHIKIJUNYA` found no OpenPreprint repository. The other account's private repositories are outside the current token's visibility; their absence is not inferred.
- `openpreprint-kit-paper` currently exposes only immutable, non-draft v1 and v2 (Release IDs `444659219` and `445442340`). Its main branch requires three status checks and zero approving reviews. The second qualifying public paper repository and its releases remain unresolved.
- Current open GitHub code-scanning, Dependabot and secret-scanning alert API counts were each zero. This is an alert readback, not a complete security/privacy assessment.
- G7 regression `test_revoked_origin_evidence_is_preserved_but_never_renewed` verifies that revoked source evidence is rejected; failed restore/renewal creates no partial output; no TSA request is sent; and the original archive and response bytes are retained.
- Formal status: G0 technical pass on this fixed SHA; G1/G2/G6 blocked; G3/G4/G5/G7 partial evidence, not pass. P4 and toolkit v1.0.0 remain NO-GO.

The latest local Gold Candidate is r36, SHA-256 `7245a0fc99ffd07d5846093b14512bb39701a4dc1df2651f57cd170f4b874b2c`. Its fixed-SHA G6 handoff input inventory contains 42 files and every file matched the source archive. This checks input integrity only; human review, rights decisions, correction/withdrawal exercises and publication approval remain pending. Earlier candidates remain preserved.
