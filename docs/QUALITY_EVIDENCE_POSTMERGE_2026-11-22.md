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

## Acceptance status

- G0: technical pass on the fixed main SHA above; independent review status remains `UNPROVEN`.
- G1/G2: `NOT CONFIRMED`. The second repo and its two historical Releases could not be resolved from current owner-scoped and public GitHub readbacks; do not infer deletion or replace historical releases.
- G3/G4/G5/G7: previously owner-recorded, not re-audited against a currently resolvable set of four formal releases. Independence and separate custody remain `UNPROVEN`.
- G6: `BLOCKED / SOURCE EVIDENCE MISSING`. Human review, correction exercise, and withdrawal exercise records were not found; owner reports second repo or G6 records absent/unknown. AI review cannot substitute.
- P4 and toolkit v1.0.0: `NO-GO`. No Release or tag was created.
- The two GitHub accounts are controlled by the same owner and do not count as independent human reviewers.
