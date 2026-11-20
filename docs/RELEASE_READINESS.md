# OpenPreprint Kit — 現在の受入状態

更新日: **2026-11-21 JST**。記録時の基準コミット: `5cd621e5be001f106260541a8cd303c3d6f1c750`（最新 main は GitHub で確認）。

**第1論文v1 (P1) は正式公開済み。正式4版（2実論文repo×各2版）も公開・再検証済み。キットv1.0.0 (P4) は、2026-11-21 の受入基準緩和により所有者の最終承認で公開判断が可能。**
独立性は `UNPROVEN`（独立人間レビューは未実施）。ソフトウェアの試験合格を、第三者監査・長期保存の証明と混同しない。緩和の詳細は [ACCEPTANCE_RELAXATION_2026-11-21.md](ACCEPTANCE_RELAXATION_2026-11-21.md)。

基準: [V1_ACCEPTANCE.md](V1_ACCEPTANCE.md) (G0–G7)。工程: [ROADMAP.md](ROADMAP.md)。完了台帳: [Issue #5](https://github.com/Unjuno/openpreprint-kit/issues/5)。過去のスナップショット [2026-11-13 manual status](../evidence/acceptance/release-status.json) は履歴としてのみ参照し、現在の判定には用いない。

## 実公開リリース（2026-11-14）

| # | Repository | Release | Release ID / タグ SHA | 公開時刻 | Immutable |
|---|---|---|---|---|---|
| 1 | [openpreprint-kit-paper](https://github.com/Unjuno/openpreprint-kit-paper) | **v1**（承認済み本短報、変更禁止） | 444659219 / `804cb76a4cf5eea65349fc7a8f01e2ce00e1176d` | 2026-11-13T19:39:48Z | ✓ |
| 2 | openpreprint-kit-paper | **v2**（実運用評価、AI支援執筆・所有者承認） | RE_kwDOVtdYwc4ajOkk / `6ec47ec58e9dc733956615343aad16caca4bb8ee` | 2026-11-14T16:48:30Z | ✓ |
| 3 | [openpreprint-kit-robustness-eval](https://github.com/Unjuno/openpreprint-kit-robustness-eval) | **v1**（改変検出の実証評価） | RE_kwDOVubJxs4ajPQ0 / `940bd77d02318e9d95fa5cb7db568804de2d1860` | 2026-11-14T16:53:04Z | ✓ |
| 4 | openpreprint-kit-robustness-eval | **v2**（追加実験: CRL鮮度対照・前方TSA更新） | RE_kwDOVubJxs4ajPhz / `2631782a109bf47572e4310ae0da32f26aec3de9` | 2026-11-14T16:54:53Z | ✓ |

- 各Releaseの全11資産の attestation（`gh release verify` / `verify-asset` ×11）・匿名DL byte一致・オフライン復元・TSA再検証は再実測済み。
- 論文 repo は事後的に branch protection を設定（deletion/force-push禁止、PR必須、必須 checks `validate (3.12)/(3.10)/audit`, strict=true）。事後設定は公開前保護の証明ではない。
- 第1論文専用ランナーの初回失敗（cffconvert PATH）は owner 承認後の同一コード経路継続で完了。FAIL 記録は保持。
- `publish_manuscript.py`（汎用ランナー）を PR #42 で統合。pre-flight 順序欠陥を PR #45 で修正。回帰テスト分離を PR #46 で完了。

## G0–G7 の判定（2026-11-21 緩和基準、所有者確認＋実測証拠）

| ゲート | 判定 | 残る証拠・形
|---|---|---|
| G0 コード・配布品質 | PASS（独立性 UNPROVEN） | main CI 全成功（Validate 3.10/3.12・Quality/audit/CodeQL・Lean・Windows/macOS regression・portable smoke）。Actions SHA固定、依存ハッシュロック、CodeQL 0 alerts、重大・高リスク未解決0 |
| G1 所有者設定・再利用 | PASS（独立性 UNPROVEN） | 2つの論文 repo（paper / robustness-eval）＋ toolkit template を読戻し。Immutable=true、branch protection 設定済み。Required approvals=0 は所有者選択 |
| G2 実公開・版管理 | PASS（独立性 UNPROVEN） | 正式4版公開・attestation・匿名DL一致・v2後もv1不変を実証 |
| G3 TSA・否定試験 | PASS（独立性 UNPROVEN） | 5版のRFC 3161再検証 PASS、2環境8回以上の正常検証、固定20否定ケース誤受理0 |
| G4 公開観測 | PASS（独立性 UNPROVEN） | 観測記録・署名・RFC 3161 を確認。独立観測者ではないことを明示 |
| G5 複製・オフライン復元 | PASS（独立性 UNPROVEN） | GitHub非接続4版復元ログ・台帳を確認。別管理保管者ではないことを明示 |
| G6 人間の編集・個人情報管理 | PASS | ライセンス分離、権利/COI確認、レビュー1件・訂正/撤回演習を記録 |
| G7 セキュリティ・証拠寿命 | PASS（独立性 UNPROVEN） | 固定SHAへの評価、失効/CA更新/復旧の試験、責任者と継続点検手順を確認。外部監査ではないことを明示 |

**P1 PASS。P2（G2）PASS。P3 PASS（独立性 UNPROVEN）。P4 は全ゲート PASS／独立性 UNPROVEN の明示付きで、所有者の最終承認により公開判断可能。**

## 残る作業

1. 所有者による最終承認（v1.0.0 を出すかどうかの意思決定）
2. 承認後に、キット本体 `v1.0.0` 不変 Release の発行と全資産の再取得検証
3. 独立性 UNPROVEN の事実を公開物の説明に残す（将来、実在する独立人間がレビューした場合のみ VERIFIED に更新）

独立人間の選任は 2026-11-21 の緩和により必須ではなくなった。架空のレビュアー・署名・別アカウントによる擬装は行わない。

## 文書の訂正履歴

- 2026-11-14: paper A v2 公開後の ER-1（解析集計ラベル誤り）・ER-2（B v2再現手順）・ER-3（ランナー pre-flight 順序欠陥）は `evidence/acceptance/erratum-2026-11-15-public-releases.md` に記録。公開済み asset は変更せず。
