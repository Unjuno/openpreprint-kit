# External dependency security policy (2026-11-06)

GitHub publication checks parse externally supplied PDF and metadata. Code is executed on
CI runners and therefore third-party parser vulnerabilities matter, even though publication
requires explicit authorization. No document parser can replace an isolated rendering sandbox.

## PDF parser

- **Pinned:** `pypdf==6.21.4` (released 2026-10-28).
- **Minimum known patched version for 2026-10-30 advisory:** `6.21.3`.
- **Never use for publication:** `pypdf==5.9.0`, used in a local exploratory test. It is
  affected by published resource-exhaustion advisories; it was replaced before merge.
- Sources:
  - https://github.com/py-pdf/pypdf/security/advisories/GHSA-62m5-6wh8-28x7
  - https://github.com/py-pdf/pypdf/security/advisories/GHSA-9mvc-8737-8j8h
  - https://pypi.org/project/pypdf/6.21.4/

The PDF limit is 25 MiB / 500 pages with bounded object traversal. These constraints reduce
but do **not eliminate** parser denial-of-service risks. The tests do not prove absence of vulnerabilities.

## Other dependencies

PyYAML and asn1crypto are pinned to explicit versions. Publication citation checks use
`cffconvert==2.0.0` (CFF 1.2.0 schema) and `bibtexparser==1.4.3`, with transitive
packages resolved by pip. Python 3.10/3.12 release CI must pass after any change.

**Still required for v1.0:** resolved transitive versions and **distribution SHA-256 hashes**,
SBOM, vulnerability scanning, key rotation/patch policy, and a separate independent security review.
Version equality in requirements is *not* a complete supply-chain lock.


## Automated update workflow

`.github/dependabot.yml` requests weekly update PRs for pinned Python packages
and pinned GitHub Actions. Dependency changes must pass both CI Python environments,
receive human code review, and be merged deliberately. No automatic merging.
Dependabot version updates do not themselves enable vulnerability alerts or
Dependabot security updates: administrators must configure repository security
settings. A clean Dependabot check is not an independent penetration test.
