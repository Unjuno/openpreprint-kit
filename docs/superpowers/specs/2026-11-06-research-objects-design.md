# Research objects and confidential record commitments — design (2026-11-06)

## Goal
A GitHub paper Release should bind the exact published paper, public research data, analysis code, documentation, and optional confidential-record commitments to one manifest and one independently verifiable RFC 3161 timestamp.

## Decisions and tradeoffs
- Keep a public-repository template; no new backend, database, or identity provider. A researcher explicitly opts in to including each public file via `research-assets.yaml`.
- Public files become one deterministic uncompressed TAR (`research-assets.tar`) plus JSON catalog (`research-assets.json`). This is simpler to verify than dozens of GitHub Release assets; it requires consumers to download an archive and limits total publication size to 100 MiB.
- Confidential files NEVER enter the repo or release. Locally generate a 256-bit secret key per file and an HMAC-SHA256 commitment with a domain separator. Commit only anonymized receipt JSON. Keep private keys and source documents outside the repository. Verification requires explicit access to the original and the corresponding key.
- Existing seven-asset releases remain supported. Research-enabled bundles add exactly two assets; timestamp files are optional until stamp generation.
- Keep integrity and timestamp distinct: SHA-256 and HMAC commitments provide content matching; a trusted RFC 3161 token on the final manifest can provide an upper existence bound under trust assumptions; none of this proves public availability, human identity, review quality or medical veracity.

## Security properties / exclusions
- Reject path traversal, absolute paths, symlinks, nested directories/special TAR entries, duplicate members, mismatched file size/digest, undeclared data, ambiguous record JSON, and attempts to overwrite earlier private receipts/keys.
- Require an explicit `public_confirmed: true` per publicly released asset, with description and license. Automated scanning cannot certify absence of personal data; users must assess consent and jurisdictional requirements before publication.
- Do not put filenames, patient identifiers, medical details, dates, source paths, or secret keys in private receipts. Record IDs are random 128-bit values. Never upload private originals or keys to GitHub Actions.
- Keep old papers/stamps unchanged; corrections create new releases/receipts.
- Explicit maximum 100 files and 100 MiB total public asset bytes, 25 MiB per file; no archive extraction by verifier.

## Data flow
1. Researcher edits metadata, `research-assets.yaml` and adds public assets under `data/`, `analysis/` or `supplements/`.
2. For a confidential file only, locally call `private_seal.py seal` with the secret/output outside the repo; one receipt is written under `evidence/commitments/<random>.json` and automatically picked up in the research package.
3. `prepare_release.py` fails closed on missing/disallowed public assets, receipts or invalid relations, then builds deterministic TAR+catalog and includes both digests in the main manifest.
4. `verify_release.py` recomputes outer hashes and traverses TAR headers *without extracting* to validate every catalog entry; `timestamp.py` signs/verifies `manifest.json` as before.
5. Optional selective verification: investigator is given the private original, matching per-record key and receipt and runs `private_seal.py verify`. Disclosing a per-record key must not reveal other records.

## Done when
- Existing unit tests stay green; new tests cover valid public data/code relationships, malicious paths and symlinks, missing files, TAR tampering, rehashed malicious TAR, deterministic builds, two distinct private commitments, data mutation, wrong key, non-leakage and timestamp-manifest binding.
- GitHub CI passes Python 3.10/3.12, and work is merged to `main`. Real clinical data are **never** used as fixtures.
