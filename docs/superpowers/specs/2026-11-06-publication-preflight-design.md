# OpenPreprint Kit publication-file preflight design (2026-11-06)

## Goal
A GitHub-derived research repository must not publish a formally invalid, encrypted, interactive, or excessively large PDF, or machine-readable citation metadata that fails external format validation. Preserve the existing one-paper/one-repo, manual-only publishing workflow and immutable versioning.

## Constraints
- Python 3.10 and 3.12 on Ubuntu 24.04 GitHub Actions; Python 3.13 local development.
- The draft template remains valid without any PDF; strict publication validation fails closed.
- No external SaaS, credentials, or real paper upload in tests. Do not claim that syntax checking proves scientific merit, PDF/A archival conformance, or security of all PDF readers.
- Hard maximum of 25 MiB and 500 pages for preprints, with explicit guidance for archives of larger data.
- Use pypdf 6.21.4 strict reading; forbid encrypted documents and interactive actions (OpenAction, JavaScript, Launch, RichMedia, embedded files, AcroForm, additional actions) found via bounded structural scan.
- Apply guard to publication, not harmless draft edits. Cover encrypted, corrupt, malicious, oversized, and valid files with tests.
- Validate generated CITATION.cff against official CFF 1.2.0 schema using cffconvert, and BibTeX through an independent parser. Never invent publication year.

## Alternatives
1. Signature-only PDF magic check: present implementation; insufficient as it allows corrupt and active PDFs.
2. CLI qpdf/Poppler on runner: stronger PDF repair/structure inspection, but adds OS packages and runner portability risk.
3. Pure Python pypdf strict structural check with size/interactive restrictions: chosen for a version-pinned reproducible base, but does not certify complete PDF conformance or render safety.

## Boundaries and residual risks
- PDFs can be constructed to exploit PDF software even when structural checks pass. Treat all PDFs as untrusted; render sandboxed.
- CFF and BibTeX external parsing checks syntax and schema, not author truth or scholarly peer review.
- Dependency hashes, public TSA operations, independent public-access observations, durable off-GitHub archive, and peer review remain distinct acceptance gates.
