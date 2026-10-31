# RFC 3161 evidence design

## Goal and existing state
One public repository per preprint. v0.1 produces seven deterministic release assets,
checks their SHA-256 values, and publishes manually through GitHub Actions. These
hashes are not independent time evidence. The user requested a roadmap and continued
implementation, so this iteration implements the RFC 3161 protocol, not a new server.

## Approaches and decision
- RFC 3161 + explicitly selected TSA: chosen for synchronous issuance and standard
  OpenSSL signature/chain verification. Requires an independently trusted CA, policy
  OID and current CRLs. No provider/account is selected silently.
- OpenTimestamps: deferred; asynchronous anchoring and proof upgrades conflict with
  a single immutable release unless evidence lifecycle is separately designed.
- GitHub-only timestamps: rejected as independent time evidence.
These are implementation decisions, not claims that the user selected a TSA.

## Evidence contract
The exact bytes of `manifest.json` are SHA-256 timestamped. The manifest binds the
five payload assets, including PDF, metadata and citations. `SHA256SUMS` also binds
the manifest. Optional `timestamp.tsq` and `timestamp.tsr` form an all-or-nothing
sidecar pair; they do NOT enter the manifest (avoids a circular digest).
The legacy `time_attestation: null` means no embedded token, not an assertion about
sidecars. No evidence status stored in metadata is trusted without verification.

Verification requires an out-of-band policy, a SHA-256 pinned PEM CA bundle, and
current CRLs. Bundled certificates are untrusted chain-building material, not roots.
Verify content integrity, nonce, SHA-256 imprint, policy OID, TSA signature, EKU,
certificate validity at verification time, and full-chain CRLs using OpenSSL 3.
Certificate expiry and unavailable/stale CRLs fail closed: archival validation at a
historical time is deliberately NOT implemented. Accuracy is an asserted UTC error
bound from the signed token, not measured uncertainty. Missing accuracy means no
computed upper time bound. Public accessibility and authorship are never inferred.

## Interfaces and trust boundaries
- `timestamp.py request DIR --policy FILE --out FILE`: DER query, fresh 128-bit nonce.
- `timestamp.py attach DIR --policy FILE --query FILE --response FILE`: offline
  verification followed by exclusive sidecar creation; never overwrite evidence.
- `timestamp.py stamp DIR --policy FILE`: HTTPS POST of only query/digest, no PDF;
  bounded response, timeout, no redirects, no tokens/credentials forwarded.
- `timestamp.py verify DIR --policy FILE`: offline JSON result, exit 0 only on
  verified crypto+CRLs; malformed/untrusted evidence exits 1.
- `verify_release.py` remains standard-library-only and clearly states that mere
  presence of timestamp files does not verify a timestamp.

## Limits and completion criteria
Python >=3.10; OpenSSL >=3.0, <4; asn1crypto==1.5.1 for ASN.1 parsing only.
Cryptography is delegated to OpenSSL, not hand-implemented. Local test TSA keys are
created in temporary directories; no private key enters GitHub. Real provider
selection, independent clock audit, genuine-paper publication, external observation,
long-term preservation and DOI remain separate acceptance milestones.
