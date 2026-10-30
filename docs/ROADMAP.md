# OpenPreprint Kit development roadmap

## v0: Template foundations — implemented
- [x] Template-ready repository layout. Owner must still enable the **Template repository** setting.
- [x] Paper title, version, license, author name fields, optional ORCID format/checksum.
- [x] Python draft and strict validation; read-only CI.
- [x] Documentation of existence-time versus public-availability-time evidence.

## v0.1: Release publication — implemented in code; real-paper exercise pending
- [x] Manual-only `workflow_dispatch` publisher, public/default-branch checks.
- [x] Publication blocked for draft metadata and missing PDF.
- [x] Deterministic PDF, machine metadata, CITATION.cff, BibTeX and release notes.
- [x] SHA-256 manifest and independently runnable, standard-library-only verifier.
- [x] Create draft -> upload all assets -> download and compare -> publish.
- [x] Reject release versions with an existing tag in the normal workflow.
- [x] Full-SHA pinned checkout and Python setup.
- [x] Unit tests for tampering, path traversal, draft blocking and reproducibility.
- [ ] Full end-to-end test with an actual research paper (not available in template).
- [ ] Upstream CFF schema validation and independent generated citation parsing.
- [ ] Automated verification of immutable-release administration setting (requires appropriate admin read permission).

## v0.2: Independent existence timestamp — not implemented
- [ ] Choose RFC 3161 TSA and establish trusted key/certificate policy.
- [ ] Request a timestamp for fixed release content digest **before publication**.
- [ ] Validate signature, certificate chain, revocation status, time accuracy and hash match.
- [ ] Attach timestamp proof and verification material to the draft bundle.
- [ ] Test forgery, expired certificates, wrong digest and clock-boundary cases.

## v0.3: Independent publication evidence and preservation — not implemented
- [ ] An independent observer fetches public Release URL and signs an observation containing digest and time.
- [ ] Optional outside-GitHub archival copy, DOI registration and GitHub Pages.
- [ ] Handle deletion, rehosting and GitHub outage in the evidence model.

## Design constraints

- One Public Repository per preprint.
- A release may include a GitHub-generated attestation if immutable releases are enabled, but GitHub is not an independent timestamp authority.
- A hash without external authentication establishes **only internal consistency**.
- Authors and license belong to the research output; the toolkit's MIT license must not be applied automatically to the research content.
