# G1 owner settings and reuse — action package

**Status:** NOT CONFIRMED. Readback snapshot: 2026-11-21 UTC (2026-11-22 JST). This package is a handoff for owner decisions; it changes no settings and publishes no repository.

## Controlling acceptance condition

G1 in [`V1_ACCEPTANCE.md`](../V1_ACCEPTANCE.md) requires an enabled template, two distinct public paper repositories derived from it, and readback of immutable release settings, protected branches, required CI, and required human review. Do not treat account switching by the same owner as independent review. Independence is recorded as `UNPROVEN`.

## Live readback

| Target | Readback | Evidence |
|---|---|---|
| `Unjuno/openpreprint-kit` | Public; `is_template=true`; immutable releases `enabled=true`, `enforced_by_owner=false` | GitHub REST `GET /repos/Unjuno/openpreprint-kit`; `GET /repos/Unjuno/openpreprint-kit/immutable-releases` |
| Template branch rule | Active ruleset `protect-main` (ID `27207738`) applies to default branch; deletion and non-fast-forward are restricted; PRs and required status checks `validate (3.12)`, `validate (3.10)`, `audit` are required; strict checks enabled. Required approvals `0`; required reviewers empty; no bypass actors | `GET /repos/Unjuno/openpreprint-kit/rulesets/27207738` |
| `Unjuno/openpreprint-kit-paper` | Public; `template_repository=Unjuno/openpreprint-kit`; immutable releases `enabled=true`, `enforced_by_owner=false` | `GET /repos/Unjuno/openpreprint-kit-paper`; `GET /repos/Unjuno/openpreprint-kit-paper/immutable-releases` |
| paper `main` protection | Required checks `validate (3.12)`, `validate (3.10)`, `audit`; classic branch protection exists; required approvals `0`; `require_code_owner_reviews=false`; repository has no rulesets | `GET /repos/Unjuno/openpreprint-kit-paper/branches/main/protection`; `GET /repos/Unjuno/openpreprint-kit-paper/rulesets` |
| Second actual paper repository | `Unjuno/openpreprint-kit-robustness-eval` returns 404 on readback. Owner reports current repo/G6 source records absent or unknown. This does not prove deletion or establish a different location. | `GET /repos/Unjuno/openpreprint-kit-robustness-eval`; user response in this conversation |

The main toolkit repository's separate active `protect-main` ruleset does not establish a qualifying human approval requirement: it currently permits zero approving reviews. The paper repository's protection has the same zero-approval condition. Immutable enabled is a positive configuration readback; `enforced_by_owner=false` means do not overstate owner-level enforcement.

## Owner actions to close G1

1. **Human review rule:** decide and authorize a concrete settings change that requires an actual human approval for protected changes. Suggested minimum is one approving review on the toolkit template and on each paper repository, alongside the existing strict required CI. Identify a reviewer who is not the PR author. If the same owner operates the reviewing account, record the review as owner-operated and `independence=UNPROVEN`; never call it independent. Settings changes are not applied by this document.
2. **Current paper repo:** confirm the reviewed branch and immutable-release configuration remain correct after any ruleset change. Preserve all immutable releases.
3. **Second actual paper repo:** locate the existing repository and provide its URL and read-only configuration evidence, or explicitly authorize creation from the template after the manuscript's author/content/license approval is ready. Current local manuscript candidate files are not proof of public repository existence or publication approval.
4. **Final readback:** record repository URLs, `template_repository` provenance, public visibility, immutable setting before any future release, active protected branches, required CI names, required approval count/reviewer rule, and observed timestamp in Issue #5. Recheck that no existing immutable release changed.

## State and non-actions

- G1 remains `NOT CONFIRMED`; current paper repo establishes one template-derived public paper repo only.
- G2 is separately `NOT CONFIRMED`: only the paper repo's v1/v2 actual-paper Releases are currently resolvable. Historical demo repos cannot replace the formal two-paper/two-version requirement.
- No permission change, new repository, paper Release, or toolkit v1.0.0 Release was made while preparing this handoff.
- The local manuscript `manuscripts/openpreprint-kit-robustness-eval/` is marked owner-approval-pending; its presence does not supply the required public repository or author approval.
