# Owner-operated publication pilot (synthetic only)

This is the concrete next action for G1/G2/G3 in `V1_ACCEPTANCE.md`, not a
production v1.0 certification. Do not substitute more unit tests for actual
public Releases. The operator must have an authenticated GitHub CLI and the
required GitHub repository creation/administration/contents permissions.
Never paste tokens or private keys into chat, Issues, source or logs.

## 1. Install the tested kit and inspect the plan

Use a reviewed checkout of OpenPreprint Kit, Python >=3.10 and OpenSSL 3. Use a
current supported GitHub CLI with `gh release verify` and `verify-asset`.
On the owner's machine:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements-build.lock
python -m pip install --require-hashes --no-build-isolation -r requirements.lock
gh auth login --hostname github.com
python scripts/pilot.py --template Unjuno/openpreprint-kit \
  --repos Unjuno/opk-demo-acceptance-a Unjuno/opk-demo-acceptance-b
```

The last command is **PLAN_ONLY**: no requests, credentials, files or public
changes. Substitute your own repository owner if necessary. The toolkit does
not grant permissions; `gh` uses the credentials the operator already holds.

## 2. Select TSA trust independently, then explicitly publish the pilot

Prepare `/trusted/timestamp-policy.json`, the independently checked CA pin and
current signed CRLs using `TIMESTAMPS.md`. The opt-in synthetic FreeTSA profile
already used by `.github/workflows/live-acceptance.yml` is a test example, not
a general approval of a time authority for clinical/regulated use. An archived
CA file must never become trusted merely because it arrived with a ZIP.

```bash
python scripts/pilot.py --template Unjuno/openpreprint-kit \
  --repos Unjuno/opk-demo-acceptance-a Unjuno/opk-demo-acceptance-b \
  --policy /trusted/timestamp-policy.json \
  --out ../opk-pilot-evidence --publish-synthetic
```

**This command changes GitHub:** it activates the toolkit's template flag if
needed, creates **two new public repositories**, enables their immutable
Releases, and publishes **four explicitly synthetic prereleases** (v1/v2).
Destination names must start `opk-demo-`. Any existing destination is refused.
It never changes repository visibility, disables protections, force-pushes,
overwrites a previous run or publishes the user's real manuscript/data.

For each version it commits only generated public source files, creates a
source-bound paper/data/code/private-commitment bundle, validates citations and
RFC 3161, creates a draft, downloads and checks every byte, rechecks immutability,
promotes, verifies GitHub's release and asset attestations, downloads anonymously,
and restores a digest-pinned evidence ZIP. After v2, it downloads v1 again and
checks that its original bytes remain unchanged. Private synthetic originals
and per-record HMAC keys are destroyed with their temporary directory and are
never exported. Earlier public commitments remain in v2's source history.

## 3. Read the result, including partial failures

`pilot-report.json` is updated after each irreversible transition. `PASS` means
only **SYNTHETIC_PUBLICATION_ACCEPTANCE** passed. `production_readiness` always
remains `NOT_ESTABLISHED`; independent witness/custodian/human review are always
`NOT_PERFORMED`. API outages and permission errors stop rather than masquerading
as an unused name/tag.

If a command fails after promotion, the Release may already be public. The
journal distinguishes a draft from a requested promotion or pending public
verification. **Nothing is automatically deleted or rolled back.** Inspect
GitHub and the preserved evidence before cleanup or a rerun. Automatic resume
is intentionally not implemented: choose new unused demo names only after
reviewing the partial state. Do not weaken immutability to force a retry.
GitHub setting checks and promotion are separate requests, not an atomic lock.

The `github-release-attestation.json`, anonymous bundles and `evidence.opk.zip`
files can be given to a separately managed verifier. Transfer archive hashes
through a different trusted channel. Full owner authentication, real GitHub
publication and genuine operator independence cannot be proven by mocked tests.

## 4. Complete the remaining external gates

Have a different operator run `observation.py` and `verify_evidence.py` with an
out-of-band observer-key pin. Have a separate custodian use `custody.py` to keep
copies under independent credentials, test recovery without GitHub, and commit
to retention and cryptographic-renewal procedures. Obtain human editorial,
consent/privacy and security sign-off. The pilot does not replace those parties.

Primary interfaces: [repo create](https://cli.github.com/manual/gh_repo_create),
[release verify](https://cli.github.com/manual/gh_release_verify),
[asset verify](https://cli.github.com/manual/gh_release_verify-asset),
[immutable release API](https://docs.github.com/en/rest/repos/repos#enable-immutable-releases).

## 5. GitHub-only evidence mirrors (supersedes external cloud examples)

After the synthetic pilot actually publishes v1/v2, build the verified multi-version
custody store using each version's `evidence.opk.zip` and its independently
computed SHA-256. On a separately managed GitHub archive account, create a
public mirror repository and enable immutable Releases. Run
`github_mirror.py plan`, then `publish --apply`, with the exact source repository,
catalog SHA-256 and independent TSA policy. The mirror Release contains
`custody.json`, the exact v1/v2 ZIPs and a digest-bound receipt. Anonymous
`github_mirror.py verify` reconstructs the local evidence store and checks
both SHA-256 pins and RFC 3161. Details:
[GITHUB_PRESERVATION.md](GITHUB_PRESERVATION.md).

No Google Drive account or integration is part of the supported publishing
pipeline. GitHub-wide outages remain a common-mode risk; export the verified
local store for offline disaster-recovery testing if that guarantee is required.
