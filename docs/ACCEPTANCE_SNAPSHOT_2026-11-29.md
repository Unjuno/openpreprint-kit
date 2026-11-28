# OpenPreprint Kit — live acceptance snapshot (2026-11-29)

This is a dated readback, not a change to the formal requirements in [`V1_ACCEPTANCE.md`](V1_ACCEPTANCE.md). It supersedes older statements that the second paper repository or its Releases could not be found. The current evidence ledger is [Issue #5](https://github.com/Unjuno/openpreprint-kit/issues/5).

## Fixed source and checks

- Kit main: `39346736ce91371b957ddbfa9b045cbe9409494f`.
- Required main checks: 7/7 successful on this exact SHA. GitHub run IDs: Validate `45997742039` (3.10/3.12), Quality `45997741896` (audit/Windows/macOS), CodeQL `45997741879`, Lean `45997741914`.
- First-paper self-application: `45997762829` successful on the same SHA; this created no Release.
- First-paper timestamp and fresh-runner restore: `45997767384` successful on the same SHA; this created no Release.
- Synthetic live-acceptance run: `46039624623` successful on the same SHA. Synthetic evidence is not a human review.
- Locked local Windows 11 / Python 3.12.10 / OpenSSL 3.5.6 test run on this source SHA: 441 tests, 0 failures, 0 errors, 16 skips; raw log and skip classifications are in [`windows-test-summary-2026-11-29.json`](../evidence/acceptance/windows-test-summary-2026-11-29.json). Ten symlink tests require Windows symlink privilege and remain required in hosted Windows CI; six POSIX shell tests are not applicable on Windows.
- The Kit currently has zero Releases. P4 remains NO-GO.

## Repositories and settings read back from GitHub

| Repository | Public/template state | Immutable releases | `main` protection readback |
|---|---|---|---|
| `Unjuno/openpreprint-kit` | Public; template | Enabled; `enforced_by_owner=false` | Active `protect-main` ruleset; 3 required checks; 0 approvals |
| `Unjuno/openpreprint-kit-paper` | Public; template source is Kit | Enabled; `enforced_by_owner=false` | Required `validate (3.10)`, `validate (3.12)`, `audit`; 0 approvals; admin enforcement false |
| `Unjuno/openpreprint-kit-robustness-eval` | Public; template source is Kit | Enabled; `enforced_by_owner=false` | 7 required checks; 1 approval; strict checks; admin enforcement true; conversation resolution required |

The same owner controls `Unjuno` and `TAKAYASHIKIJUNYA`. Activity from those accounts is technical workflow evidence only; it does not establish independent review, audit, or custody.

## Published paper Releases

The read-only `gh release verify` command succeeded for all five currently published Immutable Releases. The machine-readable result is [`evidence/acceptance/G2-verify-release-results-2026-11-29.json`](../evidence/acceptance/G2-verify-release-results-2026-11-29.json). Each has 11 attested assets (55 assets total). The four formal minimum-version targets are first-paper `v1`/`v2` and robustness paper `v1.0.0`/`v2.0.1`; the additional immutable robustness `v2.0.0` is retained and verified as history. Its Release was not changed.

| Repository / tag | Release ID | Source SHA | Public state |
|---|---:|---|---|
| [paper v1](https://github.com/Unjuno/openpreprint-kit-paper/releases/tag/v1) | `444659219` | `804cb76a4cf5eea65349fc7a8f01e2ce00e1176d` | Published, immutable, 11 assets |
| [paper v2](https://github.com/Unjuno/openpreprint-kit-paper/releases/tag/v2) | `445442340` | `6ec47ec58e9dc733956615343aad16caca4bb8ee` | Published, immutable, 11 assets |
| [robustness v1.0.0](https://github.com/Unjuno/openpreprint-kit-robustness-eval/releases/tag/v1.0.0) | `461207056` | `dedadf3b2e95090439ec10aa4298db72f048caab` | Published, immutable, 11 assets |
| [robustness v2.0.0](https://github.com/Unjuno/openpreprint-kit-robustness-eval/releases/tag/v2.0.0) | `461231538` | `5b98226d9b7847f08edb8674a89a7f9ae9f1d8e0` | Published, immutable, 11 assets; retained intermediate version |
| [robustness v2.0.1](https://github.com/Unjuno/openpreprint-kit-robustness-eval/releases/tag/v2.0.1) | `461370251` | `256e4743963a3ffb955b017bb3ecb1d91316e602` | Published, immutable, 11 assets |

The first-paper v1/v2 anonymous asset readback is [`evidence/acceptance/first-paper-anonymous-readback-2026-11-29.json`](../evidence/acceptance/first-paper-anonymous-readback-2026-11-29.json); all 22 asset hashes matched. R117 records offline verification/restore for the four formal target versions, and R136 records anonymous downloads, Release/citation/RFC 3161 verification, and offline restore for all three robustness Releases. See [R117](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7239222043) and [R136](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7241822635). R117 also explicitly states that its four-release restore ran on one Windows host; do not describe it as independent or offsite custody.

A fresh Windows 11 readback on 2026-11-29 independently repeated the robustness checks using unauthenticated HTTPS downloads for all three immutable Releases. All 33 assets matched GitHub's published asset digests where available and the corresponding authenticated CLI download byte-for-byte. Release manifest, CFF/BibTeX citation syntax, RFC 3161 chain/signature/current CRL, preservation ZIP, and offline restore all passed for `v1.0.0`, `v2.0.0`, and `v2.0.1`. Machine-readable results, per-asset SHA-256 values, TSA times, and the three preservation-archive SHA-256 values are in [`robustness-release-readback-2026-11-29.json`](../evidence/acceptance/robustness-release-readback-2026-11-29.json); the result is also recorded as [Issue #5 R151](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7244711555). The CA PEM had to be read as the fixed Git blob bytes because the Windows checkout converted LF to CRLF; the verifier correctly rejected the altered byte pin before the exact blob was used. Restoration ran on this same Windows host with HTTP(S) proxies pointed at unreachable loopback; this is technical restore evidence, not independent physical custody.

The old failed robustness `v1` draft, Release ID `461075262`, remains preserved as a draft. It is not counted as a published version and was not modified.

## Open pull requests and CI limitations

- Kit [PR #80](https://github.com/Unjuno/openpreprint-kit/pull/80), exact head `73d1ddfd92e95f101be270f619c5342a4dc6ec5e`, is open with all 18 displayed check runs successful; `reviewDecision` is empty and no approving human review is recorded. The latest two-job read-only hosted workflow passed on run `46182440809`: one GitHub-hosted runner anonymously fetched and verified all five immutable paper Releases (55 assets), then a separate fresh Linux runner restored all five archives with network proxies blocked. All 55 asset bytes were reverified. The recorded artifact IDs, API SHA-256 digests, per-archive hashes, expiry, and limitation are in [`pr80-hosted-release-readback-2026-11-29.json`](../evidence/acceptance/pr80-hosted-release-readback-2026-11-29.json). Both source artifacts expire 2026-12-12 UTC. This is PR evidence until merged; it is not independent human review or durable custody.
- Kit [PR #79](https://github.com/Unjuno/openpreprint-kit/pull/79), exact head `45bcc46eb58cb07a68af88b88fdf0eb08abff582`, is open with 15/15 checks successful. It is not merged; do not treat its SemVer guard as part of main.
- Kit PRs #75/#76 remain open. Kit PRs #73/#74 have CodeQL `startup_failure` on stale base; they need refreshed bases and complete checks before any merge decision.
- Robustness [PR #6](https://github.com/Unjuno/openpreprint-kit-robustness-eval/pull/6) is merged; its displayed 17/17 checks are historical PR checks, while merged main `6faf833e0bf7cbf4ade19da7e23f7051839adcc8` has successful required CI, self-application, CodeQL, and Lean runs.
- Robustness PRs #3/#4 remain open; their exact Dependabot heads `dddb6083d609abff8ad8bc9b2af304b3f1ae6a79` and `a557b583a962ad997cb4bf11857836358c2e370c` had CodeQL startup failures while the other 14 checks passed. Follow-up grouped-update PR #10 is open at `f26a629fea0aa3928e93ef5957ececa79abf4446`, updates the CodeQL actions to v4.39.5, and its current check runs all succeed. No repository allowlist setting was changed; #3/#4 remain open and #10 has no submitted review, so no merge is represented here.
- Robustness PR #1 (pypdf) is open at `8d52a1083a995b9036267337d0ea3a3c841697f4`, with all 18 current check runs successful and no submitted review. The earlier commit `6d7fd5acf375dc8d84d7030d8d78974b1bb3513e` failed because one test still required the old `pypdf==7.1.0` string after the lock had moved to 7.1.1; the updated PR changes that assertion and is green. No merge is represented here.
- Robustness publish run `46095811592` failed at the final publish step with GitHub HTTP 422, `tag_name was used by an immutable release`. The immutable Releases remain intact. PR #6 changed the v1 declaration to unused `v1.0.0`; current immutable v1/v2 releases and the retained `v2.0.0` intermediate are listed above. Draft Release ID `461075262` with tag `v1` remains preserved as history.
- Kit PR #81 is also open at `072e248a9cade486b96c06edfd08e4b0e1070401`; its CodeQL action update and all required checks passed on its exact head. It has not been merged.
- Kit PR #80 is open at exact head `73d1ddfd92e95f101be270f619c5342a4dc6ec5e` with all displayed check runs successful. Fixed-blob G6 inventory validation, hosted verification of all five Releases/55 assets, fresh-runner offline restore, self-application, and platform CI succeeded on runs `46182440809`, `46182440777`, `46182440798`, `46182440772`, `46182440789`, `46182440807`, `46182436607`, `46182436617`, and `46182436609`. The fresh hosted artifact report is [`pr80-hosted-release-readback-2026-11-29.json`](../evidence/acceptance/pr80-hosted-release-readback-2026-11-29.json). This remains PR evidence until merged. The owner left a COMMENTED review record on an earlier commit; it is not an approval or an independent review.

The exact-head status of every open PR must be reread before merging. Earlier approval prompts for PR #79 and repository-specific allowlist changes are not themselves approvals. No merge or settings change is made by this snapshot.

## Gate status and remaining conditions

The formal results remain G0–G3 **PARTIAL**, G4–G7 **BLOCKED**, and P4 **NO-GO**, as recorded in R136. This document strengthens and corrects the observed Release inventory; it does not silently promote a formal gate.

| Gate | Current status | Concrete missing condition |
|---|---|---|
| G0 | PARTIAL | Owner must confirm exact-source quality/security evidence and resolve the open CI/policy review items. Current main CI and self-application evidence are successful. |
| G1 | PARTIAL | Kit and first-paper branch rules have 0 required approvals; first-paper admin enforcement is false. Bring configuration/readback into line with the frozen acceptance table, then record owner confirmation. |
| G2 | PARTIAL | Five published Immutable Releases and their 55 attestations verify; owner must check the full acceptance evidence set, including citation/research payload and v1-after-v2 preservation, against the fixed target. |
| G3 | PARTIAL | Windows R117 plus Ubuntu WSL on this same physical Windows 11 machine provide 12 normal timestamp-verification run-events across the four formal targets and extra robustness v2.0.0; WSL verified all five releases. The fixed 20-case matrix passed on Windows (R118) and WSL (23/23 rejection judgments, 0 false accepts). The 2026-11-29 Windows test run passed 441/441 executed tests; ten local symlink-privilege skips remain required in hosted Windows CI. Windows and WSL are not independent physical hosts. PR #80's two-job GitHub-hosted workflow passed on exact PR head `73d1ddfd92e95f101be270f619c5342a4dc6ec5e`, including separate-runner offline restoration of all five Releases/55 assets. This remains PR evidence until merged; it does not establish long-term custody or formal gate completion. |
| G4 | BLOCKED | Complete the formal observation records for all four target versions, including the required signed/timestamped observation evidence; account independence remains `UNPROVEN`. |
| G5 | BLOCKED | The four target restore records are available, but the complete retention/fingerprint handoff must be fixed and confirmed by the named owner/custodian; do not claim independently managed custody. |
| G6 | BLOCKED | A real human must decide rights, consent, COI and privacy, complete one review, one correction exercise, and one withdrawal exercise. The handoff package is not completion evidence. |
| G7 | BLOCKED | Owner must confirm the fixed-SHA security/privacy assessment, lifecycle and recovery test evidence, residual risks, and ongoing maintenance responsibility. No external audit is claimed or required by the current formal criteria. |

Additional same-host measurements: [WSL RFC 3161 results](../evidence/acceptance/wsl-g3-verification/wsl-g3-summary.json) record five `VERIFIED` results using Ubuntu Python 3.12.3/OpenSSL 3.0.13; [WSL negative-suite record](../evidence/acceptance/g3-negative-suite-wsl/execution-record.json) records 20 fixed cases, 23 rejection judgments, 0 false accepts, and exit code 0. These do not establish physical host independence. PR #80 adds GitHub-hosted anonymous verification and fresh-runner restoration; the evidence is not part of main until merged and does not itself change the formal gate status.

No formal criterion is relaxed here. Do not publish Kit v1.0.0 until all G0–G7 are formally PASS and the owner provides explicit final issuance approval.

## Current human handoff

- [G6 review and editorial/privacy handoff](operator-packages/G6-human-review-handoff-2026-11-29.md)
- [Fixed input hashes, all release asset digests, and source inventory](../evidence/acceptance/G6-review-inputs-2026-11-29.json)
- Input inventory SHA-256: `C5D05B3960BDB589F8A2B4BBCD830A1E4A44BA255239B1C0A745E50A59EE1CE5` (recomputed from the checked-in JSON; the previous `B300…` value was stale and is superseded).
