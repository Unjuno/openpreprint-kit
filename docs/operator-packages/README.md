# Operator handoffs — current acceptance state

The controlling requirements are [`docs/V1_ACCEPTANCE.md`](../V1_ACCEPTANCE.md). The latest fixed-source status is [`docs/ACCEPTANCE_SNAPSHOT_2026-11-29.md`](../ACCEPTANCE_SNAPSHOT_2026-11-29.md), based on Kit main `39346736ce91371b957ddbfa9b045cbe9409494f`. Current evidence and decisions are tracked in [Issue #5](https://github.com/Unjuno/openpreprint-kit/issues/5).

The two public paper repositories exist and declare the Kit as their template source:

- [`openpreprint-kit-paper`](https://github.com/Unjuno/openpreprint-kit-paper)
- [`openpreprint-kit-robustness-eval`](https://github.com/Unjuno/openpreprint-kit-robustness-eval)

Their live repository settings and all five currently published Immutable Releases are listed in the snapshot. Do not use older handoff text saying that the second repository or its Releases are missing.

## Current gates

- **G1 — PARTIAL:** template-derived public repositories and immutable setting are verified; the Kit and first-paper branch rules still require zero approving reviews, and first-paper admin enforcement is off.
- **G2 — PARTIAL:** five published Immutable Releases and 55 attested assets verify; owner confirmation against the full acceptance checklist remains.
- **G4 — BLOCKED:** complete formal public-observation records for all four target versions. Same-owner account activity is not independent observation.
- **G5 — BLOCKED:** retain the four target offline restores and separate fingerprints, and complete the named-owner retention/maintenance readback. No independently managed custody is claimed.
- **G6 — BLOCKED:** a real human must complete the editorial/privacy decision, review, synthetic correction exercise, and synthetic withdrawal exercise. See the [2026-11-29 handoff](G6-human-review-handoff-2026-11-29.md).
- **G7 — BLOCKED:** owner confirmation of fixed-SHA security/privacy assessment, lifecycle/recovery evidence, residual risks, and ongoing maintenance responsibility is still needed. External audit is optional under the current formal criteria and is not claimed.

Do not treat a handoff document as evidence that the requested human action occurred. `Unjuno` and `TAKAYASHIKIJUNYA` have the same owner; that activity can test technical paths but cannot be counted as independent human review/audit/custody.

## Procedures

| File | Use |
|---|---|
| [G1-owner-settings.md](G1-owner-settings.md) | Historical setup instructions; see the current snapshot for readback. |
| [G2-optionA-publication.md](G2-optionA-publication.md) | Historical first-publication handoff; all current published releases are listed in the snapshot. |
| [G4-independent-observer.md](G4-independent-observer.md) | Optional independent observation procedure; do not claim independence without evidence. |
| [G5-custodian-handover.md](G5-custodian-handover.md) | Optional separate custodian procedure; the formal GitHub-only and offline-restore criteria remain in force. |
| [G6-human-review.md](G6-human-review.md) | Formal human decisions and exercise requirements. |
| [G6-human-review-handoff-2026-11-29.md](G6-human-review-handoff-2026-11-29.md) | Current fixed-input package ready for a real reviewer. |
| [G7-external-audit.md](G7-external-audit.md) | Optional external-audit procedure; the current formal G7 can be owner-confirmed. |
