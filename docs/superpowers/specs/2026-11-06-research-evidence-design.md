# Research-wide evidence and private records

## Scope
Extend the existing paper release, not a new medical-record database. Bind public
data, analysis code, protocols, environment files, records and declared processing
steps to exact paper bytes/version. Keep sensitive/health records and opening
secrets outside every Git working tree. No actual participant data is used in tests.

## Choices
A loose list of URLs cannot bind changing data. Uploading all source folders risks
private-data disclosure. Use an explicit `research.json` allowlist, a deterministic
stored ZIP and an index, both covered by manifest schema 2 and the existing RFC
3161 flow. Legacy paper-only schema 1 stays readable. This approach is the
implementer's choice under the requested expansion, not a claimed industry standard.

## Public inventory
Each public artifact has id, kind, visibility, path, version, title, description,
license, sensitivity=non-sensitive, publication_approved=true. Up to 100 artifacts,
25 MiB each and 100 MiB total. No recursive/glob inclusion, symlinks, hidden or
parent paths. The generated index contains hash, byte length and archive path.
Activities explicitly name inputs, outputs, code and environment ids (paper is a
reserved output). Unknown references, conflicting producers and cycles are errors.
Commands are recorded as text and NEVER run. Provenance is declared, not verified.

## Private records
A local-only command generates 32 secret random bytes and commits to the SHA-256
of the original file using a domain-separated SHA-256. The opening receipt has
no original name, hash or date and is created exclusively with POSIX mode 0600.
The receipt and original cannot be inside a detected Git tree or this toolkit tree.
Only an opaque random id, role=record, commitment scheme/digest and private
visibility are allowed in the public index. No filename, patient id, raw file hash,
secret nonce or clinical date is accepted there. This is NOT encryption,
anonymization certification or a healthcare compliance product. Linkage/counts
can still reveal information; secrets require access-controlled encrypted storage.

## Trust and limits
Timestamp the FINAL manifest, not just the paper. Offline integrity is not
independent authenticity; offer an externally pinned manifest digest. Verification
must inspect ZIP contents without extracting or executing them. A valid trusted
RFC 3161 response binds the snapshot, not the clinical event time or truthfulness.
All checksums can be rewritten unless an external digest/attestation is trusted.
Correction is a new artifact and new release; preserve the old release. The kit
cannot stop users directly committing private data, deleting repositories or
rewriting unanchored history. No absolute immutability or completeness is claimed.

## Acceptance
Tests: public round trip, deterministic output, byte modification, removal/extra
files, self-rehashed tampering with external anchor, wrong paper/version, path
escape, symlinks, size limits, malformed/duplicate JSON, graph cycle, sensitive
public record refusal, private randomized commitments/opening mismatch and no
private content/nonce in public ZIP, actual test-CA timestamp rejecting rehash.
Reader page must distinguish declared lineage/private data from verified results.
No real paper is published by development. No new server or Python dependency.
