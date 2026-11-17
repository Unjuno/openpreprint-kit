# OpenPreprint Kit — 技術監査報告 2026-11-18 Cycle 4

## 1. 発見した欠陥（すべて再現実行済み）

| ID | 深刻度 | 箇所 | 原因分析 | 影響 | 修正 | 回帰試験 |
|---|---|---|---|---|---|---|
| AUD-14 | **高** | `prepare_release.py:76-91` | `validate()` の判定と別途 `preprint.yaml` を再読し、その `paper` 値で `copyfile` していた（TOCTOU）。検証結果が実使用データに束縛されていない | リポジトリ書込み権限者が競合で任意のローカルファイルを公開バンドルへ混入（機密漏えい） | `validate(return_data=True)` が検証済み metadata を返し、そのまま利用。copy 直前にも `paper` の containment/suffix/symlink を再検証 | `test_raced_metadata_cannot_leak_outside_file` |
| AUD-15 | **高** | `pdf_validation.py:18-22,62-70` | PDF 2.0 の関連ファイル `/AF`→`/Filespec`→`/EF` が拒否キーになく、キー走査だけでは検出不可 | 埋め込みペイロード入り PDF が公開ゲートを通過（誤PASS） | `REJECT_KEYS` に `/AF`,`/EF`,`/Filespec` を追加 | `test_pdf_af_embedded_file_is_rejected` |
| AUD-16 | **高** | `pdf_validation.py:62-70` | `/Launch` 等は辞書キーではなく `/S` や `/Subtype` の**値**。注釈 `/A << /S /Launch ... >>` に検出ロジックが及ばない | 起動アクション付き PDF が公開ゲートを通過（誤PASS） | `NameObject` 値 `/S`,`/Subtype` を `REJECT_NAMES` で検査 | `test_pdf_annotation_launch_action_is_rejected` |
| AUD-17 | 中 | `private_seal.py:313-317` | `verify()` が `read_bytes()` で鍵ファイル全体を-materialize してから長さ検査 | 巨大/スパースな鍵で 100MiB+ 確保 → OOM/DoS | stat で 32バイト確認 + `read(33)` の境界付き読取り。受領書も `read(4097)` に変更 | `test_oversized_key_is_bounded` |

**未解決の重大・高リスク欠陥は 0。** 回帰試験は [tests/test_hardening_regressions_iter4.py](../tests/test_hardening_regressions_iter4.py)（4件）。

## 2. 検証

- 全試験: **403 tests / 15 skips / OK**
- 形式検証: Lean 4.35.0 ビルド成功、差分 33/33 MATCH（再実行）
- 既知の旧FAILは保持。macOS portable smoke は run `44119821885` で success（全 unittest は未設定のため UNKNOWN）
