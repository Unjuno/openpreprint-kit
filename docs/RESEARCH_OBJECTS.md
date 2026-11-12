# Research objects, public data, code, and confidential records

## Scope

OpenPreprint Kit now optionally binds **a paper, public datasets, analysis
scripts and supplementary protocols** in the same Release manifest. The same
RFC 3161 timestamp on `manifest.json` also binds the research archive and
private-record commitments when present. Previously released seven-file bundles
remain readable. This does **not** certify scientific reproducibility or
independently establish public-access time.

## Public research data — explicit opt-in

1. Place files under `data/`, `analysis/`, or `supplements/`.
2. List **every** public file in `research-assets.yaml`, with its role,
   description, license and `public_confirmed: true` after checking privacy,
   lawful authority and applicable consent.
3. Optionally describe relations such as an analysis script `analyzes` a dataset.
4. Run `python scripts/research_package.py --check`. Missing, undeclared,
   symlinked, unsafe, oversized or non-consented files stop publication.
5. Complete the standard paper release workflow, including a trusted external
   TSA policy and GitHub release immutability.

```yaml
schema_version: 1
public_assets:
  - path: data/synthetic.csv
    role: dataset
    description: "Synthetic data with no individual participants"
    license: CC0-1.0
    public_confirmed: true
  - path: analysis/reproduce.py
    role: analysis_code
    description: "Script used to analyze the published synthetic data"
    license: MIT
    public_confirmed: true
relations:
  - source: analysis/reproduce.py
    target: data/synthetic.csv
    kind: analyzes
```

Roles: `dataset` under `data/`, `analysis_code` under `analysis/`, and
`supplementary`/`protocol` under `supplements/`. Relation kinds:
`analyzes`, `derived_from`, `documents`, `produced_by`. The relations are
**author claims**, not a verified computation or causal proof.

Hard caps: maximum 100 files, 25 MiB per individual public file and 100 MiB
total in a deterministic `research-assets.tar`. Each byte sequence is named,
licensed and hashed in `research-assets.json`. The Release's main
`manifest.json` then hashes both files and the paper, and the timestamp
covers that manifest. Offline verification reads the TAR **without extracting
or executing contents**; an extra file, symlink or mismatched digest fails.

## Confidential and health/medical records

**Do not put a real patient record into the public GitHub repository.**
Hashes of predictable medical records can enable dictionary attacks if
published directly. Use per-record 256-bit HMAC-SHA256 keys instead, with
explicit domain separation. This tool creates only a non-identifying public
commitment receipt; the original and its key remain in your secure storage.

Example (commands run locally, **not on GitHub Actions**):

```bash
# The input and key must both live OUTSIDE your public Git repo.
python scripts/private_seal.py seal /secure/records/synthetic-example.pdf \
  --key-output /secure/keys/synthetic-example.bin

# Check the resulting evidence/commitments/<random-id>.json into the repo.
# Once the preprint is released, the receipt is included in the signed archive.

# Selective private verification: the verifier is intentionally given the
# original, specific key, and publicly released receipt.
python scripts/private_seal.py verify /secure/records/synthetic-example.pdf \
  --key /secure/keys/synthetic-example.bin \
  --receipt evidence/commitments/<random-id>.json
```

**The receipts are NOT encrypted records**. They disclose a random identifier
and cryptographic commitment, but not the record body, patient name, original
filename or private key. Each file uses a distinct random key. The person who
verifies the receipt needs the **original and its key**, supplied over a secure
channel with appropriate authorization. Never ask the verifier to paste records
or secrets into a public Issue or chat.

A HMAC with undisclosed key cannot be independently evaluated from public
information alone; the public timestamp on the receipt prevents a matching
commitment from being silently swapped *if the timestamp itself is verified*.
The HMAC does not prevent erasure, deletion of GitHub repos, key theft,
substitution by a fully privileged actor before timestamping, medical fraud,
false clinical claims, or backdating by a compromised TSA. A verifier must
also check GitHub/third-party archives for omission and verify the RFC 3161
proof using an **independently selected trust policy**.

## Offline verification

```bash
python scripts/verify_release.py /path/to/downloaded-release
python scripts/timestamp.py verify /path/to/downloaded-release \
  --policy /path/to/independently-chosen-timestamp-policy.json
```

`verify_release.py` checks the outer SHA-256 hashes **and** all inner TAR
members, bytes, paths, descriptions, licenses and private receipt schema.
`timestamp.py verify` independently assesses the RFC 3161 signature, nonce,
policy, certificate chain and current revocation status. Neither proves a
clinical event happened or supplies long-term trusted revocation evidence.

## Operational requirements

- Document the storage/retention/access-control rules for medical originals and
  keys outside GitHub, with user consent and applicable legal review.
- Mirror the verified research bundle in a separate immutable GitHub Release with a separately retained SHA-256 pin; for a GitHub-wide outage, retain an authenticated offline export that can be restored without GitHub. No Drive backend is required.
- Preserve earlier receipts and Release assets; corrections must be appended
  as new receipts and new paper versions, not destructive edits.
- Before claiming independent publication-time proof, deploy a **separate
  observer** that fetches the public URL and signs its observation.
