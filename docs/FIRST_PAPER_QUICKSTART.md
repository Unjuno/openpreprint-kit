# 第1論文の最終発行 / First-paper final publication

## Cross-platform owner launcher

The approved first paper is published by the **same Python program** on Windows, macOS, and Linux. The former Bash launcher is retained for existing Linux users, but is no longer the recommended entry point. No OS-specific publication/verification logic is added; the portable launcher invokes the existing fail-closed scripts/first_paper_publish.py.

**Prerequisites:** CPython 3.10+ (Python 3.12 is the reference configuration), OpenSSL **3** executable on PATH (not LibreSSL), GitHub CLI gh with release verify and verify-asset support, and an owner-authenticated GitHub account authorized to create a new public repository and enable immutable releases. Installed tools and the GitHub authentication state are checked before installing packages or publishing. Git is not required by the Python launcher. Never paste tokens into chat.

The existing public toolkit must have **Template repository** enabled. The publication code itself creates **one new** template-derived Unjuno/openpreprint-kit-paper and checks the template origin. It refuses to reuse or overwrite an existing destination. The source repository's rules and contents are not modified by the publisher.

Run from a downloaded or cloned toolkit source snapshot.

**macOS / Linux terminal:**

    python3 scripts/publish_first_paper.py --plan
    python3 scripts/publish_first_paper.py --check-pdf
    python3 scripts/publish_first_paper.py --preflight
    python3 scripts/publish_first_paper.py --publish

On macOS, install OpenSSL 3 and ensure its executable directory precedes the system LibreSSL on PATH. For example, with Homebrew's openssl@3, run:

    export PATH="$(brew --prefix openssl@3)/bin:$PATH"

**Windows PowerShell (Python 3.12 installed):**

    py -3.12 scripts/publish_first_paper.py --plan
    py -3.12 scripts/publish_first_paper.py --check-pdf
    py -3.12 scripts/publish_first_paper.py --preflight
    py -3.12 scripts/publish_first_paper.py --publish

On Windows, install gh and OpenSSL 3 using trusted distributions and ensure both executables are on PATH. The launcher chooses the platform-specific virtual-environment interpreter without Bash, curl or sha256sum.

**Smartphone / browser:** There is **no native iOS/Android publisher and no one-tap browser publication workflow**. Where GitHub Codespaces is available to the repository owner, a browser-based Codespace provides a Linux terminal; the owner can use the same Python launcher there after checking available gh authentication and OpenSSL 3. This is a cloud-computer execution path, not a claim of an independently secured mobile app, and Codespaces availability/billing may differ. Never embed a broad-scope credential into a public workflow just to obtain a mobile button.

All modes except **explicit --publish** are non-publishing. --plan is fully offline and creates no files. --check-pdf checks only the approved byte fingerprint, offline. --preflight checks tooling and read-only GitHub authentication/template state; it does not create repositories. --publish installs hash-locked Python dependencies into a new temporary venv outside the toolkit, downloads the pinned FreeTSA CA and current signed CRL using TLS and no redirects, and invokes the same existing public publication/verification implementation. If the chosen CA has changed or the CRL cannot be verified, the process must stop; do not weaken validation.

**Portability claim:** GitHub Actions' read-only portable-first-paper.yml covers Python launcher plan, approved-PDF digest and regression tests on Linux, macOS, and Windows. This is a **smoke test**, not evidence of a real platform-specific publication. Actual GitHub release creation, an independently chosen TSA policy, attestation and anonymous restore require separate end-to-end acceptance.

## Stable approved input and evidence

The exact PDF from run **43279522755** is version controlled at manuscripts/openpreprint-kit/approved-v1/paper.pdf. Its SHA-256 is:

    0860b735379fb1b9b223f5d535442dae8421f456d7ae1c6bf6ce8d3141a1b07c

The launcher checks this fingerprint **before GitHub authentication**. It never replaces the approved PDF with a re-typeset one. The original prepublication proof under evidence/first-paper/approved-v1/ has source_claim: null and cannot be labeled as proof of the new repository's public release. Publication creates a **new** source-bound manifest and obtains a **new** RFC 3161 token.

The publication output is retained under a new directory within the owner's home/OpenPreprintKitEvidence, not the OS temporary cache. The printed directory contains publication/publication-report.json, the verified preservation ZIP and the digest if the prepublication stage succeeds. Copy these public evidence artifacts and their fingerprint to independently managed durable custody; a home folder alone is not permanent preservation. A result is successful only when status=PASS and state=VERIFIED_PUBLIC_PREPRINT.

## Partial failure and read-only recovery

The verified first-paper.opk.zip and its SHA-256 are saved before making the draft public. A failed attestation or a network outage after promotion must not be called a rollback. **Never rerun --publish against an existing repository, delete a public version, or overwrite an evidence report.**

For an existing public version, use the read-only recovery path with a newly chosen output directory and the *independently retained* ZIP SHA-256:

    python scripts/first_paper_publish.py --verify-existing \
      --repository Unjuno/openpreprint-kit-paper \
      --archive /retained/first-paper.opk.zip \
      --archive-sha256 INDEPENDENTLY_RETAINED_ZIP_SHA256 \
      --policy /trusted/current-timestamp-policy.json \
      --out /new/read-only-verification

On Windows, put the command on one line or use PowerShell's line-continuation syntax; Unix backslashes above are not Windows continuation marks. This checks the exact archive and anonymous GitHub release/source bytes, immutable status, attestations and fresh TSA trust, without any public write.

Detailed boundaries: [FIRST_PAPER_PUBLICATION.md](FIRST_PAPER_PUBLICATION.md). Author Unjuno / CC BY 4.0 / v1 remain approved. Publication alone does not prove independent witness, human peer review or product v1.0 readiness.
