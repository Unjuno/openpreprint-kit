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

## G0–G7 判定

| ゲート | 現在の再確認 | 根拠・残件 |
|---|---|---|
| G0 コード・配布品質 | PR候補は技術PASS。最終mainは未固定 | PR #66 head `a8880b8e3e7988369d7f49328c7b0c8c7770e98f` の必須CI 7カテゴリ、自己適用、live RFC 3161/fresh-runnerがsuccess。PR未mergeのため、マージ後main SHAで再実行が必要。独立性 `UNPROVEN`。 |
| G1 所有者設定・再利用 | **NOT CONFIRMED** | toolkit templateは有効、paper repoの保護設定を読戻した。一方、必要な第2のtemplate-derived公開paper repoを現状で解決できず、同repoの設定も読戻せていない。 |
| G2 実公開・版管理 | **NOT CONFIRMED** | 現在解決できたのはpaper repoのv1/v2の2件。第2repoの2 Releaseとそのattestation・匿名取得・資産照合を今回再検証できていない。失われたReleaseを新規発行して過去証拠の代替にしてはならない。 |
| G3 TSA・否定試験 | OWNER-RECORDED PASS、今回未再監査 | 既存台帳は5版のRFC 3161再検証、2環境8回以上の正常検証、固定20否定ケース誤受理0を記録。正式4版の現在の識別子が解決するまで固定対象は再確定できない。独立性 `UNPROVEN`。 |
| G4 公開観測 | OWNER-RECORDED PASS、今回未再監査 | 既存台帳に署名観測・RFC 3161を記録。G2の正式対象4版との対応を再確認する。独立性 `UNPROVEN`。 |
| G5 複製・オフライン復元 | OWNER-RECORDED PASS、今回未再監査 | 既存台帳に4版のGitHub非接続復元を記録。復元対象とG2正式4版の対応を再確認する。別管理の独立性 `UNPROVEN`。 |
| G6 人間の編集・個人情報管理 | **SOURCE EVIDENCE MISSING** | Issue #5と確認した作業コピーでは、人間レビュー、訂正演習、撤回演習の個別URI/hashを確認できず、`reviews/record.json` は `events: []`。所有者は第2repo/G6記録を「存在しない／不明」と回答。現行基準どおり人間の判断・演習・履歴記録が必要。 |
| G7 セキュリティ・証拠寿命 | OWNER-RECORDED PASS、今回未再監査 | 既存台帳は固定SHA評価・失効/CA更新/復旧試験・責任者・点検手順を記録する。今回のPR候補またはmerge後main SHAに未再結合。外部監査とは主張しない。独立性 `UNPROVEN`。 |

2026-11-21の受入基準緩和により独立人間の選任・署名は必須ではない。所有者自身の確認も有効だが、独立性を証明したように表示してはならない。G6にある「実人間によるレビュー過程」は依然必須であり、AI自己点検では代替できない。

## 現在のPR候補と公開停止

- main read-back: `f2e27950de50a497ca48351b985d60a0eb0a517a`。
- PR [#66](https://github.com/Unjuno/openpreprint-kit/pull/66) はOPEN・未merge。最新読戻しhead `a8880b8e3e7988369d7f49328c7b0c8c7770e98f`。必須CI7カテゴリ、self-application、live RFC3161/fresh-runnerがsuccess。明示merge承認待ち。
- Candidate ZIPはローカルGold packageで管理し、既存ZIPを履歴として保持する。現在の再確認メモは `outputs/ACCEPTANCE_RECHECK_2026-11-22.md`、そのSHA-256は `c0eec79856651df3ca95c913629f315dbcbdade8a2113ec25836f885bfc06cec`。Issue #5 comment: https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-7064783145。
- GitHub secret名 `OPK_ADMIN_READ_TOKEN` は存在するが、値・有効性・実効scopeは読まず未確認。機密値は検査・記録しない。
- toolkit software Release数は0。正式なv1.0.0 Release/tagは作成しない。

PR merge後は新main SHAで全必須CI、self-application、必要な署名・TSA・匿名取得・offline restore証拠を再固定する。G1/G2の第二repoの解決とG6の人間実施記録が揃い、全ゲートが正式基準でPASSし、所有者の最終発行承認が明示されるまでP4はNO-GO。

## Releaseフローに関する注意

個別プレプリント用 `.github/workflows/publish.yml` はkit本体のソフトウェアReleaseではない。root `preprint.yaml` は再利用テンプレートとして `v0` / `UNSPECIFIED` のまま維持する。kit v1.0.0は、全ゲートと最終承認後、固定main SHAからソースアーカイブ、SHA256SUMS、Readiness、Master Reportを組み立て、attestation・匿名取得・byte一致・immutableを確認して発行する。

## 訂正履歴

- 2026-11-14: 公開Release後のER-1〜ER-3を `evidence/acceptance/erratum-2026-11-15-public-releases.md` に記録。immutable assetは変更していない。
- 2026-11-22: 第2repoが現行GitHub一覧・APIで解決できないこと、G6原証拠が不明であることをライブ読戻しに基づき追記。過去のG1/G2 PASSを現状PASSに転記しないよう訂正。
