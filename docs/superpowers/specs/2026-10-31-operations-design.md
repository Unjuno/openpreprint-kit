# Operational readiness design

## Intent
Extend the existing RFC 3161 prototype into an auditable publication workflow with
human review/correction records, a static reader view, and fail-closed pre-publication checks.
Do not claim a preprint is peer-reviewed merely because CI passes or reports exist.

## Decisions and alternatives
The user requested implementation, delegated engineering decisions, and explicitly
required limitations to be disclosed. Keep Python and GitHub; do not build another
hosted service. A centralized editorial platform would introduce authentication and
operational requirements outside this toolkit. Markdown-only policies would not
prevent silent record deletion; use typed JSON records and a baseline comparison.
No callable software-development subagent is available in this session; implementation
and self-review are inline. Independent human/security review remains a release gate.

## Scope
1. Preflight: read GitHub REST metadata, explicit immutable-release setting and exact
   default-branch commit; only an actual 404 means an unused tag/release. Do not publish
   with unavailable administrative read access. Re-check immutable setting before promotion.
2. Research record: events bind version and PDF SHA-256 to report bytes, actor assertions,
   declared conflicts, and UTC claimed record time. Reviews, responses, corrections,
   concerns and retractions. No automated scientific acceptance. Changes are append-only
   against a trusted base snapshot; this is not proof against an owner rewriting all history.
3. Reader view: static, escaped HTML, version-specific PDF/citations, prominent status
   and notices. Timestamp presence is not timestamp verification. No automatic Pages deployment.
4. Operations: issue forms, confidential-report guidance, contributor checks, tested-source
   artifacts and explicit blocking acceptance checklist. Do not publish a real paper or
   enroll a TSA/pay for services without actual research content/trust configuration.

## Trust boundaries
A token with Administration:read is required solely for preflight and is never printed.
GITHUB_TOKEN retains contents:write only in the existing manual publication job.
Record identities and dates are assertions; a repository owner can fabricate them.
No secret keys or real reviewer identities are included in fixtures.
RFC 3161 validation still requires independently approved CA/CRL policy; public TSA
network testing and third-party review are not implied by local synthetic tests.

## Acceptance
Tests must reject API outages as nonexistent versions, disabled immutability, base-event
mutation, deleted reports, wrong report digests, inconsistent per-version paper hashes,
unsafe HTML/URLs, and missing evidence. Existing 52 tests remain passing.
A software increment can be merged after CI; v1.0 is withheld until operational gates
in docs/RELEASE_READINESS.md are actually satisfied.
