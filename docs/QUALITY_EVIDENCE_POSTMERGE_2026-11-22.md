# Post-merge quality evidence — 2026-11-22

## Fixed source

- Repository: `Unjuno/openpreprint-kit`
- PR #66 head approved for merge: `c140290b167c2e46afd8c0f5a181fdf6c39aaec3`
- Merge commit and tested main: `450db84d9e35772fda6af3a24592ced58df8b3ec`
- Scope: technical self-application against the already approved manuscript. This does not establish authorship, independent operation, or public availability.
- Issue #5 evidence: https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7065241515

## Workflow runs

| Workflow/check family | Run ID | Result |
|---|---:|---|
| Validate Python 3.10 / 3.12 | 44920715884 | success |
| Quality, audit, Windows and macOS regression | 44920715891 | success |
| CodeQL Python | 44920715892 | success |
| Lean | 44920715881 | success |
| First-paper self-application | 44920715900 | success |
| Live RFC 3161 timestamp and fresh-runner restore | 44920715887 | success |

## Test counts and skip interpretation

- Python 3.10 validation: 440 total = 427 passed + 13 skipped + 0 failed + 0 errors.
- Python 3.12 validation, audit, Windows regression, and macOS regression: each 440 total = 434 passed + 6 skipped + 0 failed + 0 errors.
- Seven optional Hypothesis property tests skip on the Python 3.10 job because the optional test-only dependency is not installed. These are optional.
- Windows-only ACL, localized trustee SID, junction, and Win32 handle tests skip on non-Windows runners and execute on Windows.
- POSIX shell launcher integration tests skip on Windows and execute on Unix runners.
- No required test is skipped on all supporting platforms. Windows and WSL are not counted as separate physical environments.
- Original workflow logs and downloaded artifacts are preserved in the evidence package referenced from Issue #5.

## Self-application and cryptographic evidence

- Main self-application and live timestamp workflows produced byte-identical PDF output: 187,504 bytes; SHA-256 `716045b0e2656d750d69a18e7ef2883d641e43c1e47b0725ba710f2b26666da9`.
- The source-bound PDF trailer ID is `f67e968c0db6932c0395fa654a619a2c`.
- Four negative self-application cases were rejected.
- RFC 3161 verification passed at `2026-11-22T00:45:30+09:00`.
- Pinned CA SHA-256: `2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438`.
- Manifest SHA-256: `750ceed73f41ab58cfd9188866e7424a40c1bed8276907ac125a9aba10312155`.
- Fresh-runner offline restore passed. Preservation ZIP SHA-256: `719dc0a989d4d22740d7b80bfcd4dbeef174152e754ee2d72169999a16eb6d16`.

## Gold Candidate

- Candidate: `Gold-Candidate-2026-11-22-main-450db84-20261121T155352Z.zip`
- Candidate ZIP SHA-256: `1d6b9104e737a99ef2724560cdbe8cd81f309889dcabf4b03d257cec4e5fe152`.
- The ZIP was independently hashed with PowerShell and Python, ZIP integrity checked, then extracted offline; all 23 `SHA256SUMS` entries matched.
- Append-only archive ledger continuation SHA-256: `5d74114f4fcd84272bc87e674ab8316e259a7aace6344b0983f09c2b144d570f`.
- Earlier ZIPs remain preserved; this is a new candidate and does not modify prior archives or immutable paper releases.

## Current paper v1/v2 anonymous readback (partial G2 evidence)

