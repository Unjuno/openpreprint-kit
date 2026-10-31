# RFC 3161 integration implementation plan

> Execution: inline, task-by-task, tests before production code.

**Goal:** Add verifiable external existence-time evidence without conflating it with public access.
**Architecture:** Immutable manifest plus two evidence sidecars, caller-selected pinned trust.
**Tech Stack:** Python >=3.10, OpenSSL 3, PyYAML, asn1crypto 1.5.1, GitHub Actions.
**Spec:** `docs/superpowers/specs/2026-10-31-timestamp-design.md`.

## Global constraints
No production paper is disclosed by tests. No TSA/root chosen on behalf of users.
No private key committed. No automatic trust of downloaded roots. No bypass of
certificate expiry, nonce, digest, policy or CRL failures. No unrequested release.

## Review focus
Malformed metadata must reject without traceback; unknown JSON keys/duplicates must
not create ambiguous trust; partial or symlink evidence must reject; a coherent
rewrite of all checksums must still fail against an old timestamp; untrusted/stale
CRLs and wrong roots must reject. Never call local test time independent evidence.

## Task 1: Harden input and bundle boundaries
Files: `scripts/validate.py`, `scripts/verify_release.py`, `tests/test_hardening.py`.
- [x] Reproduce ORCID X-position crash, boolean schema, Unicode version, v0.0,
      padded placeholders, null author name, duplicate manifest keys.
- [x] Run failing tests, correct only those boundaries, run all baseline tests.
- [x] Accept exactly the seven base assets or those plus the two timestamp files;
      still reject partial pairs, extra files and symlinks.

## Task 2: Implement protocol and offline verification
Files: `scripts/timestamp.py`, `tests/test_timestamp.py`, `requirements.txt`.
- [x] Write CLI tests that initially fail because commands are absent.
- [x] Generate ephemeral CA/TSA/CRL fixtures with OpenSSL (no network).
- [x] Implement request, attach, stamp, verify; pin trust and require full-chain CRLs.
- [x] Test happy path, unknown CA, wrong pin, wrong nonce/policy, malformed token,
      revoked signer, stale CRL, missing proof, tampered/coherently rewritten payload,
      sidecar overwrite refusal, HTTP safety and unsigned/unknown accuracy semantics.

## Task 3: Integrate release and documentation
Files: `.github/workflows/publish.yml`, `.github/workflows/validate.yml`,
`timestamp-policy.example.json`, `trust/README.md`, `README.md`,
`docs/ROADMAP.md`, `docs/THREAT_MODEL.md`, `docs/TIMESTAMPS.md`.
- [x] Require timestamp policy before draft creation; verify downloaded proof before
      publication; preserve manual-only public/default-branch protections.
- [x] Test workflow shape, fixed paths, permissions, and pinned Actions.
- [x] Replace blanket absence claims in notes with verification instructions.
- [x] Record tested vs operationally blocked milestones with objective exit criteria.

## Task 4: Verification and delivery
- [ ] Run complete suite locally and on GitHub; inspect logs, not just badges.
- [ ] Review diff and secrets/key exclusions; record limitations honestly.
- [ ] Open reviewable PR, merge only a passing head, recheck main CI.
- [ ] Report exact commit/test evidence and outstanding deployment requirements.
