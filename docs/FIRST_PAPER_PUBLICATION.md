# Publish the approved first paper (owner execution)

## Status after actual owner publication (2026-11-14)

**Already published:** [Unjuno/openpreprint-kit-paper v1](https://github.com/Unjuno/openpreprint-kit-paper/releases/tag/v1), GitHub Release ID 444659219. The REST API returns `immutable=true`, `draft=false`, 11 assets, and the approved PDF SHA-256. The [owner's recorded checks](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-6863092530) include fresh TSA evidence, Release attestation, anonymous re-download and offline restore. The initial one-shot Windows execution failed at `SOURCE_COMMITTED` because the venv `cffconvert` script was unavailable on PATH; a separately approved same-code-path continuation completed the publication while preserving the original FAIL journal. This is not an uninterrupted launcher success or independent human audit.

**Do not rerun `--publish` against this existing repository, overwrite the immutable v1, delete the failed report, or relabel the old prepublication proof.** The remaining instructions describe the **historical single-use procedure**; for current verification use `--verify-existing` with the independently pinned preserved ZIP digest and a fresh trust policy, or [the read-only quickstart](FIRST_PAPER_QUICKSTART.md). The toolkit v1.0.0 still requires G0–G7 acceptance.

The author display name **Unjuno**, manuscript **CC-BY-4.0** and **v1** are already approved. Do not request them again. This command publishes the real first manuscript, not the synthetic pilot. It requires an owner-authenticated GitHub CLI because a code-writing GitHub connector does not supply repository-creation or Administration authority.

## Scope and preconditions

The intended destination is a **new** `Unjuno/openpreprint-kit-paper`. The toolkit repository remains unchanged. The destination must not already exist. The public toolkit must already be enabled as a Template repository; creation uses that template and verifies the returned template origin. No attempt is made to gain access beyond the owner's native `gh` permissions. Use GitHub CLI supporting `gh release verify` and `gh release verify-asset`, Python 3.10+, OpenSSL 3 and the kit's locked dependencies.

From a clone of this toolkit:

```bash
python -m pip install --require-hashes -r requirements-build.lock
python -m pip install --require-hashes --no-build-isolation -r requirements.lock
gh auth login --hostname github.com
python scripts/first_paper_publish.py
```

The last line prints a plan only; it neither connects to GitHub nor creates output. Native authentication stays on the owner's computer. Never paste a password, token, HMAC key, or clinical original into chat/Issues. Actual repository creation, Administration and Contents authority is required for the publish step. Use the narrowest credential supported for creating the new repository; do not grant unrelated organization access.

## Fixed approved input

Use the exact approved PDF retained from **run 43279522755**, commit `7b1fc1d34ede8aebeb01bd869350ef2140be528e`:

`0860b735379fb1b9b223f5d535442dae8421f456d7ae1c6bf6ce8d3141a1b07c`

This is a **PDF** SHA-256, not the ZIP digest. The author approved the manuscript metadata, not a cryptographic identity attestation. Retain the PDF and digest separately; the Actions download itself is temporary. The exact approved PDF is now version controlled at `manuscripts/openpreprint-kit/approved-v1/paper.pdf`; the launcher does not require the expiring Actions artifact. The original proof is retained at `evidence/first-paper/approved-v1/prepublication.opk.zip`. The old bundle has `source_claim: null`; it must not be silently relabeled as a publication from the new repository. This publisher retains the PDF bytes but builds a new source-bound manifest and requests a **new** TSA token.

Provide `/trusted/timestamp-policy.json` and its pinned CA/current signed CRL through an independently selected trust process, using the existing `docs/TIMESTAMPS.md` procedure. Never automatically trust the CA found inside a downloaded paper archive. The already-tested FreeTSA CA pin is `2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438`; this pin alone does not establish current revocation status or provider reliability. Do not replace a mismatched pin merely to make the run pass.

## Publish (real public side effects)

```bash
python scripts/first_paper_publish.py \
  --repository Unjuno/openpreprint-kit-paper \
  --paper-pdf /path/to/first-paper-v1.pdf \
  --paper-sha256 0860b735379fb1b9b223f5d535442dae8421f456d7ae1c6bf6ce8d3141a1b07c \
  --policy /trusted/timestamp-policy.json \
  --out ../first-paper-publication-evidence \
  --publish
```

It validates the PDF pin and all approved source inputs before any public mutation; creates one new public repository from the verified template (including its public toolkit contents); enables and reads back immutability; commits only the allowlisted paper, metadata, seven research inputs and a paper README; rebuilds the manifest with the destination repository/commit; obtains a fresh RFC3161 proof; creates a draft and compares downloaded bytes; re-checks immutability; saves a verified preservation archive and fingerprint before promotion; publishes; verifies GitHub Release/asset attestations; anonymously downloads all eleven assets; restores a preservation ZIP and verifies the original bytes. It does not upload patient records, signing keys, trust credentials, or the entire local workspace. It does not change existing repository permissions or weaken branch protection.

The report is `../first-paper-publication-evidence/publication-report.json`. Only `status=PASS` and `state=VERIFIED_PUBLIC_PREPRINT` mean this run completed publication **and** its post-publication checks. These do not mean production v1.0, independent witness, independent security audit, authorship verification, initial publication time or peer review are proven.

## Partial failures

Publication is not an atomic distributed transaction. A failure may leave a newly created public repository, a draft or an already public Release. The report retains the last stage (`REPOSITORY_CREATION_REQUESTED`, `DRAFT_CREATED`, `PROMOTION_REQUESTED`, `PUBLIC_VERIFICATION_PENDING`). It never claims rollback. Never delete a published version or bypass immutability to retry. Inspect the recorded state and GitHub before further actions. For an already-public v1, independently repeat `gh release verify v1 --repo Unjuno/openpreprint-kit-paper`, verify all downloaded assets and run `verify_evidence.py --scope existence` with externally selected policy/repository/version. An attestation that is temporarily unavailable is not a success.

## Evidence status

The supplied tests execute real paper-input packaging and ephemeral-TSA signature checks, while GitHub HTTP/CLI effects are simulated. They are not proof of an actual external publication. The current chat connection has no new-repository or admin write action. An owner-side run is necessary; the kit does not obtain or impersonate an owner credential. Separate witness, mirror custody and human review remain separate acceptance gates.

## Read-only recovery after partial publication

The pre-promotion archive is the recovery input. `--verify-existing` requires its independently retained digest, expected repository and a separately selected current TSA policy. It performs no POST/PUT/PATCH/DELETE, no timestamp issuance and no release creation. Each invocation uses a new output directory and retains its own PASS/FAIL report. Duplicate asset names, changed bytes, wrong tag target, private/absent/non-immutable Releases and unavailable attestations fail closed. A later successful read-only check does not rewrite the earlier failure report.

See the recovery command in [FIRST_PAPER_QUICKSTART.md](FIRST_PAPER_QUICKSTART.md). A fixture-only GitHub transport test is not a live public acceptance. Authenticated CLI attestation checks and anonymous downloads are distinct; both must succeed.

## Public Git source snapshot verification (2026-11-13)

A release tag pointing at the declared commit does not establish that the
**paper, data and analysis code at that commit** equal the published release.
The first-paper publisher now fetches these source files anonymously from
`raw.githubusercontent.com` at the 40-character source commit, separately from
Release-asset downloads. It compares their exact SHA-256 and byte lengths
against `paper.pdf` and each regular member of the verified, declared
`research-assets.tar`. The check runs **before the draft is promoted** and again
when the public Release is verified or read-only recovery is performed.

An absent, changed, oversized, redirected or inaccessible source file fails
closed. A transient CDN propagation failure must not be overridden by disabling
source verification. Inspect the saved journal and the GitHub repository; never
replace an already published immutable Release to repair provenance. Tests mock
GitHub transport and exercise real paper/research archive parsing; this check
cannot establish server independence, human authorship or scientific validity.
The verifier uses a bounded anonymous HTTPS connection with ambient proxies
suppressed and permits no redirects.
