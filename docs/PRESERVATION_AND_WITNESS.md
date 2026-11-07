# Portable preservation, real TSA acceptance and independent public observer

## What is cryptographically verified

For a published Release, OPK binds the exact PDF, public research data,
analysis scripts, citation metadata, and anonymous confidential-record
commitment receipts to one manifest. The RFC 3161 response is over the SHA-256
of that manifest. The verifier checks signed policy, CMS signature, nonce,
message imprint, CA chain, current full-chain CRLs, certificate validity and
integrity of each bundled asset. The TSA time has **unknown precision when its
signed `accuracy` field is absent**.

This does **not** assert who authored the files, that scientific claims are
correct, that the file was generally accessible at that time, or that the TSA
will remain trusted in 10 years. The historical CRL/trust material must be
retained, renewed and audited by an independent custodian.

## Portable backup and restoration

After independently obtaining all release assets and independently selecting
an appropriate CA/CRL trust policy, verify and create a deterministic archive:

```bash
python scripts/verify_release.py downloaded-release
python scripts/timestamp.py verify downloaded-release --policy /trusted/timestamp-policy.json
python scripts/preserve.py pack downloaded-release \
  --out paper-v1.opk.zip --policy /trusted/timestamp-policy.json
```

Store the ZIP and **its SHA-256 independently**, in a separate account,
organization or storage medium; the ZIP itself is not permanent storage. On a
**different machine**, select current trust material again from an independent
source, and use that out-of-band expected SHA-256:

```bash
python scripts/preserve.py restore paper-v1.opk.zip \
  --out restored-paper-v1 \
  --expected-sha256 EXPECTED_64_HEX_DIGIT_SHA256 \
  --policy /trusted/timestamp-policy.json
```

Reject path traversal, duplicate ZIP members, symlinks, oversized archives,
unknown extra members, missing/malformed proof, and nonempty destinations.
Neither patient originals nor per-record HMAC keys can be included. The archive
contains a **public-only historical CA/CRL snapshot**, which is evidence to
preserve and is **never automatically a trusted verification root**. This
implementation verifies revocation according to currently available CRLs; it
is not a certified long-term validation (LTV) or signature renewal system.

For forensic checks where no trusted timestamp is available, an explicit
`--integrity-only` path exists, clearly labelled `NOT_VERIFIED`, and must not
be used to claim the presence or date of a trusted timestamp.

## Public access observation, owned by a separate organization

An independent witness can **anonymously GET** a versioned public GitHub
Release and produce an Ed25519-signed record of its retrieved bytes, SHA-256s
and a **self-reported UTC observation interval**. The witness is not the
author's GitHub Action; signatures are independent only if the private key,
hosting and clock are controlled separately and the verifier pins the
observer public key out of band.

```bash
# On a separate trusted operator's machine; NEVER commit the private key.
openssl genpkey -algorithm ED25519 -out /secure/witness-private.key
openssl pkey -in /secure/witness-private.key -pubout -out /secure/witness-public.pem
sha256sum /secure/witness-public.pem  # independently convey this digest

python scripts/observation.py record \
  --repository OWNER/PAPER --version v1 \
  --out /secure/public-observation-v1 \
  --policy /trusted/timestamp-policy.json \
  --signing-key /secure/witness-private.key \
  --timestamp-observation

python scripts/observation.py verify \
  --observation /secure/public-observation-v1 \
  --public-key /secure/witness-public.pem \
  --expected-public-key-sha256 OUT_OF_BAND_PUBLIC_KEY_DIGEST \
  --expected-repository OWNER/PAPER --expected-version v1 \
  --require-observation-timestamp \
  --policy /trusted/timestamp-policy.json
```

A successful witness check **supports the claim that this witness retrieved
these exact bytes in its recorded interval**, conditional on the key and
clock being authentic. It does not prove the **first** publication time or
exclude earlier/different copies. A compromised or dishonest witness can sign
a false assertion. Do not label this `FIRST_PUBLISHED_AT`.


### Independently timestamp the signed observation itself

`--timestamp-observation` (optional, network required) creates two additional
files in the witness package: `observation.tsq` and `observation.tsr`. It
requests RFC 3161 evidence over a **domain-separated, length-prefixed SHA-256
of both `observation.json` AND `observation.sig`**. The TSA token is not included
in its own hash. The verifier uses independently approved CA/CRL material and
checks the nonce, signed digest, policy, CMS chain, certificate validity and
current CRLs. If any check fails, no witness package is finalized.

The timestamp establishes that the **signed witness assertion existed no later
than the TSA timestamp** (subject to the selected TSA policy, clock and signed
accuracy). It does **not** independently confirm the witness fetched the URL:
that fact depends on the witness's honesty, custody and control of its signing
key. A dishonest witness can timestamp a false claim. Nor does it establish the
*first* moment GitHub made the asset accessible. The observer's self-reported
start/end interval is distinct from the TSA's time; if `accuracy` is absent,
report precision as unknown rather than assuming seconds.

