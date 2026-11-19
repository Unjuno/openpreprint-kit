# OpenPreprint Kit — 技術監査報告 2026-11-18 Cycle 5

## 1. 監査範囲と結果

対象: `.github/workflows/*.yml` 全9ファイル、`scripts/publish_first_paper.sh`、`tests/test_workflows.py`。
**発見した欠陥: 0件**（再現可能な欠陥なし）。

根拠:
- `pull_request_target` / `workflow_run` の使用: 0件。公開系は `workflow_dispatch` のみ。
- `${{ ... }}` の `run:` スクリプト内への補間: 0件（全38箇所は name/path/env/with/outputs）。`test_workflows.py:59-67` が强制执行。
- secretsは `workflow_dispatch` ワークフローのみ（`OPK_ADMIN_READ_TOKEN`, `github.token`）。全 checkout で `persist-credentials: false`。
- 全 `uses:` が40-hex固定。GitHub APIで実コミットと解決し、バージョンコメントも一致。
- `actionlint v1.7.7`:  finding 0。PyYAML重複キー検査: 異常なし。
- 公開順序（引用検証→TSA→draft→再取得検証→公開）は `test_workflows.py:28-45` で固定。
- `bash -n` による launcherscript 検証、引数解析の実行テスト: すべて正常。

判断を保留した項目（欠陥ではない）:
- `publish.yml` の immutable 読戻しが公開後に行われる点は `docs/OPERATIONS.md` で明示された設計。GitHubに原子的「immutableなら公開」APIが無く、最小修正が存在しない。
- `publish_first_paper.sh` は POSIX ではなく既存Linux利用者向けの保持物。portable な entry point は Python ランチャーであり、CIもそちらを試験する。

## 2. 現状（Step 1 再確認）

- main `811dc843...` 不変、PR #51 draft/OPEN、CodeQL open alerts 0。
- 公開4版は immutable/draft=false/11資産で変更なし。
- 最新PR head `4b777a8442adb2362b3d7dab7ad0b998e9830a57` で CI 全5ワークフロー success。
  内 `portable-smoke (macos-15)` も success（run `44126039717`、jobs: macos/ubuntu/windows すべて success）。
- 全 unittest は Windows/Ubuntu のみ設定。macOS の全 unittest は UNKNOWN。
- 全試験: 403 tests / 15 skips / OK（Windows 3.12）。
- 形式検証: Lean 4.35.0 32定理、差分 33/33 MATCH（再実行）。

## 3. 未達

macOS 全unittest 未設定、G4/G5/G7 独立検証未実施、G0〜G3/G6 PARTIAL → P4 NO-GO 維持。
利用者側で必要なもの: (a) macOS runner での全unittest実行、(b) 独立レビュー担当者の選任と署名。
