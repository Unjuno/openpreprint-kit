# Post-merge quality and self-application evidence — PR #77 checkpoint

## Fixed source and required CI

- Source: `Unjuno/openpreprint-kit` main `fa279d43a1d68fb227d94194cbee739c10d2afef`.
- PR #77 head `b732223c8adedaca8b0485d04faade5d692b27d6` merged as the fixed main SHA on 2026-11-27T11:55:39Z. The PR updated readiness/evidence documentation only.
- Exact-main required checks: **7/7 success**. [Quality `45994431309`](https://github.com/Unjuno/openpreprint-kit/actions/runs/45994431309), [validation `45994431162`](https://github.com/Unjuno/openpreprint-kit/actions/runs/45994431162), [Lean `45994431259`](https://github.com/Unjuno/openpreprint-kit/actions/runs/45994431259), and [CodeQL `45994431251`](https://github.com/Unjuno/openpreprint-kit/actions/runs/45994431251).
- Windows: 441 tests, 435 passed, 6 POSIX-shell tests skipped, 0 failures/errors. macOS, Linux audit, and Python 3.12 each: 441, 435 passed, 6 Windows-only tests skipped, 0 failures/errors. Python 3.10: 441, 428 passed, 13 skips (6 Windows-only plus 7 test-only Hypothesis cases not installed for Python 3.10), 0 failures/errors.
- Windows-only skips on POSIX jobs: `test_inherited_broad_read_ace_is_rejected_before_key_creation`, `test_localized_group_display_names_cannot_bypass_wide_read_sid`, `test_unknown_trustee_sid_is_rejected_before_key_creation`, `test_safe_read_rejects_ancestor_junction`, `test_win32_api_declares_pointer_safe_signatures`, and `test_win32_missing_file_reports_open_failure_not_containment`; all were exercised by the Windows runner. Python 3.10-only optional skips: `test_bibtex_normalization_is_idempotent`, `test_hex_sha256_pattern_is_exact`, `Differential property: production preflight PASS iff the verified ...`, `test_receipt_digest_binds_data_and_signature`, `test_repository_validation_properties`, `test_safe_https_properties`, and `test_unique_object_rejects_any_duplicate_key`.

## Self-application and timestamp

- [Self-application `45994944364`](https://github.com/Unjuno/openpreprint-kit/actions/runs/45994944364) passed on the fixed main SHA. PDF: 187,504 bytes, SHA-256 `5140bee8c776a7e5ac2fd1ec0f6a0ec8e7c6f1e86ee3bc9e425610288fa59e28`. Four negative cases were rejected. Publication was false.
- [Live RFC 3161 and fresh-runner `45994952803`](https://github.com/Unjuno/openpreprint-kit/actions/runs/45994952803) passed on the same main SHA. TSA time `2026-11-27T12:01:29Z`; CA SHA-256 `2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438`; policy OID `1.2.3.4.1`; full-chain current CRLs checked; preservation archive SHA-256 `87f7ffd0bbfc9e161f81dd26e3ce57fecd1dbfa5eda713bbdb5e4acab63fbcb7`. A separate fresh runner restored and reverified the archive.
- Accuracy is unknown, authorship is not proven, and public availability is not proven. Actions artifacts expire after 14 days.

## First-paper Actions hardening

- On 2026-11-27, `Unjuno/openpreprint-kit-paper` Actions changed from `allowed_actions=all` and `sha_pinning_required=false` to `allowed_actions=selected` and `sha_pinning_required=true`. Default GitHub-owned and verified actions remain disabled.
- The allowlist contains only the four exact action references used by its workflows: checkout `3d3c42e5aac5ba805825da76410c181273ba90b1`, setup-python `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0`, upload-artifact `cf430e030ddbb5b0abf93d22962f4752f3646cd9`, and download-artifact `9000827ccba6bdab643e8b6fd33ac0654aef8333`.
- On paper main `6ec47ec58e9dc733956615343aad16caca4bb8ee`, [self-application `45995399456`](https://github.com/Unjuno/openpreprint-kit-paper/actions/runs/45995399456) and [timestamp/fresh-runner `45995415275`](https://github.com/Unjuno/openpreprint-kit-paper/actions/runs/45995415275) both passed under this policy. The existing immutable releases were not changed.

## Gate and release state

- G0: exact-main technical evidence passes; owner acknowledgement of this exact checkpoint remains to be recorded.
- G1: PARTIAL; kit and first-paper repositories require 0 approvals. Robustness-eval PR #2 still requires a review; invite `345775144` remains pending. The two accounts are managed by the same owner and do not count as independent.
- G2: BLOCKED; first-paper immutable v1/v2 remain intact; robustness-eval has zero Releases.
- G3-G5: PARTIAL; full four-version publication evidence, public observation, anonymous retrieval, and disconnected restoration are incomplete.
- G6: BLOCKED; no human review, correction, or withdrawal event is recorded.
- G7: PARTIAL; Actions hardening is implemented and tested, while owner security/privacy, lifecycle, expiry/revocation, maintenance, and recovery decisions remain.

`OPK_ADMIN_READ_TOKEN` secret names are present in kit and robustness-eval; values were never read. No existing immutable Release was changed. No robustness-eval or toolkit Release was created. P4 / toolkit v1.0.0 remains **NO-GO** until formal G0-G7 PASS and separate final issuance approval.
