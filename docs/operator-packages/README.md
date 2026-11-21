# Operator packages — current acceptance basis

The controlling acceptance table is [`docs/V1_ACCEPTANCE.md`](../V1_ACCEPTANCE.md), based on the owner-approved 2026-11-21 criteria. The detailed G4/G5/G7 files in this directory were written for the stricter 2026-11-14 process. They remain useful as optional high-assurance procedures, but any requirement in them for a separate independent witness, separately managed custodian, or external auditor is **not a current mandatory gate**. Do not represent optional independence as achieved unless it is evidenced; otherwise record `UNPROVEN`.

Current scope by gate:

- **G1:** [G1-owner-settings.md](G1-owner-settings.md) records current live readbacks and the owner actions needed for template reuse, immutable settings, branch protection, required CI/human review, and a second actual paper repository. No permission or publication operation has been carried out by creating this package.

- **G4:** the owner may perform anonymous retrieval and create signed, timestamped observation records. The records must cover every formal G2 release and its assets. Record independence as `UNPROVEN` when the operator is the owner.
- **G5:** the owner may manage the mirror and offline recovery. Preserve immutable copies, separately recorded fingerprints, and successful GitHub-disconnected restore evidence for the formal target set. Do not claim separate custody unless demonstrated.
- **G6:** actual human rights/consent/COI decisions, one human review process, one correction exercise, and one withdrawal exercise remain required. AI-generated statements or tests do not substitute for these actions. [G6-human-review.md](G6-human-review.md) is the operative handoff checklist.
- **G7:** an owner-confirmed security/privacy assessment against the fixed source SHA, lifecycle/renewal/recovery exercises, no unresolved critical/high finding, and an assigned maintenance owner are required. A third-party external audit is optional under the current criteria; never claim one unless it was actually performed.
- **G2 dependency:** G4/G5 evidence must match the formal four-release target. Current Readiness reports that `openpreprint-kit-robustness-eval` is not resolvable; resolve that discrepancy before using the old target list.

| File | Use |
|---|---|
| [G4-independent-observer.md](G4-independent-observer.md) | Optional independent observation procedure; current owner-operated route is described above. |
| [G5-custodian-handover.md](G5-custodian-handover.md) | Optional separately managed custody procedure; current owner-operated route is described above. |
| [G6-human-review.md](G6-human-review.md) | Required human editorial/privacy actions and record contents. |
| [G7-external-audit.md](G7-external-audit.md) | Optional external assessment procedure; current owner-confirmed G7 scope is described above. |

Current live verdict: **P4 = NO-GO**. G1/G2 were not reconfirmed because the second publication repository cannot currently be resolved; G6 source records are absent or unknown. See [RELEASE_READINESS.md](../RELEASE_READINESS.md) and [Issue #5](https://github.com/Unjuno/openpreprint-kit/issues/5).
