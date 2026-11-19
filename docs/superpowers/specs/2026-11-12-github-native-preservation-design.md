# GitHub-native evidence preservation design — 2026-11-12

## Goal / selected approach
OpenPreprint Kit's only supported online publication/storage service is GitHub: paper/data/code release assets, immutable source Releases, evidence archives in a SECOND GitHub repository as a distinct immutable Release. No Google Drive connector or provider dependency in software. Other independent archives are an optional separate resilience gate, never silently marked achieved by two GitHub repositories.

## Non-goals / safety
Do not publish real papers, confidential health originals, private HMAC or signing keys, or create GitHub repositories automatically in this change. No hidden network in default `plan`. No overwrites, clobber, tag reuse, deletion, or force-push. Never silently downgrade external trust when TSA validation fails. No automatic v1.0 readiness claim. A GitHub-only mirror does not survive a full GitHub outage; users can export ZIPs for offline verification without any non-GitHub cloud vendor.

## Architecture
- `custody.py` remains the local, cryptographically verified archive/custody catalog primitive, including separate catalog SHA-256 pin and per-version source identity, TSA policy, CRL checks.
- `github_mirror.py plan` is offline and read-only, returns proposed deterministic tag and operations. `publish` requires `--apply`, an existing public mirror repo, immutable releases pre-enabled, `gh` authentication, new destination tag. Validates original archive store with independently pinned catalog SHA, creates a `github-mirror-receipt.json` with repo/tag/source/archive digest declarations, and stages a draft GitHub Release containing only `custody.json`, `<version>.opk.zip`, and the receipt. Exact bytes verified after draft download before promotion, then anonymous downloads and GitHub Release/asset attestations checked. On partial failure the journal remains and no rollback is asserted. The mirror Release must not be in the source repo.
- `verify` accepts explicit source and mirror repo, exact tag, out-of-band catalog and receipt SHA-256, separately selected TSA trust policy and **new** output directory. Anonymous GitHub asset downloads are host-constrained HTTPS with size bounds and no credentials, mirror immutable metadata checked, bytes compared to pins, `custody.audit()` invokes original RFC 3161 checks, then atomically installs retrieved archive store. The verifier never accepts a digest solely from the mirrored receipt.
- Repo owner can choose a separately controlled GitHub organization/account for mirror. Under same owner, all checks may pass, but account/host independence is NOT_PROVEN.
- Documentation replaces Google Drive as online delivery recommendation; prior historical test remains explicitly described as legacy experiment, not runtime dependency.

## Acceptance
TDD RED first: missing `github_mirror` plus tests for offline plan, wrong pins, old tags, missing/changed assets, correct success with real synthetic OpenSSL-signed v1/v2 ZIPs, link checks and no unsafe writes. Then GREEN and full `python -m unittest discover -s tests -v` in supported CI. Exclude secrets and provider credentials from reports. For operational success require real GitHub owner-authenticated mirror release (not mocked); for v1.0 remain blocked on actual independent custodial management and long-term trust renewal.
