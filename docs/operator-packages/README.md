# Operator acceptance packages (G4–G7) and current verdict

This directory contains the concrete, ready-to-send packages for the
owner-designated **independent humans** required by the v1.0.0 gates.
No human has been selected yet (owner, 2026-11-14). Until a real person
performs each task and records it in Issue #5, the corresponding gate is
NOT PASS — not even with AI assistance.

- [G4-independent-observer.md](G4-independent-observer.md) — independent observer (different key/environment), anonymous retrieval, signature + RFC 3161 receipts
- [G5-custodian-handover.md](G5-custodian-handover.md) — separately managed custodian: receipt, re-hash, immutable GitHub mirror, offline restore without GitHub
- [G6-human-review.md](G6-human-review.md) — human editorial/privacy review, rights/COI consent, 1 review + 1 correction + 1 withdrawal exercise
- [G7-external-audit.md](G7-external-audit.md) — external security/privacy audit of pinned SHA the SHA current at audit time (as of writing: `84ca91cd…` / `b735988e…`; auditor MUST re-pin to the SHA current when the audit starts, e.g., the v1.0.0 tag)

Current verdict (2026-11-14): **P4 = NO-GO**. P1 = PASS. P2 = PARTIAL. P3 = BLOCKED.

See `evidence/acceptance/gate-evidence-matrix-2026-11-14.md` for what is verified,
`evidence/acceptance/g2-criterion-impact-2026-11-14.md` for the G2 criterion
mismatch and options A/B, and `evidence/acceptance/unresolved-blockers-2026-11-14.md`
for the full blocker list.
