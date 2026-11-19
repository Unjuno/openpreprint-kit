# Forward RFC 3161 timestamp renewal — scope-limited design

Objective: When a source release's preservation ZIP and its original RFC 3161 timestamp still validate under an independently selected **current** trust policy, issue a new, append-only timestamp over an explicit statement binding the entire ZIP digest and prior renewal evidence. Supply a verifier that rejects substitutions and missing chain steps.

## Boundaries

- New sidecar directory, never change or re-publish the original immutable GitHub Release; GitHub Releases can archive the renewal evidence as separately versioned assets.
- `issue` requires explicit user opt-in (`--apply`) and independent source/archive SHA-256 pin. It sends only a SHA-256 TSP request, not documents.
- `verify` demands independently obtained SHA-256 pin for latest renewal step and separately selected TSA policies for **each** step. No CA/CRL auto-trust from the renewal directory.
- Previous step is chained using a domain-separated SHA-256 over length-delimited, exact `statement.json`/`timestamp.tsq`/`timestamp.tsr` bytes. Each step's statement includes original archive SHA, exact release source/revision, step index and previous digest. Final digest separately pinned protects against truncation and alternative history.
- Every step verifies actual RFC 3161 signed message imprint, nonce, policy OID, certificate chain/CRL, current and issuance-time certificate validity; `verify` also restores original archive under independently selected policy.
- Both source policy and each renewal policy must validate **currently**. This protocol helps create a new signed existence anchor **before** old trust ages out, but does not provide historical LTV, signature rescue after expiry, absolute timestamps, independent archive custody, authorship or first publication.
- All inputs bounded; reject unknown/symlink members and existing outputs. No raw patient data, private keys or credential files in renewal evidence.

## Alternative considered

- Timestamping only the SHA-256 of the original manifest: weaker binding to old TSA evidence and other archive bytes; rejected.
- Embedding renewals inside original ZIP/Release: violates immutable originals and creates recursive digest problems; rejected.
- Letting the renewal issuer choose trust CA inside renewal artifacts: unsafe trust bootstrap; rejected.

## Acceptance

A two-step sequence using ephemeral real OpenSSL TSA signatures and distinct CA roots verifies with explicit policies. Rewritten statement, wrong archive digest, wrong pin, truncated/reordered steps, unexpected files/symlinks, missing source TS, failure of new TSA, and a missing/invalid policy must fail closed. GitHub Python 3.10 and 3.12 whole-suite CI required.
