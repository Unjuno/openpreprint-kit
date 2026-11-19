> **GitHub-only online publication/storage policy (2026-11-12):**
> The primary paper and mirrored custody snapshots are stored as immutable
> **GitHub Releases**, not Google Drive or any required second cloud vendor.
> This document remains applicable to optional **offline exports** that can be
> restored if GitHub is inaccessible. See [GitHub preservation](GITHUB_PRESERVATION.md).

# Independent multi-version custody and recurring audit

**Engineering support is implemented; real off-GitHub custody is not thereby established.**
This workflow is for a separately managed archivist/custodian who is willing to store
versioned OpenPreprint Kit preservation ZIPs. The author, GitHub, custodian and
TSA are separate trust roles. Merely moving a directory on the author's
computer is NOT independent preservation.

## Prerequisites and trust boundary

- Obtain the **actual approved published Release assets** for each version.
  Independently validate source `OWNER/PAPER`, tags and contents; do not
  presume an unapproved manuscript may be published.
- Create each `v1.opk.zip`, `v2.opk.zip` using
  [`scripts/preserve.py`](PRESERVATION_AND_WITNESS.md). The ZIPs contain the
  public paper, data, analysis and timestamp evidence, **not clinical
  originals, identifiable health data or private HMAC/Ed25519 keys**.
- Record each ZIP's `sha256sum` **over a separate trusted channel** before
  delivering it to the custodian. An archive's self-contained SHA-256 or
  a download from the same GitHub account alone is not that channel.
- Acquire a TSA trust policy, certificate CA pin and current CRL from an
  independently reviewed source. The archived CA/CRL snapshots are evidence,
  NOT automatic trust anchors.
- The custodian provisions a different access-controlled storage account or
  machine, a backup/retention policy and periodic checking outside GitHub.

## 1. Deposit exact archives (on the custodian's host)

```bash
python scripts/custody.py deposit \
  --repository OWNER/PAPER \
  --entry v1 /incoming/v1.opk.zip OUT_OF_BAND_V1_ZIP_SHA256 \
  --entry v2 /incoming/v2.opk.zip OUT_OF_BAND_V2_ZIP_SHA256 \
  --policy /custodian/trust/timestamp-policy.json \
  --out /custodian/storage/OWNER-PAPER
```

The command verifies both ZIP hashes, securely restores and verifies **all
embedded assets and RFC 3161 signed evidence**, and checks each archived
paper's source repository, tag and Git commit. It then atomically creates
`/custodian/storage/OWNER-PAPER/` with `custody.json` and both ZIPs.

**Separately record `catalog_sha256` from the JSON output** on storage controlled
outside the archive directory. It must not be copied out of `custody.json`
itself when auditing. The manifest and the archive are not trusted merely
because they are stored together. A successful deposit cannot attest that
the storage is actually independent or will remain available.

A second release or version should be accommodated by depositing a new,
complete catalog containing all previous archives in a NEW storage directory,
checking old SHA-256 values and version identities as well as the new version.
Keep the old complete catalog and its pin; do not overwrite an existing store.

## 2. Audit periodically without GitHub access

```bash
python scripts/custody.py audit \
  --repository OWNER/PAPER \
  --store /custodian/storage/OWNER-PAPER \
  --catalog-sha256 OUT_OF_BAND_CATALOG_SHA256 \
  --policy /custodian/trust/timestamp-policy.json
```

`audit` is read-only and fails if the catalog changes, any expected version is
missing, an extra file appears, an archive changes, the repo/tag/manifest is
inconsistent, or the current TSA trust/CRL check fails. A `PASS` establishes
only the specified files' integrity and time evidence **at audit time**.
The JSON result deliberately contains `offsite_custody: NOT_ATTESTED`,
`durability: NOT_PROVEN`, and `first_publication: NOT_PROVEN`.

For an operational schedule, the **independent custodian**, not the author's
GitHub Action, configures the host's job scheduler to execute the read-only
command on a documented cadence (for example, monthly). Retain the exit
code, audit JSON and logs in a *separately authenticated* append-only audit
system. On FAIL, alert the responsible archivist, suspend affirmative
verification claims and investigate missing files, compromised accounts,
expired CRLs, certificate revocation or tampering. Do not silently refresh
pins or replace original versions to make an audit pass.

## 3. Restore and disaster recovery

If GitHub or the author disappears, first acquire the **independently pinned**
catalog digest and TSA trust materials. Run the audit above; then restore
each archive with `preserve.py restore --expected-sha256 ... --policy ...`
using its digest from the now-authenticated catalog. Verify again with
`verify_evidence.py --scope existence --repository OWNER/PAPER --version v1`.
No online GitHub API is required for this local verification, although
finding fresh CRLs can require an available CA distribution service.

## Privacy and lifecycle limitations

- An HMAC of a private record is an integrity commitment, not encryption,
  patient identity proof, a guarantee of confidentiality or proof that the
  underlying medical observation was accurate. Public commitments themselves
  can carry linkage risk if identifiers or metadata are not minimized.
- There is no legal retention/deletion decision in this program. A clinical
  data controller must decide consent, access, custody, key destruction,
  retention, data-subject rights and applicable laws before using real records.
- Current CRLs verify *current* certificate status. They do not replace
  independently preserved historic revocation evidence, LTV/renewal or future
  cryptographic migration. Old timestamps may become unverifiable if trust
  material expires, an authority is revoked, or algorithms are deprecated.
- No uptime SLA, multi-site replication, WORM media guarantee, actual external
  custodian independence or third-party review is installed by this CLI.

## Acceptance before claiming G7 externally completed

Require recorded evidence from a custodian and an independent auditor:
1. An approved, actually public immutable paper Release with its complete
   asset list and externally observed download record.
2. An archive and catalog replicated to a separate organization/account,
   the pins delivered out-of-band, and the operator identified and accountable.
3. A documented backup copy and a tested restore **with GitHub inaccessible**;
   verify v1 and v2 with no loss of historical versions.
4. A periodic audit history and incident response for missing/changed files,
   stale CRLs, TSA key rollover and key-compromise scenarios.
5. Independent security/privacy review of the software and procedures.

Until these are recorded, G7 is **PARTIAL, NOT ACCEPTED**.
