# Acceptance and review package — current state

## Current fixed-source status

The latest live snapshot is [`ACCEPTANCE_SNAPSHOT_2026-11-29.md`](ACCEPTANCE_SNAPSHOT_2026-11-29.md), fixed to Kit main `39346736ce91371b957ddbfa9b045cbe9409494f`. It supersedes the earlier checkbox snapshot below for current gate decisions. The controlling criteria remain [`V1_ACCEPTANCE.md`](V1_ACCEPTANCE.md); this file does not modify or relax them.

Current formal disposition: G0–G3 **PARTIAL**, G4–G7 **BLOCKED**, P4 **NO-GO**. The Kit has no v1.0.0 Release. Same-owner activity by `Unjuno` and `TAKAYASHIKIJUNYA` may establish technical workflow evidence, but it is not independent human review, audit, or custody. Independence remains `UNPROVEN`.

The live Release inventory is five published Immutable Releases across two template-derived public paper repositories, with 11 assets each; all five `gh release verify` checks passed on 2026-11-29. The four formal target versions and the additional immutable robustness v2.0.0 are listed in the snapshot and fixed-input inventory. This fact corrects older statements that the second repository or its Releases were unavailable; it does not by itself complete G0–G7.

## Current handoffs

- G6 human editorial/privacy review, correction exercise, and withdrawal exercise: [`docs/operator-packages/G6-human-review-handoff-2026-11-29.md`](operator-packages/G6-human-review-handoff-2026-11-29.md).
- Fixed manuscript sources, SHA-256 fingerprints, Release IDs, and all 55 asset digests: [`evidence/acceptance/G6-review-inputs-2026-11-29.json`](../evidence/acceptance/G6-review-inputs-2026-11-29.json). SHA-256: `B300E4E0BF969E6506194FAE4544663407ED425833E282F99FB6E84AA89948F8`.
- Gate-specific status and concrete remaining conditions: [`ACCEPTANCE_SNAPSHOT_2026-11-29.md`](ACCEPTANCE_SNAPSHOT_2026-11-29.md).
- Ongoing evidence log: [Issue #5](https://github.com/Unjuno/openpreprint-kit/issues/5).

## Historical owner checklist (2026-11-21)

The checklist below is preserved as a historical record only. Its checked boxes and its statement that all gates were complete are not valid current PASS evidence: later live GitHub readbacks contradicted its G1/G2 claims, and it contains no current evidence of the required G6 human review, correction exercise, or withdrawal exercise. Do not reuse its check marks for a current release decision.

Historical recorded basis: `main=5cd621e5be001f106260541a8cd303c3d6f1c750`; this is not the current main.

The 2026-11-21 acceptance relaxation remains in force where defined by [`ACCEPTANCE_RELAXATION_2026-11-21.md`](ACCEPTANCE_RELAXATION_2026-11-21.md). It does not turn AI-generated statements or same-owner account switching into human review or proof of independence, and it does not remove G6's actual human actions.