The additional `.tsq` and `.tsr` are all-or-nothing. Old Ed25519-only witness
records remain verifiable with `observation_timestamp=NOT_PRESENT`, but
`--require-observation-timestamp` explicitly rejects them. The verification
CLI also requires `--expected-repository` and `--expected-version` from an
**out-of-band trusted source**, blocking substitution of a perfectly signed
receipt for a different paper. The signed publication metadata must declare
the same repository and version. These two requirements are intentionally
fail-closed. Neither witness private keys nor patient data are included.

Run an independently operated observer and TSA validation with a synthetic
public Release before using this with researcher-approved contents.

## Unified offline verification and explicit evidence level

The operator can verify exact Release bytes, the selected TSA's signature,
and optionally the signed and timestamped independent witness in **one command**.
Download a complete immutable Release **anonymously** and choose the CA/CRL
trust material separately; never trust a root because it is included in an
archive. Select a recognized public version and explicitly state which GitHub
repository was expected:

```bash
python scripts/verify_evidence.py \
  --scope existence --bundle downloaded-release \
  --repository OWNER/PAPER --version v1 \
  --policy /trusted/timestamp-policy.json \
  --expected-paper-sha256 OPTIONAL_OUT_OF_BAND_SHA256

python scripts/verify_evidence.py \
  --scope public-observation --bundle downloaded-release \
  --repository OWNER/PAPER --version v1 \
  --policy /trusted/timestamp-policy.json \
  --witness /trusted/public-observation-v1 \
  --observer-public-key /trusted/witness-public.pem \
  --observer-public-key-sha256 INDEPENDENTLY_PINNED_PUBLIC_KEY_SHA256
```

`public-observation` **requires** the witness receipt itself to have been
RFC 3161 timestamped and verifies every exact Release asset, including the
original timestamp request and response. If two valid timestamp tokens refer
to the same paper but different downloaded Release asset bytes, verification
fails. `existence` scope does not attempt to authenticate a public-access
assertion. A success always includes `first_publication: NOT_PROVEN`,
`operator_independence: NOT_VERIFIED`, `authorship: NOT_PROVEN` and
`scientific_correctness: NOT_PROVEN`. The observation clock remains
self-reported even when the signed statement was subsequently timestamped.

**Limitations:** This verifier is offline and cannot audit the witness's
identity, organizational independence, conduct, or the reliability of its
self-reported observation time. An Ed25519 signature plus a TSA token attests
to a **statement's existence before a TSA time**, conditional on independently
trusted keys; it is not a proof of first public availability. Private health
records and HMAC keys are **never** Release assets; verify them separately
under patient-specific permissions using `private_seal.py`.

## Synthetic end-to-end verification

`python scripts/acceptance.py fixture --out /tmp/opk-v1 --version v1`
creates a synthetic PDF, synthetic data/analysis and private-receipt checks.
It contains NO clinical data and NO synthetic HMAC key or original record in
public output. `acceptance.py live --policy /trusted/timestamp-policy.json
--out /tmp/real-timestamp-demo` performs the same operation with two actual
TSA tokens, byte-exact portable archive restore, and mutation rejection.

The manually dispatched **Live acceptance (synthetic only)** workflow checks
that path on a GitHub runner, preserves results for **14 days**, and
independently re-fetches the root/CRL and re-verifies both versions on a
**fresh second runner**. This is an automated integration test, not a public
Release, clinical validation, peer review, or long-term escrow service.

## Repository-owner setup

The following commands use the user's **already authenticated** GitHub CLI;
no credentials should be pasted into the repository, chat or logs:

```bash
python scripts/owner_setup.py --repository OWNER/openpreprint-kit
python scripts/owner_setup.py --repository OWNER/openpreprint-kit --apply --template
# On an individual paper repository, do NOT add --template:
python scripts/owner_setup.py --repository OWNER/my-paper --apply
```

The default is read-only. Explicit `--apply` enables immutable releases and,
for the toolkit only, `--template`. Administration access and a public repo
are required; errors stop the operation, and the script will **never** alter
repository visibility, branches, collaborators, secrets or publish a paper.
Separate human settings/verification remain necessary for workflow credentials,
branch review policies and backups.

## Operational requirements, not simulated by tests

1. Choose an independent observer and an external storage custodian; agree on
   availability, legal/regulatory retention, periodic integrity checks, and
   notification on loss of access.
2. Establish documented CA/CRL update, revocation and renewal policy (including
   renewed attestations when an algorithm or authority becomes untrustworthy).
3. Exercise a real immutable GitHub Release in **two** template-derived
   repositories only after the author explicitly approves the exact data for
   disclosure. Preserve v1 and v2 independently; check permissions before
   promotion. No real patient record may be included.
4. Obtain independent software security and privacy review; turn each finding
   into a regression test, record the remediation and keep review logs.
5. Never describe review metadata as a certified peer-review decision or
   timestamp evidence as an endorsement of scientific/clinical correctness.
