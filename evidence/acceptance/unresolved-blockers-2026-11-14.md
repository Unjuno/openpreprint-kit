# 未達項目と責任者（ブロッカー台帳、2026-11-14 / main `84ca91cd`）

判定: **P4 = NO-GO**。以下が未達。G0〜G7 を全て解消するまで v1.0.0 完成とは宣言しない。

| # | ゲート | ブロッカー | 種別 | 必要な人・権限 | 現状 |
|---|---|---|---|---|---|
| B1 | G0 | レビュー担当の独立承認（CodeQL 0件・pip-audit 0件の読み・承認） | 人間 | レビュー担当（owner 以外が望ましい） | 未了。AI自己評価不可 |
| B2 | G0 | Dependabot alerts 無効（403）の扱い: 有効化 or 代替脆弱性評価の採用記録 | 権限・判断 | owner | **RESOLVED 2026-11-14: owner 承認で有効化（PUT vulnerability-alerts → 204、open alerts=0）** |
| B3 | G1 | Required approvals=0 の独立人間レビューとしての妥当性承認、またはレビュアー追加 | 人間 | owner or 独立レビュアー | 未了 |
| B4 | G1 | paper/demo リポジトリへの branch protection 適用の要否判断（テンプレート repo 同等の保護を求めるか） | 判断 | owner | 未了（現状 rules なし） |
| B5 | G2 | **基準と実態の不一致**: 正式「2論文repo各2版」vs 現状（paper v1 のみ + synthetic 2 repo 各 v1/v2） | 基準・執筆 | owner（A案: paper v2 執筆/第2原稿、B案: 基準変更の署名付き承認） | owner 未決定（g2-criterion-impact-2026-11-14.md） |
| B6 | G2 | 発行者と別の検証担当による最終 PASS 判定 | 人間 | 検証担当（owner 以外が望ましい） | 未了 |
| B7 | G3 | TSA運用担当による信頼選定・CRL 運用の承認 | 人間 | TSA運用担当 | 未了 |
| B8 | G3 | 検証担当による G3 最終 PASS 判定 | 人間 | 検証担当 | 未了（技術証拠は揃う） |
| B9 | G4 | 独立観測者の選任・4版匿名取得・署名・RFC 3161・鍵指紋別経路確認 | 人間（別管理鍵・環境） | 観測者（著者と非同一管理・非同一環境・別鍵） | 不在（owner確認）。パッケージ完成: docs/operator-packages/G4-independent-observer.md |
| B10 | G5 | 別管理保管者の受領・SHA-256再計算・保管記録 | 人間 | 保管者（別アカウント/組織） | 不在（owner確認）。CUSTODY_LEDGER.json/HANDOVER.md 完成・未保管 |
| B11 | G5 | 別管理 GitHub 不変ミラーへ4版保存・4版オフライン復元（GitHub非接続新環境） | 人間（別管理アカウント） | 保管者 + owner | 未了 |
| B12 | G6 | 本文/データの権利・公開同意・COI・著者表示/ライセンスの人間確認 | 人間 | 編集・プライバシー担当 | 部分的（文書のみ、本人確認ではない） |
| B13 | G6 | 実人間によるレビュー過程1件・訂正演習1件・撤回演習1件の実施・記録（版/履歴保持） | 人間 | 編集担当 | 未了。テンプレート完成: docs/operator-packages/G6-human-review.md |
| B14 | G7 | 外部セキュリティ/プライバシー監査（固定SHA `3e4d373c…`・サプライチェーン・権限・不変性・失効/更新/復旧試験・保守責任）と**署名付き報告** | 人間（外部） | 外部監査者 | 未了。監査パッケージ完成: docs/operator-packages/G7-external-audit.md |
| B15 | G7 | 証明書期限切れ・失効・CA更新・証拠更新・旧失効証拠保存・GitHub障害復旧の**実測試験**と責任者確定（renewal の合成試験はCI済みだが実効試験ではない） | 人間・実測 | 監査者/TSA運用担当 | 部分（合成試験のみ） |
| B16 | P4 | キット本体 `v1.0.0` 不変Release の発行と公開後再検証 | 権限+承認 | owner（G0〜G7全PASS後） | **NO-GO（前提未達）** |

## 確認できている技術的証拠（人間承認を要しない範囲）
- main CI 全成功（Validate 3.10/3.12 367/367・Quality/audit・CodeQL・self-application・portable smoke・live-acceptance Ubuntu）。main `3e4d373c…`。
- 5 Release 全て: immutable・attestation VERIFIED・匿名DL byte一致・offline integrity PASS・TSA PASS。
- 20否定ケース誤受理0（spec 固定・再照合一致）。
- CodeQL 0 open alerts・pip-audit 0 vuln・Actions SHA固定・依存ハッシュロック。
- R04/R05 完了（synthetic、owner承認）。

## 所有者が依頼すべき最小作業（人間）
1. 観測者・保管者・編集担当・外部監査者・検証担当を選任する（B9〜B14）
2. G2 基準の A案/B案を選択・署名付きで記録する（B5）
3. G2/G3/G0 の最終判定を実行者と別の担当者が署名する（B1/B6/B8）
4. （B案選択時）V1_ACCEPTANCE.md G2 の変更 PR を承認する
5. （A案選択時）paper v2 または第2原稿の執筆・承認・公開

これらが Issue #5 に記録され、G0〜G7 が全 PASS になり、main 固定SHA の必須CIが成功し、v1.0.0 不変Release が発行・再検証されるまで、**OpenPreprint Kit v1.0.0 完成とは宣言できない**。
