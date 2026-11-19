# Independent witness receipt time anchoring — design

## Goal
Preserve an independently signed observation of anonymously retrievable, exact GitHub Release bytes, and allow a trusted RFC 3161 TSA to timestamp the **signed observation record itself**. A verifier must distinguish proof of existence of this statement from proof of first publication or authenticity of the claimed physical observation.

## Constraints
- Existing `observation.json`, `observation.sig`, and bundle remain valid (backward compatibility).
- Optional `observation.tsq` + `observation.tsr` form an all-or-nothing pair. Both are required if the caller specifies strict proof mode.
- The signed receipt and signature must be bound together via a domain-separated, length-prefixed SHA-256 digest. The timestamp response never becomes part of its own digest.
- Use explicit, separately chosen and pinned TSA policy, CA and current CRLs; no implicit trust of archived roots.
- A verifier must support caller-provided expected repository and tag, and reject mismatches.
- When a timestamp is missing, report `NOT_PRESENT`; do not use the witness self-reported clock as a trusted time.
- Never publish a paper, request private patient material, or deploy a witness private key from this toolkit.
- Reject malformed/untrusted evidence (symlinks, partial timestamp, invalid nonce, wrong digest, forged signature, missing expected identity).

## Approaches considered
1. Timestamp the observer's self-reported clock only: rejected because no external time attestation is gained.
2. Timestamp `observation.json` without Ed25519 signature: rejected because it allows a signature to be added long after the timestamp.
3. **Chosen:** SHA-256 over domain-separated receipt bytes and receipt Ed25519 signature, then RFC 3161 with independent TSA verification. This proves existence of the signed assertion by the TSA time (subject to TSA validity), not earliest publication.

## Trust boundaries
The witness key can lie about an observation; the TSA does not validate HTTP access; GitHub may have served different content earlier; SHA-256 is collision-resistant but cannot prevent deletion. Keep all claims explicit, including whether timestamp accuracy was reported. The host controlling the witness key must be independent to call its assertion independent.

## Accepted behavior
- Local test CA produces timestamp for the exact signed receipt; verifier accepts under out-of-band observer public-key pin and independent CA/CRL policy.
- Change either signed receipt or signature => reject.
- Change RFC 3161 request/response or trust roots => reject.
- Partial sidecar pair => reject; legacy records accepted only with explicit non-strict mode.
- Expected repository/version mismatch => reject without any non-local requests.
