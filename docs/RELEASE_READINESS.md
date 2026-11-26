# OpenPreprint Kit — 現在の受入状態

更新日: **2026-11-22 JST**。基準は [V1_ACCEPTANCE.md](V1_ACCEPTANCE.md) (G0–G7)。完了台帳は [Issue #5](https://github.com/Unjuno/openpreprint-kit/issues/5)。

## 2026-11-26 live gate refresh (supersedes the 2026-11-22 current-state readback below)

Read back from GitHub on 2026-11-26. No PR has merged since the fixed main SHA `76d7d4c6fd551bb48048d774e47191ba26274cbf`. PR #72 is documentation/evidence only, OPEN and unmerged, at exact head `46484a436673e6274cffde0123c8e94544bee781`; its PR-event Quality (`45759875361`), Validate (`45759875243`), Lean (`45759875301`), CodeQL Python (`45759875404`), and GitHub CodeQL (`139709770561`) checks pass. The exact-head Windows, macOS, audit, Python 3.10/3.12 counts and skip reasons are recorded in the [2026-11-26 Issue #5 CI readback](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7183618797); raw logs and the machine-readable check-run readback are preserved in Gold Candidate progress archive r74, whose SHA-256 is `1663cc6c5839ff95512b06f540e5471a70af836ad99fe8f005ac54bd00e67b4d`.

The two public paper repositories now resolve and both declare `Unjuno/openpreprint-kit` as their GitHub template source: `openpreprint-kit-paper` and `openpreprint-kit-robustness-eval`. Immutable Releases are enabled in both repositories and in the toolkit repository (`enabled=true`, `enforced_by_owner=false`). Their branch protections differ: the first paper repo has strict required checks but requires **0** approving reviews and does not enforce rules for administrators; the robustness-eval repo requires **1** approving review, strict required checks, conversation resolution, and administrator enforcement. The robustness-eval repository has no Releases yet. PR #2 (v1) is OPEN at `290868b058333f3f4118822ec8b9c07cde73b8bc`, all seven required contexts pass, but it has zero reviews and remains `REVIEW_REQUIRED`; its same-owner Write invitation is still pending. PR #5 (v2 root configuration) remains OPEN/DRAFT and stacked on PR #2. Any same-owner account review is technical workflow evidence only, not independent review.

### Current G0–G7 status

| Gate | 2026-11-26 result | Current evidence and remaining condition |
|---|---|---|
| G0 Code and distribution quality | **TECHNICAL PASS on main `76d7d4c6fd551bb48048d774e47191ba26274cbf`** | Required main checks, self-application, and timestamp/fresh-runner checks pass on the fixed source. PR #72 documentation CI also passes. This does not complete other gates. |
| G1 Owner setup and reuse | **PARTIAL / NOT PASS** | Two public template-derived paper repos exist and Immutable Releases are enabled. The first paper repo still has 0 required approvals and does not enforce administrators; the second repo's required review invitation is pending and PR #2 is not reviewed. Record the exact rule readbacks before considering G1 complete. |
| G2 Publication and version control | **BLOCKED** | The first paper repo has its existing immutable v1/v2. The second repo has no releases; its v1/v2 candidates are not published. Thus only 2 of the required 4 real-paper Releases are currently available. Existing immutable Releases remain unchanged. |
| G3 TSA and negative tests | **PARTIAL / NOT PASS** | The v1 candidate has exact-head no-publication stamp/fresh-runner evidence, and local negative-suite recomputation is 20 cases / 23 judgments / 0 false accepts. The required evidence across all four actual published versions is incomplete. |
| G4 Public observation | **PARTIAL / NOT PASS** | Observation evidence for the two existing paper versions remains; the second paper has no public Release to observe. Independence remains `UNPROVEN`. |
| G5 Replication and offline restore | **PARTIAL / NOT PASS** | Existing v1/v2 preservation evidence remains; the second paper has no published assets to anonymously download and restore. Separate management is not claimed. |
| G6 Human editorial and privacy decisions | **BLOCKED** | `reviews/record.json` still has `events: []`. No real human review record, correction exercise, or withdrawal exercise is present. The human handoff package is not a substitute for those records. |
| G7 Security and evidence lifetime | **PARTIAL / NOT PASS** | Kit and robustness-eval Actions policies have selected pinned actions and mandatory SHA pinning. The first paper repo still reports `allowed_actions=all` and `sha_pinning_required=false`. A fixed-SHA owner security/privacy decision, lifecycle responsibility, and maintenance confirmation are also outstanding. |

**P4 / toolkit v1.0.0 remains NO-GO.** Independence is `UNPROVEN`; no independent review, audit, or custody is claimed. No toolkit Release or second-paper Release was created in this refresh. The owner-authorized second-paper release sequence remains conditional on the PR #2 review and merge, v1 publication and verification, then rebasing/testing/publishing v2. Formal G0–G7 and final issuance approval remain required for toolkit v1.0.0.

**現在の判定: P4 / toolkit v1.0.0 = NO-GO。** 2026-11-21 の所有者記録はG0–G7全PASS（独立性 `UNPROVEN`）として保持するが、今回のGitHub現状読戻しでG1/G2と食い違う状態が確認された。G6の人間レビュー・訂正演習・撤回演習の個別証拠も見つかっていない。これらが解決するまで、過去のPASS記録を現状PASSとして再利用しない。

## Latest fixed-main checkpoint — PR #70

PR #70's owner-approved head `85aa296088c3c3a4d30804c619c5375d74174647` merged to main as `74f88fdb7942c793185600e4d2fcd076944596e1`. All seven required CI categories passed on that exact SHA. The self-application and live RFC 3161/fresh-runner workflows also passed on the same SHA, without publishing any Release. Detailed run IDs, 441-test per-job totals and skip reasons are in [post-merge quality evidence](QUALITY_EVIDENCE_POSTMERGE_PR70_2026-11-22.md).

The two workflow PDFs are byte-identical (187,504 bytes, SHA-256 `d892d100ce5cbae994b7547570828eba280b62e716123e2ffd26edf56e0026bc`). RFC 3161 status was `VERIFIED` at `2026-11-21T20:55:17Z`; a separate runner restored and verified the preservation archive. This proves approved-metadata evidence existence under the supplied trust policy, not authorship, public availability, independent observation or durable retention; TSA accuracy was unspecified.

Current public GitHub discovery found only `Unjuno/openpreprint-kit` and `Unjuno/openpreprint-kit-paper` as OpenPreprint repositories. The second account's private repositories are not visible to this credential, so absence is not inferred. The paper repository has only two resolvable immutable releases (v1/v2); main requires CI checks but zero approving reviews. Current code-scanning, Dependabot and secret-scanning alert endpoints each returned zero open alerts, which does not replace a human security/privacy assessment. Current status remains G1/G2/G6 **BLOCKED**, G3/G4/G5/G7 **PARTIAL EVIDENCE / NOT PASS**, P4 **NO-GO**.

The current local Gold Candidate is r36, main `74f88fdb7942c793185600e4d2fcd076944596e1`, ZIP SHA-256 `7245a0fc99ffd07d5846093b14512bb39701a4dc1df2651f57cd170f4b874b2c`. It includes a fixed-SHA G1/G2/G6 handoff, and 42/42 human-review input files were rehashed against the exact source archive. This is not a human review or publication approval. Issue #5 records the [main verification](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7069164453), [live gate/security readback](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7069233390), and [current-SHA handoff](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7069268972).

## 2026-11-14 の公開記録と 2026-11-22 の読戻し

次の表は当時の記録を履歴として残したもの。2026-11-22にライブGitHubで読み戻せた対象は、paper repo の v1/v2のみだった。第二repoとそのReleaseは現在のowner repo一覧・Release API・公開repo検索から解決できなかったため、当時の記録だけでは現在のG1/G2をPASSにできない。

| # | 履歴上のRepository | Release / ID / tag SHA | 履歴上の公開時刻 | 2026-11-22の確認 |
|---|---|---|---|---|
| 1 | `openpreprint-kit-paper` | v1 / `444659219` / `804cb76a4cf5eea65349fc7a8f01e2ce00e1176d` | 2026-11-13T19:39:48Z | repoでRelease v1を確認 |
| 2 | `openpreprint-kit-paper` | v2 / `RE_kwDOVtdYwc4ajOkk` / `6ec47ec58e9dc733956615343aad16caca4bb8ee` | 2026-11-14T16:48:30Z | repoでRelease v2を確認 |
| 3 | `openpreprint-kit-robustness-eval` | v1 / `RE_kwDOVubJxs4ajPQ0` / `940bd77d02318e9d95fa5cb7db568804de2d1860` | 2026-11-14T16:53:04Z | repo/Releaseを解決できず |
| 4 | `openpreprint-kit-robustness-eval` | v2 / `RE_kwDOVubJxs4ajPhz` / `2631782a109bf47572e4310ae0da32f26aec3de9` | 2026-11-14T16:54:53Z | repo/Releaseを解決できず |

2026-11-22のowner repo一覧（`gh repo list Unjuno --limit 300`）で `openpreprint` に一致したものは `openpreprint-kit` と `openpreprint-kit-paper` の2件だった。`openpreprint-kit-robustness-eval` はRelease APIで解決できず、公開repo検索でも結果がなかった。これはrepoが削除されたと断定するものではなく、現在の場所・可視性・名前が不明という観測である。

paper repo の `main` は保護され、required checks は `validate (3.12)`, `validate (3.10)`, `audit`。`required_approving_review_count=0`。toolkit repo は `is_template=true`。Immutable Releases API は `enabled=true`, `enforced_by_owner=false`。これらの設定値だけでは、存在不明な第二repoのテンプレート由来・保護・公開前Immutable設定を証明できない。

## 2026-11-22 post-merge technical evidence (PR #66)

PR #66 was merged with owner approval for exact head `c140290b167c2e46afd8c0f5a181fdf6c39aaec3`; merge commit/main is `450db84d9e35772fda6af3a24592ced58df8b3ec`. Required CI, self-application, live RFC 3161/fresh-runner all passed on this main. Reproducible PDF output across workflows: 187,504 bytes, SHA-256 `716045b0e2656d750d69a18e7ef2883d641e43c1e47b0725ba710f2b26666da9`; source-bound trailer ID `f67e968c0db6932c0395fa654a619a2c`. Four negative self-application cases were rejected. Fresh-runner offline restore passed; preservation ZIP SHA-256 `719dc0a989d4d22740d7b80bfcd4dbeef174152e754ee2d72169999a16eb6d16`. Full evidence and log URLs are indexed in Issue #5 comment https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7065241515 and local evidence package; scope is `APPROVED_MANUSCRIPT_EXISTENCE_ONLY`, not authorship, independent custody, or public availability.

## Post-PR #67 merge recheck (historical fixed-main checkpoint)

PR #67 was merged at its approved exact head `d484b647e894221bb72c94671c9ca722ea22ed0f`; current main is `a3a9972d812c73a826581686091a80c557c80b0d`. The seven required CI categories passed again on this SHA (Validate, audit, CodeQL, Lean, Windows, macOS), and the self-application and live timestamp/fresh-runner workflows were manually dispatched against this same main SHA. Machine-readable results and run IDs: [`main-a3a9972-postmerge-recheck-2026-11-22.json`](../evidence/acceptance/main-a3a9972-postmerge-recheck-2026-11-22.json), SHA-256 `62c60870f646c645704e605ffda47e5449d490ac1b27f30a8ca17d493df0f327`.

Both workflows produced byte-identical PDFs (187,504 bytes, SHA-256 `9fff4da2ca127f299b262026efff430959b9e7b56f8f403871a4d671021859a5`); trailer ID `f822d315343bff7b4b5450d89167b094` equals SHA-256(current main SHA)[:32]. All four negative self-application cases were rejected. The live RFC 3161 token verified at `2026-11-21T16:58:31Z`; the fresh-runner offline restore passed with preservation ZIP SHA-256 `b6bf40f6ff19d326cd2d9af990d3b34d9ed5b45dae46ce7fb1d662cc59a52432`. Neither workflow created a Release. Scope remains `APPROVED_MANUSCRIPT_EXISTENCE_ONLY`; authorship, independent operation, public availability and long-term retention are not proven.

Main runs: validate 3.10 `44920715884`; quality/audit/Windows/macOS `44920715891`; CodeQL `44920715892`; Lean `44920715881`; self-application `44920715900`; live timestamp/fresh-runner `44920715887`. All concluded success. GitHub Code Scanning and Dependabot alert API readbacks on 2026-11-22 each returned 0 open alerts; `requirements.lock` at this SHA contains 27 pinned distributions and 324 SHA-256 wheel hashes. These alert counts reflect their readback time. OS matrix: Python 3.10 440 = 427 pass + 13 skip; Python 3.12 validation/audit/Windows/macOS each 440 = 434 pass + 6 skip; no failures or errors. Skips are optional Hypothesis tests (7 on Python 3.10), Windows-specific ACL/junction/Win32 tests on non-Windows runners, and POSIX shell integration tests on Windows. Windows-specific tests run on Windows; POSIX launcher tests run on Unix. No required test was skipped on every supporting platform. Raw logs and artifact hashes are in the linked evidence record.

## Current public paper v1/v2 readback (partial G2 evidence)

On 2026-11-21 UTC, unauthenticated HTTPS downloads fetched all 11 assets from each currently resolvable actual-paper Release. `gh release verify` passed for v1/v2; both read back immutable and non-draft; GitHub API digests matched all files, and all eight entries in each `SHA256SUMS` matched. The hash-locked local `verify_release.py` and `citation_validation.py` also passed with independent v1/v2 PDF fingerprints. The recorded JSON report is [`evidence/acceptance/paper-v1-v2-anonymous-readback-2026-11-22.json`](../evidence/acceptance/paper-v1-v2-anonymous-readback-2026-11-22.json). This is partial G2 evidence only: second actual-paper repo is unresolved. The RFC 3161 tokens on these two Releases were reverified on one Windows host with the source-pinned FreeTSA policy and a current signed CRL. This does not complete current G3: the second repo is unresolved, only 2/4 actual-paper Releases were reverified here, and the required two-environment/8-normal-run/20-negative-case matrix is not satisfied by this readback.

## G0–G7 判定

| ゲート | 現在の再確認 | 根拠・残件 |
|---|---|---|
| G0 コード・配布品質 | **TECHNICAL PASS on fixed main `74f88fdb7942c793185600e4d2fcd076944596e1`** | PR #70後の必須CI・自己適用・RFC 3161/fresh-runnerが同一SHAで成功。独立性は `UNPROVEN`。|
| G1 所有者設定・再利用 | **BLOCKED** | toolkitはpublic/templateでactive `protect-main` rulesetあり。公開repo検索で確認できる論文repoは1つだけ。paper mainは必須CI 3件だがapproving review count 0。第2の論文repoは未解決。|
| G2 実公開・版管理 | **BLOCKED** | 現在解決できる実論文Releaseはpaper v1/v2の2/4。別論文repoの2版・asset attestation・匿名取得・版間不変性を検証できていない。|
| G3 TSA・否定試験 | **PARTIAL EVIDENCE / NOT PASS** | v1/v2で追加の正常・否定試験を実施したが、正式な4公開版が揃わず、現在の8回試験は同一Windows host。|
| G4 公開観測 | **PARTIAL EVIDENCE / NOT PASS** | 現在確認できる4版対応の署名観測対象が2版に留まる。独立性は `UNPROVEN`。|
| G5 複製・オフライン復元 | **PARTIAL EVIDENCE / NOT PASS** | 現在解決できる実Releaseは2版のみ。正式4版の復元行列・別保管責任は未確認。|
| G6 人間の編集・個人情報管理 | **BLOCKED** | `reviews/record.json` は `events: []`。レビュー、訂正演習、撤回演習の人間記録なし。最新42-file input handoff is in local r36 candidate and Issue #5; handoff is not review evidence.|
| G7 セキュリティ・証拠寿命 | **PARTIAL EVIDENCE / NOT PASS** | Current main CI, PR #70 revoked-origin preservation regression and zero open GitHub alert readbacks add evidence. Owner fixed-SHA security/privacy decision, lifecycle responsibility and maintenance confirmation remain outstanding.|

2026-11-21時点で適用された受入基準では全ゲートに独立人間の選任・署名を一律必須とはしていない。所有者自身の確認を認めるゲートでも、独立性は `UNPROVEN` と記録する。独立レビュー・観測・別管理保管・外部監査を証拠として主張する場合、AIや同一人物が管理する別アカウントは実在する独立担当者の代替にならない。G6の実人間によるレビュー・訂正・撤回演習は依然必須で、AI自己点検では代替できない。

## Historical checkpoint: main 838a622

The following checkpoint details are retained as historical evidence and are superseded by the PR #70 fixed-main checkpoint above.

## 現在の候補と公開停止

- main fixed SHA: `838a622ff14db35f93c5dca1a5028a8a1a6efe67` (PR #68 merge; all required CI and self-application/TSA/fresh-runner rechecks pass).
- PR [#66](https://github.com/Unjuno/openpreprint-kit/pull/66) は承認済みの正確なhead `c140290b167c2e46afd8c0f5a181fdf6c39aaec3` から merge commit `450db84d9e35772fda6af3a24592ced58df8b3ec` として統合済み。
- Candidate ZIPはローカルGold packageで管理し、既存ZIPを履歴として保持する。PR #66 merge後の品質証拠とGold Candidateは Issue #5 comment: https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7065241515 に記録済み。
- Current Gold Candidate for main `838a622ff14db35f93c5dca1a5028a8a1a6efe67`: `Gold-Candidate-2026-11-22-main-838a622-r9-20261122T022700.zip`, SHA-256 `057b9461bd39923381ac216e37a38a1e505486841d9c00948cb8b972ca56e1f0`. Issue #5 superseding evidence: https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7066518649.
- GitHub secret名 `OPK_ADMIN_READ_TOKEN` は存在するが、値・有効性・実効scopeは読まず未確認。機密値は検査・記録しない。
- toolkit software Release数は0。正式なv1.0.0 Release/tagは作成しない。

PR #68 merge後、main `838a622ff14db35f93c5dca1a5028a8a1a6efe67` で必須CI、self-application、RFC 3161/fresh-runner、offline restoreを再実行した。最新のmachine-readable evidenceは [`main-838a622-postmerge-recheck-2026-11-22.json`](../evidence/acceptance/main-838a622-postmerge-recheck-2026-11-22.json)。詳細ログとartifact URLはIssue #5の[最新台帳コメント](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7066518649)にある。G1/G2の第二repoの解決とG6の人間実施記録が揃い、全ゲートが正式基準でPASSし、所有者の最終発行承認が明示されるまでP4はNO-GO。PR #68はowner承認済みの正確なheadからmerge済み。

## Releaseフローに関する注意

個別プレプリント用 `.github/workflows/publish.yml` はkit本体のソフトウェアReleaseではない。root `preprint.yaml` は再利用テンプレートとして `v0` / `UNSPECIFIED` のまま維持する。kit v1.0.0は、全ゲートと最終承認後、固定main SHAからソースアーカイブ、SHA256SUMS、Readiness、Master Reportを組み立て、attestation・匿名取得・byte一致・immutableを確認して発行する。

## 訂正履歴

- 2026-11-22: PR #70 approved head `85aa296088c3c3a4d30804c619c5375d74174647` merged as `74f88fdb7942c793185600e4d2fcd076944596e1`. Required CI, self-application and live RFC 3161/fresh-runner passed. Cross-workflow PDF SHA, G1/G2 live readback, zero alert counts, G7 revoked-origin regression, and current-SHA human handoff were recorded; P4 remains NO-GO.

- 2026-11-22: PR #66 merge後の固定main SHA、全必須CI・自己適用・RFC 3161/fresh-runner結果、再現可能PDF hash、否定試験、OS別件数を追記。G1/G2/G6とP4の未達状態は維持。
- 2026-11-22: 承認済みPR #67 merge後のmain `a3a9972…` で必須CI、自己適用PDF、RFC 3161、fresh-runner復元を再実行し、証拠JSONを追加。ゲートの未達とP4 NO-GOは維持。
- 2026-11-22: PR #68を承認済みhead `22787ab…` からmerge。main `838a622…` で必須CI、自己適用PDF、RFC 3161、fresh-runner復元を再実行し、最新証拠JSON・Issue #5 ledgerを追加。未達ゲートとP4 NO-GOは維持。
- 2026-11-22: Gold Candidate ZIPをmain `838a622…` に再固定。別経路SHA-256とオフライン展開・134 checksum照合を記録。独立性を主張する担当作業はAIまたは同一管理者の別アカウントで代替しない旨を明記。
- 2026-11-14: 公開Release後のER-1〜ER-3を `evidence/acceptance/erratum-2026-11-15-public-releases.md` に記録。immutable assetは変更していない。
- 2026-11-22: 第2repoが現行GitHub一覧・APIで解決できないこと、G6原証拠が不明であることをライブ読戻しに基づき追記。過去のG1/G2 PASSを現状PASSに転記しないよう訂正。

- 2026-11-22 follow-up: PR #67 merge advanced fixed main to `a3a9972d812c73a826581686091a80c557c80b0d`. Required CI, self-application and live RFC 3161/fresh-runner verification passed on that exact SHA. Results: [`main-a3a9972-postmerge-recheck-2026-11-22.json`](../evidence/acceptance/main-a3a9972-postmerge-recheck-2026-11-22.json), SHA-256 `62c60870f646c645704e605ffda47e5449d490ac1b27f30a8ca17d493df0f327`. PDF SHA-256 `9fff4da2ca127f299b262026efff430959b9e7b56f8f403871a4d671021859a5`; preservation ZIP SHA-256 `b6bf40f6ff19d326cd2d9af990d3b34d9ed5b45dae46ce7fb1d662cc59a52432`. The corresponding local Gold Candidate ZIP SHA-256 is `e7d9478fcc673215d7749b264867474e0b4e9f365c0121e365aa5c5ef0fc5d96`; previous archives remain retained. No Release was created.
