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
