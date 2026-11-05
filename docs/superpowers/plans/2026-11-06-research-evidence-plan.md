# Research evidence implementation plan

> Execute inline using executing-plans and test-driven-development. No independent
> development subagent is available; do not label self-review as independent review.

**Goal:** bind papers, research assets and local private-record commitments in a
verifiable versioned release.
**Architecture:** allowlisted inventory + stored ZIP + schema-2 manifest. Keep
RFC 3161 signing unchanged, expand its hashed subject. Private openings stay local.
**Tech Stack:** Python >=3.10 standard library; existing PDF/citation/TSA dependencies.
**Spec:** ../specs/2026-11-06-research-evidence-design.md

## Global constraints
No real health/participant data, private keys or opening secrets in GitHub.
No research code execution; no real paper release. Retain legacy schema-1 reads.
File count 100; public file 25 MiB, total 100 MiB; JSON 1 MiB. Explicit privacy approval.

## Review focus
- Private metadata leakage: exact allowlist; receipt and source outside Git.
- ZIP traversal/bombs/duplicates: bounded stored entries, no extraction.
- Full rehash/downgrade: separate manifest pin and real test-CA signature.
- False provenance: invalid graph rejected; valid graph remains author-declared.
- Integration: uploaded pair, reverified pair, escaped reader inventory, old tests.

## Task 1: public research package
Files: scripts/research_bundle.py, prepare_release.py, verify_release.py;
 tests/test_research_bundle.py; research.json.
Interfaces: build_research(root, paper_sha256, version)->dict[str,bytes];
 verify_research(folder, metadata)->None (ValueError on rejection).
- [x] Write black-box failing tests against existing prepare/verify commands.
- [x] Implement exact schemas, graph checks and bounded deterministic ZIP.
- [x] Add schema 2, exact asset set and --expected-manifest-sha256.
- [x] Run new tests and old paper-only regression tests; record results.

## Task 2: private local openings
Files: scripts/private_record.py, tests/test_private_record.py.
Interfaces: commit_record(source, receipt)->public artifact dict;
 verify_record(source, receipt, expected_commitment)->None.
- [x] Write failing tests for randomized opening, tampering, Git-tree refusal,
 secret permissions, overwrite refusal and no public names/raw hashes.
- [x] Implement local-only bounded streaming and explicit independent digest input.
- [x] Run tests, then an actual test-CA proof on a mixed public/private bundle.

## Task 3: integration and operation
Files: build_site.py, workflows, docs/RESEARCH_DATA.md, README.md, ROADMAP.md,
 RELEASE_READINESS.md, tests/test_research_integration.py.
- [x] Write reader/workflow/crypto regression tests, confirm failures.
- [x] Render inventory/declared lineage; upload only named generated assets.
- [x] Document synthetic example, privacy review and correction retention.
- [x] Verify uploaded code identity and full pinned-runtime CI (code commit 005cd31); final documentation/head checks remain a merge gate.

## Execution ledger
Baseline archive tree matches remote ecf3c18addaeac9fddf476021d467c93e59f8394.
Local network cannot install pinned pypdf 6.21.4 or citation tools; installed pypdf
5.9.0 hangs on a legacy malformed-PDF test. Do not downgrade repository pins.
New data/privacy tests use standard library and valid synthetic PDF fixtures;
complete pinned-runtime verification must run on GitHub CI. No full local PASS
is claimed while that environment mismatch remains.

CI evidence: code commit `005cd31a13cef8319c39821ebe6bdbbb885d373a`, validate run
42106895016 (Python 3.10/3.12), quality run 42106895291. Artifact log records
158 tests, OK with no skipped tests. All uploaded code/test files equal local bytes;
only the intentionally pending documentation differs. Final source identity and
merge CI are checked separately on the final PR head. No real health data, real TSA
request or paper Release was created. Independent review remains outstanding.
