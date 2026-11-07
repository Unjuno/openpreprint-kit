# Unified offline evidence verifier — design

## Intent
Readers need one entry point for **both** GitHub preprint content and separately trusted evidence. Users must explicitly choose whether to verify an existence-time claim or an independent witness assertion. Individual commands `verify_release.py`, `timestamp.py`, and `observation.py` exist but their distinct PASS outputs can be confused with full authentication.

## Non-negotiable boundaries
- Never report a scientific, clinical, authorship, first-publication, or genuine operator-independence guarantee.
- Never rely on the CA bundled beside the paper or the observer public key bundled beside the witness. The CLI requires a separately selected TSA policy and, in witness mode, an independently pinned observer key.
- Verify the **same exact file set and bytes** in the local release and downloaded witness bundle; matching the paper PDF only is insufficient.
- Explicit scope `existence` verifies content hashes + RFC 3161 + repository/version metadata. Explicit scope `public-observation` additionally verifies witness signature + RFC 3161 of signed observation, identity, and full byte equality.
- `public-observation` is evidence of an attested witness statement; it is not proof of initial public availability or an independently audited operator.
- Fail closed on missing proof, mismatched repository/version, wrong key pin, malformed JSON, partial witness arguments, and sidecar modifications.
- Do not make network requests or fetch remote GitHub resources while verifying; do not create GitHub Releases or expose medical originals.

## Approaches
1. Return a single binary PASS from existing `verify_release.py`: rejected because it only validates unsigned hashes.
2. Merge all cryptography into a new verifier: rejected because duplicated certificate logic can diverge.
3. **Selected:** compose tested existing modules, enforce identical bytes and explicit trust policy, and emit machine-readable evidence scope plus limitations.

## Acceptance
- Two success scopes with unambiguous outcome/limitations and JSON output.
- Malformed input and mixing source versions fail with nonzero exit codes, and no false PASS.
- Tests using actual ephemeral OpenSSL TSA/Ed25519 keys, not fabricated crypto-success mocks.
- Existing verifier behaviour and publication workflows remain unchanged.
