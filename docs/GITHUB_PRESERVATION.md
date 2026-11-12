# GitHub-only publication and verifiable evidence mirrors

**The supported online publication and storage infrastructure for OpenPreprint Kit is GitHub.** Google Drive is neither required nor a supported runtime integration. This page supersedes the old ad hoc cloud-storage experiment described historically in `STATUS_2026-11-12.md`.

## Architecture and trust model

1. **Paper repository (`OWNER/PAPER`):** GitHub source code and **immutable Releases** per version (`v1`, `v2`, ...). Each Release contains PDF, public research data, analysis code, manifest, RFC 3161 request/response, checksums and citation information. Never publish raw patient/health records or HMAC/Ed25519 private keys.
2. **Mirror repository (`ARCHIVER/EVIDENCE`):** a *different* public GitHub repository whose immutable Releases contain exact, verified preservation ZIPs for one or more versions, `custody.json`, and an inventory receipt. Every snapshot gets a new tag derived from the pinned custody catalog; existing tags/releases are never modified.
3. **Verifier:** anonymously downloads mirrored assets over restricted HTTPS, checks **two hashes obtained out of band** (`catalog_sha256` and `receipt_sha256`), validates original paper/version/commit and RFC 3161 with an independently selected TSA trust policy, and restores archives to a new directory. `verify` **does not require `gh` or a login**. With `--require-source-release`, it also checks that original GitHub Releases remain public and immutable, and every asset byte agrees with the pinned mirror. This validates HTTPS bytes and GitHub API metadata, **not** Sigstore attestations.
4. **Owner/publisher:** performs opt-in mirror publication with `gh` credentials. The default `plan` operation has no filesystem or network effects.

A second GitHub repository **is not a second cloud provider or an independently verified custodian**. A different GitHub organization/account creates an additional credential domain only when it actually has separately managed credentials and custodians. All GitHub Releases may become inaccessible during a platform-wide GitHub outage. A separately retained ZIP and digest can be validated offline; this does not require Drive or another cloud service, but someone must actually store that offline copy. No ten-year availability claim is made without operational evidence.

