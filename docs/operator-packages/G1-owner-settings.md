# G1 owner settings and reuse — current action package

**Readback date:** 2026-11-29. This package records configuration facts and remaining owner confirmation. It does not authorize access changes or publish a release.

## Controlling acceptance condition

G1 in [`V1_ACCEPTANCE.md`](../V1_ACCEPTANCE.md) requires an enabled template, two distinct public paper repositories derived from it, and readback of immutable-release settings, protected branches, required CI, and required human review. The owner controls both `Unjuno` and `TAKAYASHIKIJUNYA`; activity from both accounts is technical workflow evidence only. Independence remains `UNPROVEN`.

## Current GitHub readback

| Target | Readback | Evidence source |
|---|---|---|
| `Unjuno/openpreprint-kit` | Public; template enabled; immutable releases enabled (`enforced_by_owner=false`). Active `protect-main` ruleset requires PRs and strict `validate (3.10)`, `validate (3.12)`, `audit`; 0 approving reviews and 0 required reviewers. | `GET /repos/Unjuno/openpreprint-kit`; `/immutable-releases`; `/rulesets/27207738` |
| `Unjuno/openpreprint-kit-paper` | Public; template source is `Unjuno/openpreprint-kit`; immutable releases enabled (`enforced_by_owner=false`). `main` requires strict `validate (3.10)`, `validate (3.12)`, `audit`; 0 approvals; administrator enforcement disabled. | `GET /repos/Unjuno/openpreprint-kit-paper`; `/immutable-releases`; `/branches/main/protection` |
| `Unjuno/openpreprint-kit-robustness-eval` | Public; template source is `Unjuno/openpreprint-kit`; immutable releases enabled (`enforced_by_owner=false`). `main` requires strict `audit`, CodeQL Python, Lean, macOS, Windows and Python 3.10/3.12 validation; 1 approval; administrator enforcement enabled; conversation resolution required. | `GET /repos/Unjuno/openpreprint-kit-robustness-eval`; `/immutable-releases`; `/branches/main/protection` |

Both paper repositories exist and are public. They are distinct template-derived repositories. The current immutable-release and branch-protection readings are also summarized in [`ACCEPTANCE_SNAPSHOT_2026-11-29.md`](../ACCEPTANCE_SNAPSHOT_2026-11-29.md). The second repository's rule does not establish that its approver is an independent person; the owner controls both known accounts.

## Gate status and remaining owner decision

G1 remains **PARTIAL**, not PASS. The template and both paper repositories are present and the immutable-release setting is enabled on each. The Kit template and first-paper repository still require zero approving reviews; first-paper administrator enforcement is disabled. The second-paper repository requires one review and enforces its protection for administrators, but this alone does not close the settings gap across all three repositories or prove independent review.

The owner must decide whether to apply a consistent human-review rule to the Kit and first-paper repository and then read back the resulting settings. Do not change security settings solely from this handoff. Preserve every existing immutable Release. Once configuration is confirmed, record the exact API readbacks and owner decision in Issue #5; record same-owner account activity as `independence=UNPROVEN`.

## Explicit non-claims

- A 404 or repository-list search is not evidence of deletion; the second repository is now directly resolved as public.
- Same-owner account switching does not supply an independent reviewer.
- `enforced_by_owner=false` is not owner-level immutability enforcement; report the actual setting without overstating it.
- Repository settings and CI success do not establish human editorial review or completion of G6.
- No permission change or Kit v1.0.0 Release is performed by this package.
