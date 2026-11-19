# Independent Custodian Audit — Design (2026-11-08)

## Intent and scope
A separately operated archive custodian needs to ingest exact, versioned OpenPreprint evidence ZIPs and prove, on demand, that none went missing or changed and that their underlying RFC 3161 signatures still validate under an independently configured trust policy. This closes an *engineering* gap in G7; it does not turn local storage into independent custody, a long-term availability SLA, or proof of first publication.

## Alternatives considered
1. **Hash-only archive directory:** simple, but cannot distinguish a forged manifest or invalid timestamp. Rejected.
2. **New centralized storage service:** adds credentials, infrastructure and an implicit trust authority. Rejected for initial open-source toolkit.
3. **Offline custodian CLI (chosen):** an explicitly named set of versioned archives is copied to an independently managed storage location only after checking out-of-band archive hashes, source identity and RFC 3161 cryptographic validity. Repeated audits require an independently retained catalog hash, a separately selected CA/CRL trust policy and the expected repository identity.

## Interface
- `python scripts/custody.py deposit --repository OWNER/PAPER --entry v1 /in/v1.opk.zip HEX [--entry v2 /in/v2.opk.zip HEX] --out /custodian/archive --policy /trusted/policy.json`
- `python scripts/custody.py audit --repository OWNER/PAPER --store /custodian/archive --catalog-sha256 HEX --policy /trusted/policy.json`
- Output contains `custody.json`, `v1.opk.zip`, `v2.opk.zip`. No input keys or actual patient data are accepted.
- `deposit` emits the catalog hash for separate custody; `audit` never accepts a catalog hash from the catalog itself. It fails closed on any missing, extra or changed archive, any changed catalog, symlinks, wrong repository/version, invalid timestamp, expired CRL or policy failure.
- `deposit` is atomic on one filesystem and never overwrites an existing output. `audit` is read-only. Both return bounded JSON on success and nonzero exit status on failure.

## Trust boundary
The catalog hash, TSA policy and custodian operations must be supplied via channels controlled outside GitHub and outside the authors. A successfully verified catalog proves only integrity *at audit time* and only under that externally supplied trust. Persistent storage requires the actual custodian's retention policy, backup, availability and periodic audit operations. Independent clock assurance, historical certificate revocation evidence, TSA renewal and witness identity remain separate production requirements.

## Quality and security constraints
Python 3.10+, OpenSSL 3, pinned existing dependencies; use existing `preserve.restore()` and `assert_source_identity()` rather than new cryptography. Reject unsafe ZIP content at restore and do not make copied files executable. Require strict version identifiers, bounded catalog and archive size, unique versions, and refuse symlink targets. Test with a real ephemeral OpenSSL TSA signature rather than only mocks. Keep CI publishing read-only unless human manually triggers publication.
