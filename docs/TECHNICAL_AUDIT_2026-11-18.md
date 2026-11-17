# OpenPreprint Kit — 技術監査報告 2026-11-18 (継続サイクル3)

対象: PR #51 ブランチ `hardening/formal-verification-20261117` / 基準 main `811dc84367c88a81dbf062fa5d262f5d10a41180`
前回: [TECHNICAL_AUDIT_2026-11-17.md](TECHNICAL_AUDIT_2026-11-17.md)

## 1. Step 1 現状確認（古いログを流用せず再読）

- main は `811dc84` のまま（PR #51 は draft / OPEN、未マージ）
- 最新 CI: PR head `3bce2b9` で Validate(3.10/3.12)・Quality(Ubuntu/Windows)・CodeQL が success
- CodeQL open alerts 0、公開4版はすべて `draft=false immutable=true` 11資産（変更なし）
- Issue #5 / #3 は open のまま

## 2. 今回発見した欠陥（すべて再現実行済み）

| ID | 深刻度 | 箇所 | 原因分析 | 影響 | 修正 | 回帰試験 |
|---|---|---|---|---|---|---|
| AUD-10 | **高** | `commitment_history.py:18-19` | all-zero baseline を「最初のコミット」として無条件 `[]` を返し、git コマンドを1つも実行せず PASS | 信頼できる baseline 供給側が失敗・誤設定で0を渡すと、匿名 commitment の追加専用保証が**完全に無効化**される | all-zero を明示的エラーに変更（CI側は既に0を渡さない。validate.yml で確認済み） | `test_all_zero_baseline_is_rejected` |
| AUD-11 | **高** | `commitment_history.py:23-38` | `git diff base HEAD` の**端点ネット差分**しか見ていない。改変→復元の2コミットはネット差分0で PASS | 通常のコミット権限で受領書を改変・復元でき、CIは追加専用不変条件が保たれたと誤判定（誤 PASS） | `git log base..HEAD -- evidence/commitments` で全コミットを列挙し、各コミットの `diff-tree -m` で `A` 以外を拒否（マージコミットも対象） | `test_tamper_then_restore_is_rejected`（ネット差分が空であることも同時に実証）, `test_tampered_receipt_merged_from_side_branch_is_rejected` |
| AUD-12 | 中 | `research_record.py:50,169` | 深くネストした JSON が `RecursionError` を送出。これは `RuntimeError` の派生で `except (OSError, ValueError, TypeError, KeyError)` に捕捉されない | 約6KBの入力でプロセスが未処理 traceback 終了。CIが不定失敗し、パス/環境情報を漏らす可能性 | `RecursionError` を捕捉 tuple に追加し、常に `FAIL` を返す | `test_deeply_nested_json_fails_cleanly` |
| AUD-13 | 中 | `first_paper_selftest.py:83-103` | `Path.absolute()` は `..` と symlink 祖先を正規化しないため、`is_relative_to()` のテキスト比較を迂回して出力先が検証済み bundle 内に解決される | `copytree(bundle, bundle内)` が自己再帰し、検証済み成果物を汚染 + ディスク/パス枯渇 | `resolve()` で正規化、workspace と rename 直前にも再チェック | `test_export_candidate_resolves_dotdot` |

再現・修正・回帰は [tests/test_hardening_regressions_iter3.py](../tests/test_hardening_regressions_iter3.py) に集約（4件）。
**未解決の重大・高リスク欠陥は 0。**

## 3. Step 4 形式検証との整合（保存ログを流用せず再実行）

- Lean 4.35.0 ビルド成功、`sorry/admit/axiom` なし
- 差分ベクトルを 28 → **33** に拡張。新規 ST-09〜13 で `verified→published`、強制更新ブロック、published 終端、checked 不一致/欠落を照合
- Python 側は本番 `preflight.preflight()` を直接呼び、公開遷移は `publish_manuscript.execute()` の検証順序を再表現したアダプタで照合
- 結果: **33/33 MATCH**（`formal/VERIFICATION_RESULTS.txt`）
- 暗号学的性質・OS/API 挙動は引き続き未証明（モデル外）

## 4. Step 5 証拠

- 全試験: **399 tests / 15 skips / OK**（Windows / Python 3.12 / OpenSSL 3.5.0、原ログは CI artifact とローカル実行で取得）
- 回帰: 既存9件 + 今回5件 = 14件すべて PASS
- 旧 FAIL（`44028158017`, `44028158061`）は削除せず前回報告に保持
