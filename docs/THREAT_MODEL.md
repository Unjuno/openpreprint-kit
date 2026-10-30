# Security and evidence model

## Claims and boundaries

| Claim | Evidence available now | Not established |
|---|---|---|
| Asset bytes match their recorded checksums | Recomputed SHA-256 and length | Manifest authenticity without a trusted external digest |
| PDF matches a separately pinned fingerprint | `verify_release.py --expected-paper-sha256` | Creation time and authorship |
| Published assets resist changes | GitHub **Immutable Releases**, when enabled **before publishing** | Independent time evidence |
| Paper existed at a specific absolute time | **Not implemented** | Would require trusted third-party time evidence |
| Paper was publicly accessible at a specific time | **Not implemented** | Requires a trusted independent observer and signed observation |
| A person actually authored the paper | Metadata assertions only | Human identity, ORCID ownership and intellectual-property rights |

Git Author Date and Committer Date are user-configurable. A SHA-256 manifest by itself is neither a digital signature nor a cryptographically proven timestamp. The metadata field `source_claim` is not independently authenticated.

## Threats and protections

1. **Accidental publication:** The strict validator rejects placeholders, missing PDFs, draft version `v0` and malformed author names. The publisher is manual-only. Do not run it before you intend disclosure.
2. **YAML-based injection:** Metadata is read with `yaml.safe_load`, never evaluated as shell or Python code. Version tags follow a narrow numeric format. Release filenames are fixed in the workflow.
3. **Path traversal and symlinks:** The PDF resolves within the repository. Verification rejects symlink assets, missing files and unexpected files.
4. **Alteration while staging:** The publisher downloads seven draft assets and compares their bytes with the locally generated bundle before publication.
5. **Alteration after publication:** GitHub's immutable release feature must be enabled by the paper repository owner. The workflow receives a user acknowledgment, **not independent verification of GitHub's administration setting**. GitHub is still a trust dependency.
6. **Software supply chain:** Checkout and Python setup Actions are SHA-pinned. PyYAML is constrained by a major version range but its distribution hash is not pinned.
7. **Potentially malicious PDFs:** The current validator checks file presence, minimum length and the PDF signature, but **not full PDF parsing, script sanitization or scientific validity**.

## Verification procedure

1. Download the exact seven assets from the desired release.
2. Run `python3 scripts/verify_release.py /path/to/assets`; pass a separately trusted paper digest using `--expected-paper-sha256` when available.
3. For a GitHub immutable release use `gh release verify TAG` and/or `gh release verify-asset TAG paper.pdf` to assess the GitHub provenance attestation.
4. Do **not** infer an independently proven absolute creation time, public access time or author identity from these checks.

## Research directions

- **Cryptography:** add an RFC 3161 timestamp for a content digest, validate TSA certificates, revocation status and time bounds; the presence of a token alone is insufficient.
- **Scholarly publishing:** maintain an unambiguous public version history and citation metadata for each paper.
- **Distributed systems and archival science:** use an independent observer that retrieves the public URL, records the exact bytes and produces independently signed observations; preserve copies outside GitHub.

A third-party timestamp created before a paper is publicly released proves **prior existence at most**, never first public availability by itself.
