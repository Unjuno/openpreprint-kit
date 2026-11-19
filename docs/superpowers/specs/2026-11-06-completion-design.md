# Verifiable delivery and recovery — design

Goal: a third party can verify a paper, data, code and confidential-record commitments,
receive real RFC 3161 evidence, and recover the same bytes without GitHub.
Existing release semantics, strict trust policy and original records remain unchanged.
No clinical claims, patient data, fabricated reviewers or automatic trust of bundled roots.

Decisions (implementation choices under the user's instruction to finish):
- Exercise public FreeTSA with synthetic bytes only, using its officially published CA
  PEM SHA-256 pin, explicit OID 1.2.3.4.1 and current CRL. No payment or account is needed.
  A successful signature is evidence under that TSA trust assumption, not public availability.
- Preserve a portable uncompressed ZIP with a fixed allowlist: bundle assets, public
  verification material and a manifest. Never archive a workspace, secrets or arbitrary files.
- Require a separately retained archive digest before restoring. Reject ZIP traversal,
  duplicate names, links, unknown members and oversized members. Verify inside a temporary
  directory before atomic promotion; never overwrite an existing destination.
- Verify timestamp evidence again using the caller's current independently supplied policy.
  Archived CA/CRLs are evidence copies, not automatically trusted or always-current material.
- Supply a single acceptance runner that makes synthetic v1 and v2 without editing the
  template; proves private commitments, tamper rejection and restore in isolated processes.
- Hash-lock dependencies for supported CI runtimes and test a clean installation.
- Independent operator deployment, admin-only settings and a human audit are not fabricated.

Alternatives: remote database/SaaS rejected (unnecessary new trust and cost); arbitrary ZIP
backup rejected (secret leakage and extraction attacks); keeping checksums only rejected
(no externally anchored authenticity). Long-term legal signature validation is not claimed.
