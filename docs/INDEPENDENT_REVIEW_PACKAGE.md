# 受入パッケージ（所有者判定方式 / 2026-11-21 緩和後）

作成日: 2026-11-18。改訂: 2026-11-21（所有者承認による緩和）。
用途: 所有者が G0〜G7 の受入判定を行い、v1.0.0 公開判断に必要な証拠を固定するための資料。
**独立人間の選任・署名は必須ではない（[ACCEPTANCE_RELAXATION_2026-11-21.md](ACCEPTANCE_RELAXATION_2026-11-21.md)）。独立性が証明されていないゲートは `独立性=UNPROVEN` と明示し、架空のレビュアー・署名・別アカウントによる擬装は行わない。**

## 1. 対象と固定値

| 項目 | 値 |
|---|---|
| 現在の main | `5cd621e5be001f106260541a8cd303c3d6f1c750` |
| 技術検証の基準 SHA | `afbd55b475b7b583bc319a0f76c3555f0539b5fa`（PR #51 マージ後のコード完成点） |
| 直近の必須 CI | main `5cd621e5` で validate 3.10/3.12・Quality audit/Windows/macOS・CodeQL Python・Lean・portable smoke すべて success |
| tree hash（基準 SHA） | `dfb0256d628c7dbc30ec8298536e20b9c070b41b` |
| source zip SHA-256（基準 SHA） | `9af1e73b7b3580ec864ca3564c043b368a48da6e7b34e337376d6a1abd919452` |
| 旧スナップショット（履歴保持） | tree hash `a8a2747e994a7763cca2ba3e4664d2cbdd659b2f` / source zip `3bef7dc8f4e6351fde3c0bfb8de2826e9c75162311882179b4c619b7788e89c5` |
| 受入基準 | [V1_ACCEPTANCE.md](V1_ACCEPTANCE.md)（2026-11-21 緩和版） |
| 技術記録 | [TECHNICAL_ACCEPTANCE.md](../TECHNICAL_ACCEPTANCE.md), [TECHNICAL_AUDIT_2026-11-19.md](TECHNICAL_AUDIT_2026-11-19.md) |

## 2. 判定者

| ゲート | 判定者 | 独立性 |
|---|---|---|
| G0〜G7 | 所有者 | UNPROVEN（独立人間レビューは未実施） |

AI 自己点検や別アカウントの作成は独立レビューに計上しない。将来、実在する別人間がレビューを行った場合のみ `独立性=VERIFIED` と記録する。

## 3. 各ゲートの確認項目（所有者が原証拠を確認）

- [x] G0: 基準 SHA で Validate 3.10/3.12・Quality(Ubuntu/Windows/macOS)・CodeQL・Lean の原ログを確認。重大・高リスク未解決 0。
- [x] G1: テンプレート有効、2 論文 repo の immutable/branch protection/必須CI を読戻し。
- [x] G2: 4 版の Release ID/URL/版/ソースSHA、全 11 資産の attestation、匿名DL byte一致、v2 後も v1 不変を確認。
- [x] G3: 別途選定した CA/CRL/policy で全 4 版を再検証。2 環境 8 回以上、20 不正ケース誤受理 0。
- [x] G4: 4 版の匿名取得記録、Ed25519 署名記録、RFC3161 証拠を確認。**独立性は UNPROVEN**。
- [x] G5: ミラーURL、台帳/ハッシュの別経路保管、GitHub 非接続 4 版復元ログを確認。**管理分離は UNPROVEN**。
- [x] G6: ライセンス/公開同意/COI、実人間のレビュー1件・訂正演習・撤回演習を確認。
- [x] G7: 固定 SHA へのセキュリティ評価、失効/CA更新/復旧の試験、責任者と継続点検手順を確認。**外部監査ではない（UNPROVEN）**。

## 4. 証拠の記録形式

`gate_id`, 対象repo/tag/commit, 実行環境, operator, 独立性の根拠, expected/actual, 実通信かmockか, verdict, observed_at_utc, 証拠URIとsha256, reviewer, checked_at_utc を記録する。未取得値は `null` / `UNKNOWN` とし、推測で埋めない。

## 5. 判定と出荷

- 全ゲートの証拠と所有者の確認が揃い、所有者の最終承認があれば P4 の公開判断を行える。
- 独立性 UNPROVEN の事実を公開物の説明に残す。
- 過去の FAIL（例: `44028158017`, `44028158061`）は削除・上書きせず履歴として残す。

## 6. 現状（2026-11-21）

技術的証拠と全ゲートの確認は揃っている。独立人間レビューは未実施だが必須ではなくなった。
v1.0.0 の発行は所有者の最終承認があれば実行可能（本ファイル自体は発行を行わない）。
