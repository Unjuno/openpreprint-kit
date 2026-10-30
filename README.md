# OpenPreprint Kit

**Open-source GitHub template for publishing one research preprint per public repository.**

OpenPreprint Kit supports GitHub-based preprints with metadata validation, version-specific Releases, citation files and offline checksum verification.

> **Evidence limitation:** This early version does NOT provide an independent cryptographic timestamp, independently verified first-publication time, author identity proof, DOI or long-term off-GitHub preservation. See [Threat model](docs/THREAT_MODEL.md).

## 1. Create a research repository

1. Click **Use this template → Create a new repository**. The owner must first enable **Settings → General → Template repository**.
2. Create a **Public** repository for one paper.
3. Edit `preprint.yaml`: paper title, authors, abstract, keywords, version, paper license.
4. Add the final PDF to `paper/paper.pdf` (or change its location in `preprint.yaml`).
5. Check before publishing:

```bash
python3 -m pip install -r requirements.txt
python3 scripts/validate.py --strict
python3 -m unittest discover -s tests -v
```

The template deliberately starts with `v0`, placeholder data and no PDF, so strict validation and publishing **fail by default**. Use an explicit public version (v1, v2 or v1.1) only when ready to publish.

## 2. Preview and verify a release bundle

```bash
python3 scripts/prepare_release.py --output dist
python3 scripts/verify_release.py dist
```

Seven assets are created:

| File | Purpose |
|---|---|
| `paper.pdf` | Byte-for-byte PDF selected in metadata |
| `preprint-metadata.json` | Scholarly metadata, version, source claim and PDF SHA-256 |
| `CITATION.cff` | Machine-readable CFF 1.2.0 citation metadata |
| `citation.bib` | BibTeX citation, no fabricated publication year |
| `manifest.json` | SHA-256 digests and byte sizes |
| `SHA256SUMS` | Conventional checksums, including manifest |
| `RELEASE_NOTES.md` | Version information, paper license and evidence notice |

The manifest is **unsigned**: checksums alone do not establish a trusted publication time, authentic authorship or who first uploaded the paper. The offline verifier needs only Python's standard library.

## 3. Publish on GitHub (manual, public disclosure)

1. In your **paper repository** enable **Settings → General → Releases → Enable release immutability** before publishing. The workflow asks you to acknowledge this setting but cannot verify the administration setting itself.
2. Open **Actions → Publish preprint release → Run workflow** on the default branch.
3. Check `acknowledge_immutable_enabled` after verifying the setting and press Run workflow.
4. After strict checks pass, the workflow creates a **draft Release**, uploads seven assets, downloads them again and compares bytes before publication.
5. Inspect the Release page, including the **Immutable** label and release attestation when enabled.

**Publication happens automatically when this manually dispatched workflow succeeds. Do not run it unless the paper is ready for public disclosure.** Failed runs can leave an unpublished draft; inspect and clean up manually before retrying. Never overwrite old public versions: increment the version instead.

## 4. Verify downloaded assets

Download all seven assets of a versioned GitHub Release into an empty directory:

```bash
python3 scripts/verify_release.py /path/to/downloaded-assets
python3 scripts/verify_release.py /path/to/downloaded-assets \
  --expected-paper-sha256 YOUR_SEPARATELY_TRUSTED_64_HEX_DIGIT_HASH
```

A SHA-256 digest obtained from a separate trusted channel permits stronger integrity checking. If GitHub issued an immutable release attestation, verify it with `gh release verify TAG` and/or `gh release verify-asset TAG paper.pdf`.

## 5. Metadata example

```yaml
schema_version: 1
title: "Example preprint"
authors:
  - given_names: "Jane"
    family_names: "Doe"
    orcid: "0000-0002-1825-0097"
  - name: "Research Group"
abstract: "A short abstract."
keywords: ["mathematics", "physics"]
version: "v1"
paper: "paper/paper.pdf"
license: "CC-BY-4.0"
```

For a person use `given_names` and `family_names`. `name` represents a team or other entity; the older one-string `name` field is retained for compatibility but **should not be used for personal names** if they can be separated.

The generated `CITATION.cff` is included as a Release asset, **not automatically written to the repository root**, so GitHub's built-in Cite this repository widget is not yet enabled.

## 6. License and technical design

Toolkit code: **MIT**. The paper and datasets have **their own** license set by the researcher (for example CC BY 4.0).

Python ≥ 3.10, PyYAML ≥ 6.0.2, GitHub Actions and GitHub CLI on the hosted Ubuntu runner. GitHub Actions checkout/setup-python dependencies are pinned to immutable commits; PyYAML is constrained to major version 6, not a hash-locked wheel.

See [Roadmap](docs/ROADMAP.md) and [Threat model](docs/THREAT_MODEL.md).
