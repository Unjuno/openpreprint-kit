# Verifiable delivery and recovery implementation plan

> Execute with superpowers:executing-plans; no subagent dispatch tool is available here.

**Goal:** Real public-TSA and portable recovery acceptance, not only mock tests.
**Architecture:** Add safe preservation around existing immutable bundle and timestamp APIs.
**Tech Stack:** Python >=3.10, OpenSSL 3, ZIP, existing pinned Python packages.
**Spec:** ../specs/2026-11-06-completion-design.md

## Global constraints
- Existing bundle filenames/format stay compatible. No patient originals/keys in archives.
- Keep authority trust explicit. Never disable CRL/signature checking to make a test pass.
- Never publish a real paper or set an unsupported completion flag.

## Review focus
ZIP traversal/duplicates/links; silently missing timestamp; bundled-root trust; partial
restore; confusing CI artifacts with permanent archival; confidential-key leakage.

## Tasks
- [x] T1: Test preservation roundtrip, bad archive pin, traversal, duplicate names,
  symlinks, unexpected private files, malformed proof, existing output, and missing proof.
  Run failing tests, implement scripts/preserve.py, run the full suite.
- [x] T2: Build synthetic fixture generator and tests. Include paper/data/code/receipt,
  no private bytes in public bundle, v1/v2 retained, reproducibility and exact paths.
- [x] T3: Run scripts/live_acceptance.py on GitHub with public-TSA proof, tamper tests,
  recovery, and fresh verification in a second environment. Save actual evidence.
- [x] T4: Generate hash locks for supported Python runtimes and validate installs.
- [x] T5: Add optional signed public observation and a verification/renewal procedure;
  clearly separate who observed availability from who authenticated a timestamp.
- [x] T6: Update release-readiness ledger, verify source identity, CI, and merge only
  tested changes. Preserve evidence and name authorization-only blockers precisely.

Preflight: preserve consumes verify_release.verify and timestamp.verify_proof unchanged.
Fixture generator copies scripts into separate workspaces; never modifies source metadata.
