# G7 Actions policy hardening — readback and rerun evidence

Observed on 2026-11-23 UTC after owner authorization to apply the G7 Actions hardening proposal. Source code baseline: `76d7d4c6fd551bb48048d774e47191ba26274cbf`.

## Applied repository policy

GitHub REST readback for `Unjuno/openpreprint-kit`:

- Actions enabled: `true`
- Allowed actions: `selected`
- Full-SHA pinning required: `true`
- GitHub-owned actions allowed by default: `false`
- Verified actions allowed by default: `false`
- Exact allowlist:
  - `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`
  - `actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0`
  - `actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9`
  - `actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333`

The initial owner proposal omitted `actions/download-artifact`, although fixed main used it in the first-paper timestamp and live-acceptance workflows. The first post-change timestamp run `45132587300` ended `startup_failure` before creating a job. The missing reference was confirmed at the fixed source SHA and its upstream commit is [`9000827ccba6bdab643e8b6fd33ac0654aef8333`](https://github.com/actions/download-artifact/commit/9000827ccba6bdab643e8b6fd33ac0654aef8333) (v8.0.2). This exact full-SHA reference was added; default action access remains denied.

## Post-change workflow evidence

- Self-application: [run 45132587326](https://github.com/Unjuno/openpreprint-kit/actions/runs/45132587326) — success; job installed dependencies and executed the self-application test suite.
- Live RFC 3161 timestamp and second-runner verification: [run 45133161597](https://github.com/Unjuno/openpreprint-kit/actions/runs/45133161597) — both `stamp-v1` and `fresh-verify` jobs succeeded. The fresh verifier executed the newly allowlisted `actions/download-artifact` step, fetched a pinned FreeTSA CA and signed current CRL, restored the preservation ZIP, and verified it.
- Synthetic live acceptance: [run 45133363406](https://github.com/Unjuno/openpreprint-kit/actions/runs/45133363406) — success for v1/v2 synthetic fixtures; timestamp verification, tamper rejection, restore byte equality and v1 preservation all passed. The workflow explicitly reports `github_release=NOT_CREATED`, `public_availability=NOT_PROVEN`, and `human_review=NOT_PERFORMED`.

The first-paper archive SHA-256 is `83238e849b86c0ae6c50680585d2fa2adb0fbde4f8a94ffb8655860f49b6051d`; the workflow's fresh-verify report binds the same SHA and reports `PASS`. Synthetic archive SHA-256 values are `4b61fbd6ebe1d1a3fe44003082243cb13ada7c4944e24c1b9d4bd8528f65de65` (v1) and `4c582e468191dfe066db290843d23743729d43beb6b92bf2f086f0ac5a2ec1f0` (v2). GitHub Actions artifacts are temporary retention, not independent or permanent custody.

This evidence establishes the configured allowlist and successful post-change workflows. It does not establish an independent security review, long-term custody, public publication, or toolkit v1.0.0 acceptance. Required CI on this documentation PR is reported by its own commit checks.

## CodeQL startup failure on PR #72 — 2026-11-23 readback

PR #72 head `b0982b447d30c5f4407dddd731d2d61226f523bf` has six of seven required contexts successful. Its required CodeQL run [45134001861](https://github.com/Unjuno/openpreprint-kit/actions/runs/45134001861) ended `startup_failure` before creating a job. The GitHub annotation states that the existing workflow references `github/codeql-action/init@33d7b85da1a04171e211befe2c739303b9a4c066` and `github/codeql-action/analyze@33d7b85da1a04171e211befe2c739303b9a4c066`, and that these are denied because the selected allowlist only contains the four `actions/*` references above. The exact SHA is the official CodeQL Action v4.39.3 commit: [GitHub source](https://github.com/github/codeql-action/commit/33d7b85da1a04171e211befe2c739303b9a4c066).

The narrow proposed correction is to add only `github/codeql-action@33d7b85da1a04171e211befe2c739303b9a4c066`, keeping full-SHA pinning mandatory and both broad default checkboxes disabled. This security-sensitive permission expansion is **not yet saved**; owner action-time confirmation is pending. The allowlist correction must be read back and the seven required PR contexts rerun successfully before this evidence PR is ready to merge. G7 remains PARTIAL; no toolkit Release was created.

## Current allowlist readback (2026-11-25)

The owner-authorized setting was applied after the 2026-11-23 observation above. A live REST readback on 2026-11-25 reported `github_owned_allowed=false`, `verified_allowed=false`, and these additional explicit full-SHA references:

- `github/codeql-action/init@33d7b85da1a04171e211befe2c739303b9a4c066`
- `github/codeql-action/analyze@33d7b85da1a04171e211befe2c739303b9a4c066`

`sha_pinning_required=true` and `allowed_actions=selected` remain enabled. The effective policy is the two exact sub-action patterns above; the earlier proposal text naming one combined `github/codeql-action@...` pattern is not the current readback.

For PR #72 head `18facac1bae0c1e7f3ef8f8d663831a1ad1c4e43`, CodeQL `workflow_dispatch` run [45158561375](https://github.com/Unjuno/openpreprint-kit/actions/runs/45158561375) completed successfully. The original PR-event CodeQL run [45152140381](https://github.com/Unjuno/openpreprint-kit/actions/runs/45152140381) remains `startup_failure`; GitHub does not permit rerunning that startup-failed run. Thus the successful dispatch proves the workflow can run with the updated policy, but does not prove a fresh pull-request event succeeded. A new PR head is needed to trigger that event and verify it. No Release was created.

## Fresh pull-request event verification at PR #72 head `bc679e15849267e1f229935d34b58f7914457feb` — 2026-11-25

The earlier note above said a new PR head was needed because the CodeQL pull-request run on head `18facac1bae0c1e7f3ef8f8d663831a1ad1c4e43` ended at startup. That historical limitation was resolved by a later head. On `bc679e15849267e1f229935d34b58f7914457feb`, the actual `pull_request` CodeQL security-analysis run [45682418076](https://github.com/Unjuno/openpreprint-kit/actions/runs/45682418076) completed successfully. Its job executed both pinned references, `github/codeql-action/init@33d7b85da1a04171e211befe2c739303b9a4c066` and `github/codeql-action/analyze@33d7b85da1a04171e211befe2c739303b9a4c066`.

GitHub's current PR check readback shows success for the CodeQL app context, CodeQL Python, audit, Lean proofs, Validate Python 3.10 and 3.12, Windows regression, and macOS regression at this head. The latest source workflow runs are [CodeQL](https://github.com/Unjuno/openpreprint-kit/actions/runs/45682418076), [quality and reproducible source](https://github.com/Unjuno/openpreprint-kit/actions/runs/45682418121), [Lean](https://github.com/Unjuno/openpreprint-kit/actions/runs/45682418068), and [validation](https://github.com/Unjuno/openpreprint-kit/actions/runs/45682419743). The app-provided CodeQL context is [also green](https://github.com/Unjuno/openpreprint-kit/runs/139447422807).

Accordingly, the 2026-11-23 and 2026-11-25 startup failures remain historical evidence and are not current-head failures. No Release was created. This CI result proves workflow execution under the selected allowlist; it does not prove independent human review or satisfy other G7 human acceptance requirements.

## Fresh GitHub Actions settings readback — 2026-11-26

A new read-only REST readback was taken on 2026-11-26 at `2026-11-26T04:19:27Z` for repository `Unjuno/openpreprint-kit`, source main SHA `76d7d4c6fd551bb48048d774e47191ba26274cbf`. The machine-readable record is [`ACTIONS_SETTINGS_READBACK_2026-11-26.json`](ACTIONS_SETTINGS_READBACK_2026-11-26.json), SHA-256 `75259eb23718ba2901003f71a65b0aa0a5b256021f3fb5de6e1cbaf72a2929ed`.

The effective settings remain: Actions enabled; `allowed_actions=selected`; `sha_pinning_required=true`; `github_owned_allowed=false`; `verified_allowed=false`; the exact six SHA-pinned action references listed in the JSON; default workflow token permission `read`; `can_approve_pull_request_reviews=false`; Immutable Releases enabled. No secret values were read.

PR #72 head `6584ae61c74949900edccf30d3c58dec9d33d3d9` remains open and unmerged; its current CodeQL, CodeQL Python, audit, Lean, Python 3.10/3.12, Windows, and macOS checks pass. This settings and CI evidence supports the technical configuration claim only. Formal G7 remains PARTIAL pending full acceptance; no independent review, audit, or permanent custody is claimed. No Release was created.
