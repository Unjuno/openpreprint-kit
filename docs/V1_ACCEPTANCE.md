# OpenPreprint Kit — v1.0 goal and objective release gates

## Single v1.0 goal

Publish and independently verify **one paper + disclosed public research data + analysis code** per public GitHub repository, with immutable versioned Releases, machine-checkable SHA-256 provenance, an independently trusted RFC 3161 existence-time token, and a separately managed signed public-access witness. A different custodian must restore and verify the bytes **without GitHub**.

The kit is **not** a scholarly journal, formal peer-review certification, authorship or scientific-truth oracle, clinical electronic-health-record system, proof of initial publication time, or guarantee of ten-year future availability. Confidential originals and all private signing/HMAC keys must remain outside public GitHub. Real patient data require a separately assessed regulated-data workflow.

## Release gates (ALL required)

| Gate | Owner | Verifiable acceptance | Status (2026-11-08) |
|---|---|---|---|
| G0: code/security | Engineer + human reviewer | Python 3.10/3.12 Ubuntu 24.04; **0 failed mandatory tests**, no skipped mandatory checks; distribution-hash locks and pinned Actions; 0 unresolved critical/high issues; RED→GREEN for repairs. | PARTIAL: 216 tests green in each Python 3.10/3.12 job ([CI 42408857827](https://github.com/Unjuno/openpreprint-kit/actions/runs/42408857827)); independent security sign-off remains a separate G7 gate |
| G1: owner configuration | GitHub repository owner | Template enabled; 2 distinct public template-derived paper repos; immutable Releases enabled **before** publication; protected branch, required CI and human PR review readback. | BLOCKED |
| G2: versioned publishing | Publisher + independent verifier | **2 repositories × 2 versions = 4** immutable Releases, including >=1 author-approved genuine paper; check every asset and GitHub attestation; v1 bytes unchanged after v2. | BLOCKED: 0 Releases |
| G3: trusted TSA | TSA policy custodian + verifier | All 4 bundles validate signed imprint/nonce/OID/chain/current CRL under independently pinned CA; >=20 tamper/expired/revoked/wrong-policy samples produce **0 false PASS**; unknown accuracy labeled unknown. | PARTIAL: synthetic FreeTSA v1/v2 verified |
| G4: public witness | External operator, **not** author/GitHub Actions | Anonymous GET of all 4 published Releases using separately controlled host/Ed25519 key, signed receipt plus optional RFC 3161 receipt timestamp; second verifier checks out-of-band key pin and exact assets. | BLOCKED |
| G5: GitHub-native custody and offline portability | Separate GitHub archival operator + offline recovery verifier | All 4 immutable source versions replicated to another GitHub repository with distinct credentials; pinned catalog/receipt SHA-256 independently retained; all 4 archives anonymously downloaded and restored on a fresh machine offline after export. Operational retention and annual audit schedules required. GitHub-wide availability is NOT guaranteed. | BLOCKED: no real GitHub mirror or external operator |
| G6: research governance | Author + human editorial/privacy lead | Real copyright/consent/COI review; no patient originals or secrets published; 1 human review process, 1 correction and 1 retraction exercise with history unchanged. | BLOCKED |
| G7: independent security and long-term plan | Unrelated software/privacy reviewer | Signed security/privacy assessment for GitHub permissions, YAML/PDF/archives, TSA chain and historical CRLs, witness key and confidential data; renewal/re-timestamping documented and tested; high/critical issues fixed. | BLOCKED |

**Decision:** PASS only if G0–G7 all have dated evidence, independent check and explicit owner sign-off. FAIL on accepted malicious content, privacy breach or integrity failure. Otherwise **UNCERTAIN/BLOCKED**; do not claim production v1.0. No real sensitive files in acceptance fixtures.

## H / T / D / C / U acceptance contract

**H (falsifiable hypothesis):** Four immutable releases, verified independently on two environments (8 release verifications total), yield no erroneous acceptance of 20 intentionally modified/unauthorized samples. All historical releases retain original bytes.

**T (minimum verification):** 2 repo × 2 releases, >=8 off-machine bundle checks, 4 signed witness observations, 4 offline restorations from GitHub-exported archives, 20 intentionally invalid cases, one real author-approved manuscript, one human-led correction/retraction rehearsal and one independent security/privacy review. Fail fast on any false acceptance or leaked secret.

**D (decision):** `PASS` iff all gates independently evidenced. `FAIL` if any tamper/secret leak is incorrectly accepted. `UNCERTAIN/BLOCKED` for missing owner permissions, TSA precision, witness independence or custody evidence. Do not silently downgrade validation.

**C (counterhypotheses):** One operator controls both author and witness keys; GitHub mutable settings race the release; TSA/CRL trust expires or is revoked; archive/digest both lost; semantic/clinical claims are untrue even when bytes match. Exercise controllable attacks; require external evidence for non-testable claims.

**U (uncertainty):** TSA signed accuracy may be absent; TSA operation and clock, verifier's clock, CA revocation history, offsite custodian continuity, and human consent are unmeasured. No basis to compute combined standard uncertainty `u_c` or coverage factor `k`; record **UNKNOWN**, not a fabricated estimate. **Ten years of verifiability is a maintenance target**, not a present-tense measured fact.

## Work order

1. Close YAML duplicate-key ambiguity with test-first patch and CI.
2. Owner enables template, immutable Releases, branch checks; retain readback, **without sharing tokens in chat**.
3. Publish two synthetic repository version sequences then one author-approved real paper; verify attestations, historical stability, citations and downloadability.
4. Obtain an independently operated witness, a separately administered GitHub archive repository, and a tested offline export/restore with digest pins; a second GitHub repo is not another cloud failure domain.
5. Run consent, review, correction, retraction and external security/privacy gates.
6. Implement/test renewal, historical revocation evidence and durable discovery/identifiers; re-run all gates before v1.0 declaration.

Audit evidence: [AUDIT_2026-11-08.md](AUDIT_2026-11-08.md). Tracking: GitHub issue #5. This gate supersedes broad implementation-stage checkboxes as the **v1.0 production decision**.

## 2026-11-12 — GitHub-only online storage decision

**Online publication and replication backend: GitHub Releases only.**
`github_mirror.py` allows an existing public source Release's verified custody
store to be mirrored into a **different** immutable GitHub Release. Anonymous
recovery is verified with separately pinned catalog and receipt hashes and a
separately approved TSA policy. Google Drive is not a required acceptance
mechanism. This supersedes any implied Drive preference in earlier notes.

**G5 is NOT automatically satisfied by a second GitHub repository.**
Separate-owner GitHub mirroring reduces repository/account-specific risk, but
is still one hosting provider. The existing GitHub-unavailable restoration test
requires an *actual exported* store and separately held hashes on an offline
machine; it does not demand any specific second cloud vendor. Human custody,
retention, renewal, and future availability require recorded evidence.

## 2026-11-12 — source Release provenance check for mirrors

The mirror read-only `verify --require-source-release` option independently GETs each original source Release from GitHub, checks `immutable=true`, confirms the exact asset inventory and compares every asset byte against the pinned archive. Failures do not leave a partially verified output. Without the flag, disaster recovery remains possible when a source repository disappears, but the output explicitly records `source_publication=NOT_CHECKED`. Anonymous mode does **not** cryptographically verify GitHub/Sigstore release attestations, so G2 still requires `gh release verify` and independent attestation evidence. Neither mode establishes operator independence.
