# 第1論文の最終発行 / First-paper final publication

## Initial owner setup (not performed by a remote desktop)

The toolkit must be a public Template repository. The owner enables it through GitHub settings and confirms the change. New paper repositories are generated with `--template`, and `template_repository.full_name` is checked before any scientific input is committed. Existing repositories are never reused or overwritten. The publisher does not modify the toolkit's administration settings.

On Linux, with Python 3.10+ and venv, GitHub CLI supporting Release verification, curl, OpenSSL 3 and sha256sum, authenticate using the owner's chosen GitHub mechanism. No passwords or tokens are sent to chat.

```bash
gh auth login --hostname github.com
bash scripts/publish_first_paper.sh --plan
bash scripts/publish_first_paper.sh --publish
```

`--plan` is offline and side-effect free. `--publish` creates one NEW **Unjuno/openpreprint-kit-paper**, from the public template, enables/reads back immutability on that NEW repository, uploads the approved scientific inputs and publishes v1 after staging checks. It does NOT imply general-production acceptance or independent review.

## Stable approved input

The exact PDF from run **43279522755** is now version controlled at `manuscripts/openpreprint-kit/approved-v1/paper.pdf`. Its SHA-256 is:

`0860b735379fb1b9b223f5d535442dae8421f456d7ae1c6bf6ce8d3141a1b07c`

The launcher checks this fingerprint BEFORE authentication and package installation. It no longer downloads a 14-day Actions artifact. A preview, re-typeset document, or same-named file with different bytes is rejected. The original prepublication proof is retained under `evidence/first-paper/approved-v1/`; it is NOT relabeled as a published proof. Source-bound publication always requires a fresh timestamp.

## Failure and subsequent checks

A verified `first-paper.opk.zip` and its fingerprint are saved **before** public promotion. An unavailable attestation after publication does not destroy recovery evidence. Do not rerun creation against an existing repo or delete immutable history. Use read-only recovery with a NEW output directory instead:

```bash
python scripts/first_paper_publish.py --verify-existing \
  --repository Unjuno/openpreprint-kit-paper \
  --archive /retained/first-paper.opk.zip \
  --archive-sha256 INDEPENDENTLY_RETAINED_ZIP_SHA256 \
  --policy /trusted/current-timestamp-policy.json \
  --out /new/read-only-verification
```

This verifies archived and anonymously fetched bytes, source tag/commit, GitHub release and asset attestations, and RFC 3161 under independently selected current trust. It does not publish, reissue a timestamp, modify settings, or overwrite previous reports. It is suitable for an operator's periodic read-only check. Scheduling it does not establish observer independence or guarantee availability; certificate/CRL changes and high-severity alerts still require responsible review.

Detailed boundaries: [FIRST_PAPER_PUBLICATION.md](FIRST_PAPER_PUBLICATION.md). Author Unjuno / CC BY 4.0 / v1 remain approved. A successful local/mock test is never described as a real public Release.