[GitHub documentation: immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases) explains that assets and tag are protected **after publication**; release title/body are mutable, so they are not used as trusted metadata. [GitHub CLI release create](https://cli.github.com/manual/gh_release_create) drafts, uploads and publishes in multiple network operations, not one atomic transaction.

## 1. Prepare the GitHub repositories (owner action)

With an authenticated, current `gh` CLI and reviewed policy on the owner's own host:

```bash
gh auth status
# One-time creation by the archive owner (choose a DIFFERENT operator if available)
gh repo create ARCHIVER/EVIDENCE --public --description 'Immutable OpenPreprint evidence mirror'
python scripts/owner_setup.py --repository ARCHIVER/EVIDENCE --apply
```

**Do not mark the evidence mirror as a template.** Enable/confirm immutable Releases **before** its first release, then configure branch rules and required human review as applicable. The mirror account must not be an untrusted PR automation account. The archive owner can inspect the exact operations; never paste credentials, private signing keys or clinical originals into chat, Issues or workflow logs.

## 2. Prepare a verified custody snapshot from the paper's released versions

First download and verify the **actually public** source Release assets and build `v1.opk.zip`, `v2.opk.zip` with `preserve.py pack` under an independently pinned RFC 3161 TSA policy. Optionally, the synthetic publication acceptance pilot outputs these archives per version. Record their SHA-256 fingerprints through an operator-controlled separate channel.

```bash
python scripts/custody.py deposit \
  --repository OWNER/PAPER \
  --entry v1 /input/v1.opk.zip VERIFIED_SHA256_OF_V1_ZIP \
  --entry v2 /input/v2.opk.zip VERIFIED_SHA256_OF_V2_ZIP \
  --policy /trusted/timestamp-policy.json \
  --out /safe/new-custody-snapshot
```

This creates `custody.json` and the exact versioned archives. Capture `catalog_sha256` from the output **in an independent trusted record**. The catalog cannot establish its own authenticity.

## 3. Publish the entire custody snapshot as one immutable GitHub Release

`plan` is offline and makes no changes:

```bash
python scripts/github_mirror.py plan \
  --source OWNER/PAPER --mirror ARCHIVER/EVIDENCE \
  --catalog-sha256 VERIFIED_CATALOG_SHA256
```

On an owner-authorized workstation (this **publishes files to a public GitHub repository**):

```bash
python scripts/github_mirror.py publish --apply \
  --source OWNER/PAPER --mirror ARCHIVER/EVIDENCE \
  --store /safe/new-custody-snapshot \
  --catalog-sha256 VERIFIED_CATALOG_SHA256 \
  --policy /trusted/timestamp-policy.json \
  --out /safe/new-mirror-journal
```

The publisher refuses an existing release or tag, missing admin permission, disabled immutability, a wrong custody hash, invalid TSA/CRL or unsafe file. It creates a **draft** containing only allowlisted evidence, downloads all assets and checks bytes, rechecks immutable settings, publishes, confirms the immutable release/asset list, calls `gh release verify` and `gh release verify-asset` for attestation checks, and **anonymously** re-downloads the public Release and fully audits it. If a post-publication check fails, a `FAIL` journal remains; the publication may still be public and is *not* falsely described as rolled back. Investigate and use a **new snapshot/tag**, never clobber.

Store both `tag` and `receipt_sha256` from `mirror-report.json` **separately from the mirror repository**, along with the previously pinned catalog hash and your own TSA trust-policy selection. Do not obtain trust roots or expected hashes exclusively from the mirrored files you are checking.

## 4. Independently verify and recover from GitHub without login

No GitHub token or `gh` CLI is required for this read-only operation:

```bash
python scripts/github_mirror.py verify \
  --source OWNER/PAPER --mirror ARCHIVER/EVIDENCE \
  --tag opk-custody-YOUR_VERIFIED_TAG \
  --catalog-sha256 OUT_OF_BAND_CATALOG_SHA256 \
  --receipt-sha256 OUT_OF_BAND_RECEIPT_SHA256 \
  --policy /trusted/timestamp-policy.json \
  --out /safe/new-downloaded-store \
  --require-source-release

python scripts/custody.py audit \
  --repository OWNER/PAPER \
  --store /safe/new-downloaded-store \
  --catalog-sha256 OUT_OF_BAND_CATALOG_SHA256 \
  --policy /trusted/timestamp-policy.json
```

**Verification scope:** Without `--require-source-release`, output reports `source_publication=NOT_CHECKED`; this permits a mirror-only recovery if the original repository is unavailable. With this flag, `source_publication=PUBLIC_IMMUTABLE_ASSETS_MATCH` requires all live source Releases and every original asset to match the mirrored bytes. Both modes report `github_attestation=NOT_VERIFIED_BY_ANONYMOUS_MODE`; the authenticated publisher separately runs `gh release verify`/`gh release verify-asset`. For G2 acceptance, an independent verifier also needs genuine GitHub attestation evidence and an externally approved TSA policy. The anonymous check does **not** establish independent custody or first-publication time.

For **offline disaster recovery after an actual export**, take the verified store and its out-of-band hash to a machine without GitHub access and invoke `custody.py audit` followed by `preserve.py restore` for each archive. If the only surviving copy was on GitHub and GitHub itself is unavailable, recovery is not possible; don't call that case `PASS`.

## Security, privacy and acceptance boundaries

- This is **GitHub-to-GitHub replication**, not independent long-term escrow, human academic review or clinical compliance. Public mirrors are forbidden for identifiable health data, HMAC secrets and private originals. Only existing validated public archive members are permitted.
- Changing the paper invalidates SHA-256, and the timestamp signature binds the original manifest. An anonymous verifier cannot infer who authored the study or that a healthcare observation is accurate.
- TSA trust root/CRL and expected SHA-256 values must remain out of band. Unknown TSA accuracy is not zero. Certificate expiry, revocation, renewal and multi-year continuity are separate obligations.
- A green unit test in which GitHub traffic is mocked is **not** evidence that a real mirror Release was published. Closing v1.0 G1/G2/G4/G5/G7 requires dated owner and separately administered operator evidence, not the script's existence.

## Forward timestamp re-attestation (separate immutable Release)

Existing source and mirror Release assets are never modified to add newer time evidence. When current original TSA validation still passes, use [forward renewal](FORWARD_RENEWAL.md) to produce a separately pinned ZIP of new linked RFC 3161 attestations. Publish it under a **new** immutable GitHub tag and independently re-download/restore it. This is an additional timestamp, **not** a completed RFC 4998 Evidence Record or a substitute for independently managed custody.
