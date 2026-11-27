# Post-merge quality and self-application evidence — 2026-11-27

## Fixed source and CI

- Source: `Unjuno/openpreprint-kit` `main` at `e804fb2105479cfd37ff1bd1117bcc03a7547ffd`.
- PR #72 head `8387a9e18eddfd397e2db75f266d6f0f9d46954d` merged as `e804fb2105479cfd37ff1bd1117bcc03a7547ffd` at `2026-11-27T11:26:26Z`. PR #72 changed documentation and evidence only; the main source code was unchanged.
- Post-merge required checks on the exact main SHA: **7/7 success**. Runs: [quality `45990497329`](https://github.com/Unjuno/openpreprint-kit/actions/runs/45990497329), [validation `45990497351`](https://github.com/Unjuno/openpreprint-kit/actions/runs/45990497351), [Lean `45990497335`](https://github.com/Unjuno/openpreprint-kit/actions/runs/45990497335), [CodeQL `45990497336`](https://github.com/Unjuno/openpreprint-kit/actions/runs/45990497336).
- Python 3.12 validation, Linux audit, Windows 3.12, and macOS 3.12 each ran 441 tests: 435 passed, 6 platform-specific skips, 0 failures, 0 errors. Python 3.10 ran 441: 428 passed, 13 skips (6 Windows-specific plus 7 optional Hypothesis property tests unavailable on Python 3.10), 0 failures, 0 errors.
- The six POSIX shell integration tests are skipped only on Windows. The six Windows-only tests skipped on POSIX jobs are `test_inherited_broad_read_ace_is_rejected_before_key_creation`, `test_localized_group_display_names_cannot_bypass_wide_read_sid`, `test_unknown_trustee_sid_is_rejected_before_key_creation`, `test_safe_read_rejects_ancestor_junction`, `test_win32_api_declares_pointer_safe_signatures`, and `test_win32_missing_file_reports_open_failure_not_containment`. All were exercised by the Windows regression job. Python 3.10 additionally skips these seven optional tests because Hypothesis is a test-only dependency requiring Python >=3.11: `test_bibtex_normalization_is_idempotent`, `test_hex_sha256_pattern_is_exact`, `Differential property: production preflight PASS iff the verified ...`, `test_receipt_digest_binds_data_and_signature`, `test_repository_validation_properties`, `test_safe_https_properties`, and `test_unique_object_rejects_any_duplicate_key`. These are optional version/platform skips, not accepted failures.

## Self-application and RFC 3161

- [Self-application run `45991205961`](https://github.com/Unjuno/openpreprint-kit/actions/runs/45991205961) succeeded at the fixed main SHA. The actual paper PDF is 187,504 bytes, SHA-256 `0089e7334e12ea2926a188348563b0f87b2771406aa12df92ab0c91b556616ca`; four negative cases were rejected; publication was explicitly false. The report says independent review/witness are false and does not prove authorship or independent PDF equivalence.
- [Live timestamp/fresh-runner run `45991210476`](https://github.com/Unjuno/openpreprint-kit/actions/runs/45991210476) succeeded at the same SHA. RFC 3161 status `VERIFIED`; timestamp `2026-11-27T11:33:39Z`; pinned CA SHA-256 `2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438`; current signed CRL/full-chain revocation checked; policy OID `1.2.3.4.1`. A separate fresh runner restored and verified the preservation archive, SHA-256 `8dc482914813b56b856e15316532a614ef291d7e423bd58f86d3283c664a000f`.
- TSA accuracy is **unknown** (`accuracy_microseconds: null`). The evidence proves neither authorship nor public availability. The Actions artifacts expire after 14 days; they are not durable custody.

## Live settings and gate readback

Read-only GitHub API readbacks on 2026-11-27 found the `OPK_ADMIN_READ_TOKEN` *name* in both the kit and robustness-eval repositories. Secret values were not accessed.

| Gate | Current finding |
|---|---|
| G0 | Technical evidence passes at `e804fb2105479cfd37ff1bd1117bcc03a7547ffd`; owner acceptance of this exact evidence remains to be recorded. |
| G1 | Partial. The kit has an active main ruleset with required CI but 0 required approving reviews. The first-paper repo has 0 required approvals and administrator enforcement is off. The robustness-eval repo requires 1 approval, all 7 CI contexts, and administrator enforcement; invite `345775144` for `TAKAYASHIKIJUNYA` is still pending and effective permission is read. The two accounts are administered by the same owner and cannot establish independent review. |
| G2 | Blocked. The first paper has its existing immutable v1/v2 Releases; the robustness-eval repo has 0 Releases. No existing immutable Release was changed. |
| G3 | Partial. The current first-paper v1 candidate has verified timestamp/fresh-runner evidence, but the prescribed full evidence set across all four real-paper Releases is incomplete. TSA accuracy remains unknown. |
| G4 | Partial. Public observations exist for the first-paper versions; no second-paper Releases exist to observe. Independence remains `UNPROVEN`. |
| G5 | Partial. Existing first-paper preservation evidence remains; no robustness-eval Releases/assets exist for anonymous retrieval and restore. Separate custody is not claimed. |
| G6 | Blocked. `reviews/record.json` has no human review, correction, or withdrawal events. |
| G7 | Partial. Kit and robustness-eval Actions use the selected six full-SHA-pinned references and require pinning. The first-paper repository still allows all Actions and does not require SHA pinning; the human security/privacy and evidence-lifecycle decisions are outstanding. |

**P4 / toolkit v1.0.0 remains NO-GO.** Do not issue a toolkit Release until G0–G7 formally pass and final owner issuance approval is recorded. Existing paper Immutable Releases remain unchanged. Same-owner account activity is technical evidence only; independence is `UNPROVEN`.

Raw logs, downloaded workflow artifacts, machine-readable check/settings readbacks, and SHA-256 inventory for this checkpoint are in the local post-merge evidence package. Issue #5 is the evidence ledger.
