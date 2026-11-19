# Forward timestamp renewal and GitHub-only distribution

> **Status:** Engineering support for *new, forward-looking RFC 3161 existence anchors* on an already valid public preservation ZIP. **Not** complete historical LTV, RFC 4998 Evidence Record Syntax (ERS), 10-year verification certification, first-publication evidence, or independent custody. Production use remains blocked by the v1.0 acceptance gates.

## Why the source ZIP and earlier proofs must be linked

An immutable GitHub Release cannot be changed merely to add a later timestamp. Instead, keep its exact public evidence ZIP byte-for-byte and create a **new** sidecar chain. For each step, the system timestamps the SHA-256 digest of a canonical JSON statement containing the original archive digest, source repository/version/manifest digest and the preceding step's complete evidence digest. The preceding step's digest is computed over the exact JSON statement, TSP request and signed TSP response, with domain separation and length prefixes.

The terminal chain fingerprint must be retained **out of band**; the file under inspection must never be trusted as the sole source of its own expected digest. Both the original TSA and every renewal TSA must currently verify against separately selected CA/CRL files. The package contains **no automatically trusted CA or CRL**.

## Preconditions

- Python 3.10 or 3.12, OpenSSL 3, SHA-256-locked OPK requirements.
- A previously published, valid `v1.opk.zip` from the exact GitHub Release; archive SHA-256 independently recorded.
- Current trust policies under `/trusted/` for the original RFC 3161 proof and each renewal step. Each policy has an independently approved `ca_sha256` and a fresh full-chain CRL.
- An owner-operated, separate GitHub evidence repository with **immutable Releases enabled before publication**. The producer needs `gh` authentication; an independent verifier downloading public assets does not need credentials.
- No patient originals, HMAC keys, Ed25519 private keys, or secret files in the public ZIP.

## First renewal: verify, timestamp, package

A call **without `--apply` is plan-only and performs no HTTPS request**:

```bash
python scripts/renewal.py issue /safe/v1.opk.zip \
  --expected-archive-sha256 ORIGINAL_ZIP_SHA256 \
  --source-policy /trusted/original-tsa.json \
  --renewal-policy /trusted/new-tsa.json \
  --repository OWNER/PAPER --version v1 \
  --out /safe/v1-renewal-step1

# Explicitly opts in to sending the new SHA-256 RFC 3161 request to TSA:
python scripts/renewal.py issue /safe/v1.opk.zip \
  --expected-archive-sha256 ORIGINAL_ZIP_SHA256 \
  --source-policy /trusted/original-tsa.json \
  --renewal-policy /trusted/new-tsa.json \
  --repository OWNER/PAPER --version v1 \
  --out /safe/v1-renewal-step1 --apply
```

Record `chain_sha256` from the JSON output through an independently controlled channel. This new chain contains only timestamp statements, TSP requests and responses; the original ZIP remains unchanged.

```bash
python scripts/renewal.py verify /safe/v1.opk.zip \
  --expected-archive-sha256 ORIGINAL_ZIP_SHA256 \
  --source-policy /trusted/original-tsa.json \
  --renewal-policy /trusted/new-tsa.json \
  --repository OWNER/PAPER --version v1 \
  --chain /safe/v1-renewal-step1 \
  --expected-chain-sha256 INDEPENDENT_CHAIN_SHA256

python scripts/renewal.py pack /safe/v1.opk.zip \
  --expected-archive-sha256 ORIGINAL_ZIP_SHA256 \
  --source-policy /trusted/original-tsa.json \
  --renewal-policy /trusted/new-tsa.json \
  --repository OWNER/PAPER --version v1 \
  --chain /safe/v1-renewal-step1 \
  --expected-chain-sha256 INDEPENDENT_CHAIN_SHA256 \
  --out /safe/v1-renewal.opk.zip
```

`pack` returns `package_sha256`, and the deterministic ZIP includes only allowlisted sidecar files. Save **both** the chain and ZIP digests outside the Release that will contain the ZIP.

## Follow-on renewal: additional TSA / CA is permitted

**Before** earlier CA certificates or CRLs become unacceptable, issue another step. Different CAs/policies are allowed, but the whole previous chain must be verified with the **prior** out-of-band pin and explicit policies.

```bash
python scripts/renewal.py issue /safe/v1.opk.zip \
  --expected-archive-sha256 ORIGINAL_ZIP_SHA256 \
  --source-policy /trusted/original-tsa.json \
  --renewal-policy /trusted/tsa-newer.json \
  --prior /safe/v1-renewal-step1 \
  --expected-prior-sha256 INDEPENDENT_OLD_CHAIN_SHA256 \
  --prior-policy /trusted/new-tsa.json \
  --repository OWNER/PAPER --version v1 \
  --out /safe/v1-renewal-step2 --apply
```

For verification or packaging of the two-step chain, provide `--renewal-policy /trusted/new-tsa.json --renewal-policy /trusted/tsa-newer.json` **in that order**. The new terminal SHA-256 differs from the old fingerprint; the old public GitHub Release must remain unchanged. This verifier currently rejects expired/invalid original TSA proofs even when a newer timestamp is present. **It does not rescue old signatures after expiry** or implement RFC 4998 archival timestamp renewal semantics. Time-sensitive operators must not wait until trust has already expired.

