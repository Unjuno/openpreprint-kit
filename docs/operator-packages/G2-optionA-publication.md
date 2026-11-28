# G2 — formal four-release publication and verification record

**Readback date:** 2026-11-29. The second paper repository and its public Releases now exist. Older statements below earlier historical snapshots that it was unresolved or unpublished are superseded by this record and [`ACCEPTANCE_SNAPSHOT_2026-11-29.md`](../ACCEPTANCE_SNAPSHOT_2026-11-29.md). This package records evidence and remaining owner confirmation; it does not change an immutable Release.

## Formal condition

The controlling criteria are G2 in [`V1_ACCEPTANCE.md`](../V1_ACCEPTANCE.md): at least two template-derived paper repositories, two immutable versions per repository (**計4件以上** formal target Releases), at least one owner-approved substantive paper, and verification of every Release and asset for attestations, anonymous retrieval, citation and research payload consistency, and preservation of v1 after v2. Gate status is not changed merely because the files below exist. The owner reviews and confirms the evidence; independence remains `UNPROVEN` because both GitHub accounts are controlled by the same owner.

## Formal target Releases

| Paper repository | Version | Release ID / source SHA | Current readback |
|---|---|---|---|
| [`openpreprint-kit-paper`](https://github.com/Unjuno/openpreprint-kit-paper) | v1 | `444659219` / `804cb76a4cf5eea65349fc7a8f01e2ce00e1176d` | Published, immutable; 11 assets; `gh release verify` PASS; anonymous asset digest readback PASS |
| [`openpreprint-kit-paper`](https://github.com/Unjuno/openpreprint-kit-paper) | v2 | `445442340` / `6ec47ec58e9dc733956615343aad16caca4bb8ee` | Published, immutable; 11 assets; `gh release verify` PASS; anonymous asset digest readback PASS |
| [`openpreprint-kit-robustness-eval`](https://github.com/Unjuno/openpreprint-kit-robustness-eval) | v1.0.0 | `461207056` / `dedadf3b2e95090439ec10aa4298db72f048caab` | Published, immutable; 11 assets; `gh release verify` PASS; anonymous asset digest readback PASS |
| [`openpreprint-kit-robustness-eval`](https://github.com/Unjuno/openpreprint-kit-robustness-eval) | v2.0.1 | `461370251` / `256e4743963a3ffb955b017bb3ecb1d91316e602` | Published, immutable; 11 assets; `gh release verify` PASS; anonymous asset digest readback PASS |

Robustness `v2.0.0`, Release ID `461231538`, source `5b98226d9b7847f08edb8674a89a7f9ae9f1d8e0`, is an additional immutable intermediate retained and verified in the evidence. Failed draft ID `461075262` is historical, remains a draft, and is not counted. No existing immutable Release was modified.

## Evidence already collected

- [`G2-verify-release-results-2026-11-29.json`](../../evidence/acceptance/G2-verify-release-results-2026-11-29.json): `gh release verify` PASS for all five published Releases, 55 attested assets.
- [`first-paper-anonymous-readback-2026-11-29.json`](../../evidence/acceptance/first-paper-anonymous-readback-2026-11-29.json): 22 v1/v2 asset digests matched.
- [`robustness-release-readback-2026-11-29.json`](../../evidence/acceptance/robustness-release-readback-2026-11-29.json), SHA-256 `bf878b49138035098b9ecbbc65a24d74c3438668a6186aeeb64ff73b97932762`: fresh unauthenticated HTTPS retrieval of the three robustness Releases; all 33 asset hashes match GitHub digest where available and authenticated CLI bytes; CFF/BibTeX validation, manifest verification, RFC 3161 chain/signature/current CRL verification, preservation packing, offline restore, and restored-byte equality PASS. Restoration ran on the same Windows host with proxies pointed at unreachable loopback; it is not separate physical custody.
- [`Issue #5 R117`](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7239222043) and [`R136`](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7241822635): four-target offline verification/restore and robustness publication evidence.
- [`Issue #5 R151`](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7244711555): detailed robustness readback, failures, per-asset digests and archive hashes.
- Kit PR #80 [exact head `73d1ddfd92e95f101be270f619c5342a4dc6ec5e`](https://github.com/Unjuno/openpreprint-kit/pull/80/checks), run `46182440809`: anonymous download and verify of all five immutable Releases/55 assets followed by restore on a separate fresh GitHub-hosted Linux runner with network proxies blocked; 5/5 archives and 55/55 restored assets PASS. This is PR evidence until merged; its Actions artifacts are temporary and do not establish long-term custody.

The source lineage, Release IDs, all 55 asset hashes, and immutable status are collated in the linked machine-readable readback. Citation parser success does not certify citation truth, manuscript quality, authorship, rights, publication consent, peer review, or scientific correctness.

## Owner confirmation still required for G2

G2 remains **PARTIAL** in the formal ledger until the owner checks the complete four-target evidence against the frozen condition and records the decision in Issue #5. In particular, the owner should confirm the formal target selection, owner-approved substantive paper, citation and research-payload comparison, and post-v2 preservation of both v1 Releases. Do not infer these judgments from AI or GitHub activity alone. If any asset differs from its fixed digest, stop and record the discrepancy; do not replace or reissue an immutable Release to hide it.

## Restrictions

- Preserve all immutable Releases, including the additional robustness `v2.0.0` intermediate and the failed historical draft.
- Keep the three synthetic-demo Releases as historical mechanism tests; do not count them as either paper repository.
- Same-owner account switching is technical evidence only and never an independent review.
- This record does not authorize new publication or the Kit `v1.0.0` Release. P4 remains NO-GO until every G0–G7 gate is PASS and the owner gives explicit final issuance approval.
