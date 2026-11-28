# G5 — owner-operated preservation and offline restore handoff

**Controlling acceptance:** [`docs/V1_ACCEPTANCE.md`](../V1_ACCEPTANCE.md), G5. The frozen condition requires immutable mirror storage for the four formal versions, ZIP and ledger hashes retained through a separate channel, download of the four stored archives, complete restoration with GitHub unavailable, and owner confirmation of retention and inspection responsibility. A separate human custodian is not required under the accepted 2026-11-21 criteria; independence remains `UNPROVEN`.

## Current status: PARTIAL

### Completed technical evidence

The read-only GitHub-hosted verification workflow [`run 46182440809`](https://github.com/Unjuno/openpreprint-kit/actions/runs/46182440809) anonymously retrieved all five currently published immutable paper Releases and verified 55 assets. A separate fresh Linux runner restored all five preservation archives with HTTP(S) proxies set to unreachable loopback and rechecked all 55 restored assets. The formal four targets are the paper repository `v1`/`v2` and robustness repository `v1.0.0`/`v2.0.1`; the extra robustness `v2.0.0` is retained as history, not substituted for a formal target. Artifact IDs and API digests are in [`pr80-hosted-release-readback-2026-11-29.json`](../../evidence/acceptance/pr80-hosted-release-readback-2026-11-29.json). The downloadable Actions artifact expires 2026-12-12 UTC.

The four exact formal target archives have been copied into [`G5-owner-preservation-2026-11-29/`](../../evidence/acceptance/G5-owner-preservation-2026-11-29/), with the source Release ID, source commit, archive size, and SHA-256 in its [machine-readable manifest](../../evidence/acceptance/G5-owner-preservation-2026-11-29/G5-owner-preservation-manifest-2026-11-29.json). The ZIP hashes were recomputed after copying and match the fresh-runner report:

| Repository / tag | Release ID | Source commit | Archive | SHA-256 | Bytes |
|---|---:|---|---|---|---:|
| `openpreprint-kit-paper` / `v1` | `444659219` | `804cb76a4cf5eea65349fc7a8f01e2ce00e1176d` | `paper-v1.opk.zip` | `350e87787836a70739b376a05768431cab1dfea06c1d1fbe9b3bddf83018dcd5` | 248871 |
| `openpreprint-kit-paper` / `v2` | `445442340` | `6ec47ec58e9dc733956615343aad16caca4bb8ee` | `paper-v2.opk.zip` | `795658e72a3826e7a779a4a1a053ce69a03a748239152ed0f3cb0ba7c1c4d0f1` | 1162825 |
| `openpreprint-kit-robustness-eval` / `v1.0.0` | `461207056` | `dedadf3b2e95090439ec10aa4298db72f048caab` | `robustness-v1.0.0.opk.zip` | `9b9bd400046ef4afc23c669ccf6eac27c34a1dd47cd690ff59f6ce1e541ab257` | 280562 |
| `openpreprint-kit-robustness-eval` / `v2.0.1` | `461370251` | `256e4743963a3ffb955b017bb3ecb1d91316e602` | `robustness-v2.0.1.opk.zip` | `8e9ace748310fb4ed1f4f03b23e238cfb7fef7a4dc6eb4b2c2b2aa0975e03026` | 245897 |

Manifest SHA-256: `04d9bd41946ca45d973671b37bbfbc509d11c9adfe92bb82fdb5cb2a4e413920`.

The four copied ZIPs were also restored locally using the locked Python 3.12.10 environment, Git for Windows OpenSSL 3.5.6, the pinned CA/CRL policy, and HTTP(S) proxies set to unreachable loopback. All four expected archive SHA-256 values matched, and all four RFC 3161 chains/signatures/current CRLs verified. Machine results: [`g5-local-offline-restore-results-2026-11-29.json`](../../evidence/acceptance/G5-owner-preservation-2026-11-29/g5-local-offline-restore-results-2026-11-29.json), SHA-256 `43ab7e3f984641bce51dd69f2bf01e4aac5a8c1a39d18a1d6fd633ea2fa55151`. This used the same owner-managed Windows host and does not establish independent custody.

### Remaining G5 work

- These archive copies are committed to the open Kit PR branch, but no immutable mirror Release has been created. A branch or Actions artifact does not meet that condition.
- Record the manifest and four ZIP hashes in Issue #5 or another separately retained channel, then verify the exact mirror Release URL, immutable state, and anonymously downloaded bytes against those hashes.
- The owner must confirm where these copies will be retained, the inspection interval, and who handles recovery. The same owner can accept this route, but it does not prove independent custody.
- Keep G5 `PARTIAL` until those conditions and the owner decision are recorded. Never rewrite an existing immutable Release; if a future mirror snapshot changes, use a new tag.

No second preservation Release or new repository is authorized by this handoff itself. Kit v1.0.0 publication remains prohibited until G0–G7 all pass and final issuance approval is explicit.
