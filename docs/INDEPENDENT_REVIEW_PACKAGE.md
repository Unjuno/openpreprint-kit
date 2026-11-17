# 独立レビュー受入パッケージ（提出用テンプレート）

作成日: 2026-11-18
用途: 所有者が**独立した人間**を選任し、G0〜G7 の受入判定を行わせるための提出資料。
**本ファイルは提出の準備物であり、審査・署名・PASS判定を代行しない。AI自己検証は独立レビューとして計上しない。**

## 1. 対象と固定値

| 項目 | 値 |
|---|---|
| 正式 main | `811dc84367c88a81dbf062fa5d262f5d10a41180` |
| 提案ブランチ / PR | `hardening/formal-verification-20261117` / [Draft PR #51](https://github.com/Unjuno/openpreprint-kit/pull/51) |
| 直近コード検証済みSHA | `e3c5f68da1efac54937d0615adb4307dd0bfd63b`（Validate/Quality/CodeQL/selftest success、Ubuntu/Windows） |
| 現在のPR head | `e3c5f68da1efac54937d0615adb4307dd0bfd63b`（ドキュメント更新のみの commit が後続する場合あり） |
| tree hash | `a8a2747e994a7763cca2ba3e4664d2cbdd659b2f` |
| source zip SHA-256 | `3bef7dc8f4e6351fde3c0bfb8de2826e9c75162311882179b4c619b7788e89c5` |
| 受入基準 | [V1_ACCEPTANCE.md](V1_ACCEPTANCE.md)（緩和・置換禁止） |
| 技術記録 | [TECHNICAL_ACCEPTANCE.md](../TECHNICAL_ACCEPTANCE.md), [TECHNICAL_AUDIT_2026-11-17.md](TECHNICAL_AUDIT_2026-11-17.md), [TECHNICAL_AUDIT_2026-11-18.md](TECHNICAL_AUDIT_2026-11-18.md) |

## 2. レビュー担当者の選任（所有者が記入）

| ゲート | 要求される独立性 | 担当者名 | 選任日 | 署名 |
|---|---|---|---|---|
| G0 コード・配布品質 | 開発者と別のレビュー担当 | — 未選任 — | | |
| G1 所有者設定 | 各リポジトリ所有者 | — 未選任 — | | |
| G2 実公開・版管理 | 発行者と別の検証担当 | — 未選任 — | | |
| G3 TSA・否定試験 | TSA運用担当＋検証担当 | — 未選任 — | | |
| G4 独立公開観測 | 著者と別の環境・秘密鍵の観測者 | — 未選任 — | | |
| G5 複製・オフライン復元 | 別管理の保管者 | — 未選任 — | | |
| G6 人間編集 | 著者・編集・プライバシー担当 | — 未選任 — | | |
| G7 外部監査 | 実装者と別の監査者 | — 未選任 — | | |

同一人物の別GitHubアカウント、およびAI自己評価は独立人間として計上しない（V1_ACCEPTANCE §5）。

## 3. 各ゲートの確認項目（レビュー担当者が原証拠を確認）

- [ ] G0: 対象SHAで Validate 3.10/3.12・Quality( Ubuntu/Windows )・CodeQL・selftest の原ログを確認。CodeQL警告0をトリアージ。重大・高リスク未解決0を独立確認。
- [ ] G1: テンプレート有効、2論文repoの immutable/branch protection/必須CI/人間レビューを読戻し。
- [ ] G2: 4版の Release ID/URL/版/ソースSHA、全11資産の attestation、匿名DL byte一致、v2後もv1不変を発行者以外が確認。
- [ ] G3: 別途選定した CA/CRL/policy で全4版を再検証。2環境8回以上、20不正ケース誤受理0。
- [ ] G4: 独立観測者の Ed25519 鍵指紋、署名記録、RFC3161、観測者の独立性申告を確認。
- [ ] G5: 別管理ミラーURL、台帳/ハッシュの別経路保管、GitHub非接続4版復元ログを確認。
- [ ] G6: ライセンス/公開同意/COI、実人間のレビュー1件・訂正演習・撤回演習を確認。
- [ ] G7: 固定SHAへの外部監査報告、失効/CA更新/復旧の実測、責任者と継続点検手順を確認。
- [ ] 未検証OS（macOS）の扱い: portable smoke は最新 run `44126039717` で macos-15 success。ただし全 unittest は Ubuntu/Windows のみ → **UNKNOWN**。macOS で全 unittest が成功するまで PASS にしない。過去の cancelled run `44116478457`, `44122897522` は履歴として保持。

## 4. 証拠の記録形式（各ゲート）

V1_ACCEPTANCE §5 に従い次を記録: `gate_id`, 対象repo/tag/commit, 実行環境, operator, 独立性の根拠, expected/actual, 実通信かmockか, verdict, observed_at_utc, 証拠URIとsha256, reviewer, checked_at_utc。
未取得値は `null` / `UNKNOWN` とし、推測で埋めない。

## 5. 判定と出荷

- いずれかのゲートが未達なら P4 は **NO-GO** を維持。
- 全ゲートPASS＋所有者の最終承認が得られた場合に限り、固定SHAから v1.0.0 不変Releaseを発行し、全資産を再取得・照合する。
- 過去のFAIL（例: `44028158017`, `44028158061`）は削除・上書きせず履歴として残す。

## 6. 現状（2026-11-18）

独立レビューは**未実施**。全ゲートの reviewer 欄は空。macOS portable smoke は PASS だが全 unittest は UNKNOWN。
したがって本パッケージは「提出準備完了」を意味し、「受入完了」を意味しない。
