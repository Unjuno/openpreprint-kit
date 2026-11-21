# OpenPreprint Kit — 現在の受入状態

更新日: **2026-11-22 JST**。基準は [V1_ACCEPTANCE.md](V1_ACCEPTANCE.md) (G0–G7)。完了台帳は [Issue #5](https://github.com/Unjuno/openpreprint-kit/issues/5)。

**現在の判定: P4 / toolkit v1.0.0 = NO-GO。** 2026-11-21 の所有者記録はG0–G7全PASS（独立性 `UNPROVEN`）として保持するが、今回のGitHub現状読戻しでG1/G2と食い違う状態が確認された。G6の人間レビュー・訂正演習・撤回演習の個別証拠も見つかっていない。これらが解決するまで、過去のPASS記録を現状PASSとして再利用しない。

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

## Post-PR #67 merge recheck (current main)

PR #67 was merged at its approved exact head `d484b647e894221bb72c94671c9ca722ea22ed0f`; current main is `a3a9972d812c73a826581686091a80c557c80b0d`. The seven required CI categories passed again on this SHA (Validate, audit, CodeQL, Lean, Windows, macOS), and the self-application and live timestamp/fresh-runner workflows were manually dispatched against this same main SHA. Machine-readable results and run IDs: [`main-a3a9972-postmerge-recheck-2026-11-22.json`](../evidence/acceptance/main-a3a9972-postmerge-recheck-2026-11-22.json), SHA-256 `62c60870f646c645704e605ffda47e5449d490ac1b27f30a8ca17d493df0f327`.

Both workflows produced byte-identical PDFs (187,504 bytes, SHA-256 `9fff4da2ca127f299b262026efff430959b9e7b56f8f403871a4d671021859a5`); trailer ID `f822d315343bff7b4b5450d89167b094` equals SHA-256(current main SHA)[:32]. All four negative self-application cases were rejected. The live RFC 3161 token verified at `2026-11-21T16:58:31Z`; the fresh-runner offline restore passed with preservation ZIP SHA-256 `b6bf40f6ff19d326cd2d9af990d3b34d9ed5b45dae46ce7fb1d662cc59a52432`. Neither workflow created a Release. Scope remains `APPROVED_MANUSCRIPT_EXISTENCE_ONLY`; authorship, independent operation, public availability and long-term retention are not proven.

Main runs: validate 3.10 `44920715884`; quality/audit/Windows/macOS `44920715891`; CodeQL `44920715892`; Lean `44920715881`; self-application `44920715900`; live timestamp/fresh-runner `44920715887`. All concluded success. GitHub Code Scanning and Dependabot alert API readbacks on 2026-11-22 each returned 0 open alerts; `requirements.lock` at this SHA contains 27 pinned distributions and 324 SHA-256 wheel hashes. These alert counts reflect their readback time. OS matrix: Python 3.10 440 = 427 pass + 13 skip; Python 3.12 validation/audit/Windows/macOS each 440 = 434 pass + 6 skip; no failures or errors. Skips are optional Hypothesis tests (7 on Python 3.10), Windows-specific ACL/junction/Win32 tests on non-Windows runners, and POSIX shell integration tests on Windows. Windows-specific tests run on Windows; POSIX launcher tests run on Unix. No required test was skipped on every supporting platform. Raw logs and artifact hashes are in the linked evidence record.

## Current public paper v1/v2 readback (partial G2 evidence)

On 2026-11-21 UTC, unauthenticated HTTPS downloads fetched all 11 assets from each currently resolvable actual-paper Release. `gh release verify` passed for v1/v2; both read back immutable and non-draft; GitHub API digests matched all files, and all eight entries in each `SHA256SUMS` matched. The hash-locked local `verify_release.py` and `citation_validation.py` also passed with independent v1/v2 PDF fingerprints. The recorded JSON report is [`evidence/acceptance/paper-v1-v2-anonymous-readback-2026-11-22.json`](../evidence/acceptance/paper-v1-v2-anonymous-readback-2026-11-22.json). This is partial G2 evidence only: second actual-paper repo is unresolved. The RFC 3161 tokens on these two Releases were reverified on one Windows host with the source-pinned FreeTSA policy and a current signed CRL. This does not complete current G3: the second repo is unresolved, only 2/4 actual-paper Releases were reverified here, and the required two-environment/8-normal-run/20-negative-case matrix is not satisfied by this readback.

## G0–G7 判定

| ゲート | 現在の再確認 | 根拠・残件 |
|---|---|---|
| G0 コード・配布品質 | **TECHNICAL PASS on current main `a3a9972d812c73a826581686091a80c557c80b0d`** | PR #66 exact head `c140290b167c2e46afd8c0f5a181fdf6c39aaec3` and PR #67 exact head `d484b647e894221bb72c94671c9ca722ea22ed0f` are merged. Required CI, self-application, live RFC 3161/fresh-runner passed on current main. Independent review remains `UNPROVEN`. |
| G1 所有者設定・再利用 | **NOT CONFIRMED** | toolkitはpublic/template/immutable-enabled。active `protect-main` rulesetはPR・必須CI・削除/force-push禁止だが、approving review 0・required reviewersなし。paper repoは同template由来・public・immutable-enabledで、main required checksは有効だがapproval 0・rulesetなし。第2の実論文repoは現状で解決できない。詳細と設定依頼は [G1 owner settings package](operator-packages/G1-owner-settings.md)。 |
| G2 実公開・版管理 | **NOT CONFIRMED** | 現在解決できたのはpaper repoのv1/v2の2件。第2repoの2 Releaseとそのattestation・匿名取得・資産照合を今回再検証できていない。失われたReleaseを新規発行して過去証拠の代替にしてはならない。 |
| G3 TSA・否定試験 | OWNER-RECORDED PASS、今回未再監査 | 既存台帳は5版のRFC 3161再検証、2環境8回以上の正常検証、固定20否定ケース誤受理0を記録。正式4版の現在の識別子が解決するまで固定対象は再確定できない。独立性 `UNPROVEN`。 |
| G4 公開観測 | OWNER-RECORDED PASS、今回未再監査 | 既存台帳に署名観測・RFC 3161を記録。G2の正式対象4版との対応を再確認する。独立性 `UNPROVEN`。 |
| G5 複製・オフライン復元 | OWNER-RECORDED PASS、今回未再監査 | 既存台帳に4版のGitHub非接続復元を記録。復元対象とG2正式4版の対応を再確認する。別管理の独立性 `UNPROVEN`。 |
| G6 人間の編集・個人情報管理 | **SOURCE EVIDENCE MISSING** | Issue #5と確認した作業コピーでは、人間レビュー、訂正演習、撤回演習の個別URI/hashを確認できず、`reviews/record.json` は `events: []`。所有者は第2repo/G6記録を「存在しない／不明」と回答。現行基準どおり人間の判断・演習・履歴記録が必要。 |
| G7 セキュリティ・証拠寿命 | OWNER-RECORDED PASS、今回未再監査 | 既存台帳は固定SHA評価・失効/CA更新/復旧試験・責任者・点検手順を記録する。今回のPR候補またはmerge後main SHAに未再結合。外部監査とは主張しない。独立性 `UNPROVEN`。 |

2026-11-21時点で適用された受入基準では独立人間の選任・署名は必須ではない。所有者自身の確認も有効だが、独立性を証明したように表示してはならない。G6にある「実人間によるレビュー過程」は依然必須であり、AI自己点検では代替できない。

## 現在の候補と公開停止

- main fixed SHA: `a3a9972d812c73a826581686091a80c557c80b0d` (PR #67 merge; all required CI and self-application/TSA/fresh-runner rechecks pass).
- PR [#66](https://github.com/Unjuno/openpreprint-kit/pull/66) は承認済みの正確なhead `c140290b167c2e46afd8c0f5a181fdf6c39aaec3` から merge commit `450db84d9e35772fda6af3a24592ced58df8b3ec` として統合済み。
- Candidate ZIPはローカルGold packageで管理し、既存ZIPを履歴として保持する。PR #66 merge後の品質証拠とGold Candidateは Issue #5 comment: https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7065241515 に記録済み。
- GitHub secret名 `OPK_ADMIN_READ_TOKEN` は存在するが、値・有効性・実効scopeは読まず未確認。機密値は検査・記録しない。
- toolkit software Release数は0。正式なv1.0.0 Release/tagは作成しない。

PR #67 merge後、main `a3a9972d812c73a826581686091a80c557c80b0d` でも必須CI、self-application、RFC 3161/fresh-runner、offline restoreを再実行した。G1/G2の第二repoの解決とG6の人間実施記録が揃い、全ゲートが正式基準でPASSし、所有者の最終発行承認が明示されるまでP4はNO-GO。PR #68は候補修正・証拠同梱を含む未マージPRであり、最新headのCI成功はマージ承認ではない。

## Releaseフローに関する注意

個別プレプリント用 `.github/workflows/publish.yml` はkit本体のソフトウェアReleaseではない。root `preprint.yaml` は再利用テンプレートとして `v0` / `UNSPECIFIED` のまま維持する。kit v1.0.0は、全ゲートと最終承認後、固定main SHAからソースアーカイブ、SHA256SUMS、Readiness、Master Reportを組み立て、attestation・匿名取得・byte一致・immutableを確認して発行する。

## 訂正履歴

- 2026-11-22: PR #66 merge後の固定main SHA、全必須CI・自己適用・RFC 3161/fresh-runner結果、再現可能PDF hash、否定試験、OS別件数を追記。G1/G2/G6とP4の未達状態は維持。
- 2026-11-22: 承認済みPR #67 merge後のmain `a3a9972…` で必須CI、自己適用PDF、RFC 3161、fresh-runner復元を再実行し、証拠JSONを追加。ゲートの未達とP4 NO-GOは維持。
- 2026-11-14: 公開Release後のER-1〜ER-3を `evidence/acceptance/erratum-2026-11-15-public-releases.md` に記録。immutable assetは変更していない。
- 2026-11-22: 第2repoが現行GitHub一覧・APIで解決できないこと、G6原証拠が不明であることをライブ読戻しに基づき追記。過去のG1/G2 PASSを現状PASSに転記しないよう訂正。

- 2026-11-22 follow-up: PR #67 merge advanced fixed main to `a3a9972d812c73a826581686091a80c557c80b0d`. Required CI, self-application and live RFC 3161/fresh-runner verification passed on that exact SHA. Results: [`main-a3a9972-postmerge-recheck-2026-11-22.json`](../evidence/acceptance/main-a3a9972-postmerge-recheck-2026-11-22.json), SHA-256 `62c60870f646c645704e605ffda47e5449d490ac1b27f30a8ca17d493df0f327`. PDF SHA-256 `9fff4da2ca127f299b262026efff430959b9e7b56f8f403871a4d671021859a5`; preservation ZIP SHA-256 `b6bf40f6ff19d326cd2d9af990d3b34d9ed5b45dae46ce7fb1d662cc59a52432`. The corresponding local Gold Candidate ZIP SHA-256 is `e7d9478fcc673215d7749b264867474e0b4e9f365c0121e365aa5c5ef0fc5d96`; previous archives remain retained. No Release was created.
