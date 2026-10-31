# Security and evidence model / v0.2

## Claims and trust boundaries

| Claim | Evidence now | Boundary |
|---|---|---|
| Bundle internal consistency | SHA-256 and byte sizes | An attacker can rewrite an unsigned manifest and every checksum |
| Existence-time assertion | RFC 3161 token over manifest, verified signature/nonce/policy/imprint | Only under the caller's independently selected CA/TSA policy and correct cryptographic assumptions |
| Certificate status | Validity now and at token time; current full-chain CRLs | No historical revocation evidence or archival/LTV support |
| Exact upper time bound | Signed genTime plus signed accuracy | Unknown if accuracy absent; accuracy is an assertion, not independently measured here |
| Protection on GitHub | Immutable Release when enabled; GitHub attestations | GitHub is a trust dependency; the release can be deleted and persistence is not guaranteed |
| Public availability at time | **Not implemented** | Requires a separate independent observer, not the same owner's Actions |
| Authorship, originality, ORCID ownership | **Not established** | Metadata and ORCID checksum are not identity or intellectual-property certification |

## Defenses

- No publication on push/PR. Only explicit manual dispatch from a public repository's default branch.
- Draft placeholders, all-zero versions, malformed ORCID and ambiguous author data fail validation.
- Safe YAML parsing; narrow ASCII numeric tags; fixed output filenames; shell arguments quoted and metadata never executed.
- The verifier rejects duplicate JSON keys, unexpected files, partial timestamp pairs and symlink assets.
- A timestamp is bound to the exact manifest and thus all five payload assets. Rewriting all ordinary checksums does not make an old token verify.
- Request nonces are 128-bit random. Requests, tokens and chosen TSA policy must agree.
- SHA-256 pin covers the exact CA PEM bundle bytes. Embedded signer certificates are not automatically trusted roots.
- OpenSSL 3 performs signature, timestamp EKU, chain and CRL checking at security level 2. No `-no_check_time` bypass or failed-to-success fallback.
- HTTPS only; no redirects, URL credentials/query fragments, ambient HTTP proxy credentials or PDF upload. Response size <=1 MiB. Network and subprocess timeouts are bounded; workflow has a 10-minute wall-clock limit.
- Evidence files are written only after verification, exclusively, without replacement. A crash leaving a partial pair fails subsequent verification.
- Draft assets are downloaded and compared before publication; downloaded timestamp evidence is reverified.
- GitHub Actions are full-SHA pinned; job permissions are read-only except the manual publishing job. Package hash-locking is **not implemented**.

## Important remaining risks

1. **Trusted-but-dishonest TSA / compromised keys**: cryptographic validity cannot prove a trustworthy clock or honest operator. Choose the CA/TSA independently and review policy and incident handling.
2. **Current-state validation only**: stale/unavailable CRLs and expired certificates cause failure. Preserve and renew evidence for long-term verification; this lifecycle is not implemented.
3. **GitHub immutability**: the pre-publication administration setting is acknowledged by the user, not independently read by the workflow. The post-publication API check detects a mutable release only AFTER disclosure; it cannot undo publication.
4. **PDF safety and scholarly quality**: validation checks a signature/minimum length, not full PDF structure, active content, scientific correctness or plagiarism.
5. **Local execution**: the runner, Python/OpenSSL binaries, selected trust policy and local clock must be trusted. A malicious repository owner can replace workflows and tooling; use an independent reviewed verifier for adversarial cases.
6. **Source provenance**: `source_claim` is metadata, not a verified build attestation. The timestamp binds its bytes, not the truth of that assertion.
7. **Reuse and citation**: complete real-provider/paper E2E, CFF schema checks, Pages, DOI, archive restoration and independent review remain roadmap items.

## Verification guidance

Run `verify_release.py` for consistency. Run `timestamp.py verify --policy ...` for time evidence.
Obtain the policy/CA pin through a separate trusted channel; never blindly adopt the paper's own policy.
GitHub's attestation verification is additional platform evidence, not an independent timestamp authority.
No tests in this repository publish a real paper or call a public TSA. Private test keys exist only in temporary directories.

## Primary references

- RFC 3161: https://www.rfc-editor.org/rfc/rfc3161.html
- OpenSSL ts: https://docs.openssl.org/3.0/man1/openssl-ts/
- Immutable Releases: https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases
- GitHub Release API (`immutable` field): https://docs.github.com/en/rest/releases/releases
