# Trust boundaries and threat model

## Separate claims
- SHA-256 checksums: internal consistency, not authenticated origin without an independent digest.
- RFC 3161: prior existence under the caller's trust policy, not public access time or authorship.
- GitHub immutable releases: platform-enforced release preservation, not an independent TSA.
- Research records: human assertions with report-byte hashes, not authenticated identities or scientific certification.
- Static reader page: a potentially stale rendering, not independent timestamp verification.

## Timestamp verification policy
`timestamp.py` requires SHA-256 manifest matching, 128-bit request/response nonce, policy OID,
CMS signature, TSA EKU and certificate chain validation. Only the explicitly pinned CA PEM
is trusted; embedded certificates are untrusted chain material. The OpenSSL3 verifier checks
current full-chain CRLs, certificate validity now and at the signed time, and rejects timestamps
more than 300 seconds ahead of the verifier clock. Missing accuracy remains unknown.
The TSA clock and key operation must be trusted separately. Current CRLs and certificates
expire: this is not archival/historical revocation validation or a perpetual proof.
HTTPS requests transmit only the digest/nonce, not the PDF. Plain HTTP, redirects, URL
credentials, query strings and oversized responses are rejected. No keys are shipped.

## Publication safety
The manual/default-branch publisher validates drafts, source commit, public visibility,
version vacancy and immutable-release settings before sending a TSA request. Only an actual
404 means a free tag/release; failures are not interpreted as nonexistence.
`OPK_ADMIN_READ_TOKEN` has repository-scoped Administration:read and is exposed only to
preflight steps. Normal GITHUB_TOKEN retains contents:write only in the manual publishing job.
Assets are downloaded and byte-compared while in draft; timestamp evidence is reverified.
Immutable settings are checked again before promotion, and immutable state after publication.
These checks are NOT an atomic settings lock. A malicious administrator or concurrent setting
change remains a trust dependency. Failed post-publication checks do not undo disclosure.

## Review/correction records
CI compares the current record with the actual base commit and requires the old event list
to remain an identical prefix. Referenced reports must exist below reviews/evidence/, match
SHA-256, be UTF-8 .md/.txt <=256 KiB, and contain no symlink path components.
Events have bounded size/count and bind one version to one PDF hash. Retraction remains
prominent even if a later review is added. Actor names and UTC dates are unverified assertions.
An owner can rewrite all unanchored history or invent reviews. Branch rules and independent
reviewers are operational controls, not automatic effects of installing this repository.
Records are NOT included in the original paper's timestamp. Independent anchoring of later
notices remains an open acceptance item. Public repositories cannot provide confidential review.

## Reader view and other limitations
Generated HTML escapes metadata and reports, runs no scripts, uses version-specific links,
retains original paper assets and labels timestamp verification as NOT_VERIFIED. It does not
render Markdown/HTML as executable content. Links can become stale; no external archive is created.
The PDF validator currently checks signature/presence, not full syntax, malware or active content.
CFF/BibTeX external schema/parser tests and dependency distribution hash locking remain incomplete.
Scientific merit, human identity, ethics approval, rights and formal editorial decisions require humans.

## Review and response
Read SECURITY.md before reporting sensitive problems. Use synthetic data, a failing regression
test, a reviewed fix and a full green suite. Never call self-review an independent security audit.
See RELEASE_READINESS.md for the conditions blocking v1.0 and OPERATIONS.md for recovery.