## Publish only the new sidecar ZIP to GitHub Releases

Use the dedicated public evidence repository, not the original published paper's immutable tag. The tag and asset name below are operator-selected unique identifiers. **These commands publish an irreversible public Release once the draft is promoted**; use only on approved public data.

```bash
python scripts/owner_setup.py --repository ARCHIVER/EVIDENCE

gh auth status
# Make sure TAG is new and policy, hashes and source identity are independently approved.
TAG=opk-renew-v1-NEW_UNIQUE_FINGERPRINT_PREFIX

gh release create "$TAG" /safe/v1-renewal.opk.zip \
  --repo ARCHIVER/EVIDENCE --draft --latest=false \
  --title "OPK forward renewal — v1" \
  --notes "Only renewal evidence; not full LTV or first-publication proof"

# Inspect all upload bytes and draft metadata before this publication action.
gh release edit "$TAG" --repo ARCHIVER/EVIDENCE --draft=false
gh release verify "$TAG" --repo ARCHIVER/EVIDENCE
gh release verify-asset "$TAG" /safe/v1-renewal.opk.zip --repo ARCHIVER/EVIDENCE
```

Inspect `immutable: true` from the **public** GitHub Release metadata, then download its exact public asset and compare its independently retained fingerprint. Do not claim this step succeeded unless the actual GitHub calls were performed and rechecked. If draft upload or post-publication verification fails, investigate before creating a **new** tag; do not assert an immutable Release was rolled back.

## Read-only recovery from GitHub Releases

After independently receiving the archive/chain fingerprints and TSA trust policies:

```bash
mkdir /safe/renewal-download
gh release download "$TAG" --repo ARCHIVER/EVIDENCE \
  --pattern 'v1-renewal.opk.zip' --dir /safe/renewal-download

python scripts/renewal.py restore /safe/v1.opk.zip \
  --expected-archive-sha256 ORIGINAL_ZIP_SHA256 \
  --source-policy /trusted/original-tsa.json \
  --renewal-policy /trusted/new-tsa.json \
  --repository OWNER/PAPER --version v1 \
  --package /safe/renewal-download/v1-renewal.opk.zip \
  --expected-package-sha256 INDEPENDENT_PACKAGE_SHA256 \
  --expected-chain-sha256 INDEPENDENT_CHAIN_SHA256 \
  --out /safe/restored-renewal
```

`restore` refuses unknown ZIP members, traversal, repeated entries, symlinks, compression/encryption, missing bytes or wrong external pins; it then verifies **all** actual RFC 3161 signature/chain/nonce/OID/current CRLs before installing a destination. Runtime uses current trust material from the operator, **not** bundled certificates. An independent anonymous GitHub download may also retrieve the public release URL without `gh`; the verifier itself does not use GitHub credentials or network.

## Trust model and limitations

| Input / symbol | Meaning (Japanese) | SI unit | Range/assumption | Type |
|---|---|---|---|---|
| `archive_sha256` | 元証拠ZIP全体のSHA-256指紋 | 1 (無次元) | 64桁の小文字16進文字、外部保持 | バイト列のハッシュ表現 |
| `chain_sha256` | 最新の更新ステップを固定する指紋 | 1 (無次元) | 64桁の小文字16進文字、外部保持 | バイト列のハッシュ表現 |
| `package_sha256` | GitHubに置く更新ZIPの指紋 | 1 (無次元) | 64桁の小文字16進文字、外部保持 | バイト列のハッシュ表現 |
| `step_number` | 更新の連番 | 1 (無次元) | 1〜16、途中欠落なし | 整数スカラー |
| `tsa_time_utc` | TSAが署名した生成時刻 | s (秒) | UTC、検証者の時計とTSAに依存 | 時刻スカラー |

**Dimensional check:** all fingerprint matches compare SHA-256 values with SHA-256 values (dimensionless); no unverified conversion from a hash to elapsed seconds occurs. The TSA-signed `genTime` is a time assertion, not measured clock accuracy. If signed accuracy is absent, uncertainty is **UNKNOWN**, not zero. A combined uncertainty `u_c` or coverage factor `k` is unjustifiable without independently measured inputs.

A new timestamp establishes the existence of **its signed statement** under its TSA trust model; the statement explicitly ties back to the original archive bytes and earlier timestamp proofs. The original TSA may be revoked after renewal, the CA may expire, or SHA-256 may become weak. This implementation still requires every proof to validate **now**. It is **not** an [RFC 4998 ERS](https://www.rfc-editor.org/rfc/rfc4998.html) implementation and does not perform the archival hash-tree renewal, certificate validation at historical policy time or continuous external custody needed for long-term proof.

OpenPreprint Kit must retain historical CRL/OCSP, certificates, independent archive copies, re-timestamp schedules and independent security review before claiming long-term validation or v1.0. A second GitHub repository is still one cloud provider; it cannot guarantee recovery during a platform-wide GitHub outage.
