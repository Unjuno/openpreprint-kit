# OpenPreprint Kit — 技術監査報告 2026-11-18 Cycle 6

## 1. 今回の対応

### 解決: macOS 全 unittest 未設定（UNKNOWN → PASS）
- `quality.yml` に `macos-regression (3.12)` を追加。hash固定lock（3本）+ Homebrew OpenSSL 3 をPATHに設定。
- 初回 run `44169617220` は **FAIL**: `test_operation_guards` が `timeout-minutes: 25 > 15` を検出（既存ガードが機能した）。この FAIL は削除せず保持。
- `timeout-minutes: 15` に修正後、run `44172420938` で **macos-regression success**。
  原ログ: `OpenSSL 3.5.9 29 Sep 2026` / `Ran 403 tests in 103.711s` / `OK (skipped=3)`。
- 同 run で `audit`, `windows-regression` も success。最新SHA `695b232` で CI 全5ワークフロー success。

### 負の結果（前cycle）
- ワークフロー／POSIXランチャー監査: 実証可能な欠陥 0件（`docs/TECHNICAL_AUDIT_2026-11-18-CYCLE5.md`）。

## 2. 現状

- main `811dc843...` 不変、PR #51 draft/OPEN、CodeQL open alerts 0。
- 公開4版 immutable・draft=false・11資産で変更なし。
- OS 別試験: Windows（403 tests / 15 skips）、Ubuntu（403 / 3 skips）、macOS（403 / 3 skips）、Python 3.10 は Validate job。
- Lean 4.35.0 32定理、差分 33/33 MATCH。証拠ハッシュ台帳整合。

## 3. 未達

独立レビュー（G0〜G7 の署名入り受入）は未実施。TQ-7/TQ-8 UNKNOWN、G4/G5/G7 BLOCKED、P4 NO-GO 維持。
利用者側の手配が必要: 独立レビュー担当者（観測者・保管者・監査者を含む）の選任と署名。