- Readback report: [`evidence/acceptance/paper-v1-v2-anonymous-readback-2026-11-22.json`](../evidence/acceptance/paper-v1-v2-anonymous-readback-2026-11-22.json), SHA-256 `AD5ACFBF87E34E6C7AADFB2177FC7755EF790E849F146A416DE93079C7F5C3FB`. The downloader used unauthenticated HTTPS GET requests and recorded the transport and per-asset digests.
- `gh release verify v1` and `gh release verify v2` both passed and verified GitHub attestations. Both releases read back as `immutable=true`, `draft=false`, 11 assets.
- Anonymous downloads: all 11 asset digests for each release matched the GitHub Releases API. All 8 entries in each release's `SHA256SUMS` also matched. The existing 2026-11-14 release matrix's 11 recorded v1 digests match the current v1 download; that historical matrix does not contain an entry for paper v2.
- With dependencies installed from the repository's hash-locked `requirements.lock`, `scripts/verify_release.py` passed for both releases with separately recorded PDF fingerprints; `scripts/citation_validation.py` passed CFF schema and BibTeX parsing. These checks do not establish truth of citation metadata, authorship, or peer review.
- RFC 3161 re-verification on this Windows host returned `VERIFIED` for both manifests using the source-pinned FreeTSA caller-supplied policy (CA SHA-256 `2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438`, policy OID `1.2.3.4.1`). OpenSSL 3.5.6 verified the downloaded CRL signature; CRL validity was 2026-09-18 through 2027-09-18. The TSA times were v1 `2026-11-13T19:39:35Z`, v2 `2026-11-14T16:48:12Z`. This verifies only 2/4 actual-paper Releases in one environment, so it does not satisfy the full G3 matrix (4 releases, 8 normal verifications over 2 environments, and 20 negative cases).
- This verifies only the currently resolvable `openpreprint-kit-paper` v1/v2. It does not resolve the second actual-paper repository or meet the two-paper/two-version G2 requirement. No Release or asset was changed.

## Acceptance status

- G0: technical pass on the fixed main SHA above; independent review status remains `UNPROVEN`.
- G1/G2: `NOT CONFIRMED`. The second repo and its two historical Releases could not be resolved from current owner-scoped and public GitHub readbacks; do not infer deletion or replace historical releases.
- G3/G4/G5/G7: previously owner-recorded, not re-audited against a currently resolvable set of four formal releases. Independence and separate custody remain `UNPROVEN`.
- G6: `BLOCKED / SOURCE EVIDENCE MISSING`. Human review, correction exercise, and withdrawal exercise records were not found; owner reports second repo or G6 records absent/unknown. AI review cannot substitute.
- P4 and toolkit v1.0.0: `NO-GO`. No Release or tag was created.
- The two GitHub accounts are controlled by the same owner and do not count as independent human reviewers.
- G0 security/dependency readback on 2026-11-22: GitHub Code Scanning alerts API returned 0 open alerts; Dependabot alerts API returned 0 open alerts. `requirements.lock` at this fixed source contains 27 pinned distributions and 324 SHA-256 wheel hash entries. These alert counts describe the state at readback time.

## Superseding post-PR #67 fixed-main recheck

The current fixed main for this recheck is `a3a9972d812c73a826581686091a80c557c80b0d` (PR #67 merge). The machine-readable record is [`main-a3a9972-postmerge-recheck-2026-11-22.json`](../evidence/acceptance/main-a3a9972-postmerge-recheck-2026-11-22.json), SHA-256 `62c60870f646c645704e605ffda47e5449d490ac1b27f30a8ca17d493df0f327`.

- Required CI passed: validate 3.10/3.12, audit, CodeQL Python, Lean, Windows regression, and macOS regression. Windows and macOS are separate hosted runners; WSL is not counted as an independent physical environment.
- Test totals: Python 3.10 `440 = 427 PASS + 13 SKIP + 0 FAIL + 0 ERROR`; Python 3.12 validation, Ubuntu audit, Windows regression, and macOS regression each `440 = 434 PASS + 6 SKIP + 0 FAIL + 0 ERROR`. Skip reasons and platform scope remain as listed above.
- Self-application and live timestamp workflows produced identical PDFs (187,504 bytes, SHA-256 `9fff4da2ca127f299b262026efff430959b9e7b56f8f403871a4d671021859a5`); four negative cases were rejected.
- RFC 3161 token verified at `2026-11-21T16:58:31Z`; pinned CA SHA-256 `2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438`; manifest SHA-256 `3da6a2397785bdcecf6b8c1f6274da43eae5dc962fac0daae5aeb6183130373e`. Fresh-runner offline restore passed; preservation ZIP SHA-256 `b6bf40f6ff19d326cd2d9af990d3b34d9ed5b45dae46ce7fb1d662cc59a52432`.
- No Release was created. This demonstrates the approved-manuscript self-application workflow, not independent review, authorship, formal G0-G7 acceptance, or long-term custody.

The updated local Gold Candidate is `outputs/Gold-Candidate-2026-11-22-main-a3a9972-r7-20261122T020512.zip`, SHA-256 `e7d9478fcc673215d7749b264867474e0b4e9f365c0121e365aa5c5ef0fc5d96`. Its independent sidecar is adjacent to the ZIP; the offline audit record SHA-256 is `4a1a1f983b174e4bc3788b9d03680991d4086b548a61846252a25dcba87efa6e`. Earlier Gold ZIPs remain preserved. This is a local technical candidate package; it does not qualify as independent custody.

## Superseding post-PR #68 fixed-main recheck

PR #68 exact owner-approved head `22787ab49a4cc9c0cbb724ea0915d22ffade20b0` was merged as main `838a622ff14db35f93c5dca1a5028a8a1a6efe67`. Machine-readable recheck: [`main-838a622-postmerge-recheck-2026-11-22.json`](../evidence/acceptance/main-838a622-postmerge-recheck-2026-11-22.json), SHA-256 of committed Git blob bytes `35a20f83c2644dd2304bc6a4f994607662da11b0f1ba01b5d065fbc52925a31e` (a CRLF-converted Windows working copy has a different digest). Source-tree archive SHA-256 `657f9c7fe7eaa96d173945f0353eac3f3900ed842d35fd621b4f7642486ace8e`. Run IDs: validate `44929110267`; quality/audit/Windows/macOS `44929110382`; CodeQL `44929110325`; Lean `44929110275`; self-application `44929173591`; live timestamp/fresh-runner `44929176037`.

- Required CI: all 7 categories passed. Python 3.10: 440 total = 427 PASS + 13 SKIP + 0 FAIL + 0 ERROR. Python 3.12 validate, Ubuntu audit, Windows and macOS each 440 = 434 PASS + 6 SKIP + 0 FAIL + 0 ERROR.
- Skip reasons: Python 3.10 skips 7 optional Hypothesis tests because its test-only dependency is absent and 6 Windows-only tests. Ubuntu/macOS each skip the 6 Windows-only tests; Windows skips 6 POSIX shell integration tests, which run on Unix. No required test is skipped on all supporting platforms.
- Self-application and live timestamp runs produced byte-identical PDFs (187,504 bytes; SHA-256 `1d79581a7e543d95162991d98b251077f0062da9339d1c9e98d0401ce91c0811`); four negative cases were rejected.
- RFC 3161 token status `VERIFIED` at `2026-11-21T17:18:46Z`; manifest SHA-256 `45c20926b70965274ee69ba8974581326d59e08c7ffe8236a5da7e94a8ed93ee`. Fresh-runner offline restore passed; preservation ZIP SHA-256 `4da83d9380e2e5d4641adeb21267cbb7b840381ff50477eac94aa7b66af9b508`. Neither workflow created a Release.
- Four previously preserved archive candidates still have only one-host technical verification; no G2/G3/G5 formal gate upgrade is claimed.
- New local Gold Candidate ZIP SHA-256 `057b9461bd39923381ac216e37a38a1e505486841d9c00948cb8b972ca56e1f0`. ZIP measured independently by PowerShell and Python, extracted offline, 135 file members and 134 checksum entries matched with zero mismatches. Previous ZIPs remain retained.
- G0 technical PASS on fixed main; G1/G2 NOT CONFIRMED; G3/G4/G5/G7 owner-recorded but not fully re-audited to the current formal four-release target; G6 human review/correction/withdrawal evidence missing or unknown. Independence remains UNPROVEN and P4 stays NO-GO.

Issue #5 ledger: https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7066518649. This is technical evidence only: it does not establish authorship, human acceptance, independent custody, formal G0-G7 acceptance, or long-term retention.
