# Erratum — 公開済み4版に関する訂正記録（2026-11-15）

**公開済み不変Asset・Releaseは変更していない。** 以下は、公開後に確認された事実と訂正で、新しい版でしか正式反映されないもの。

## ER-1: paper A v2 — 解析コードの集計ラベル誤り（非機密・データ誤り）

`manuscripts/openpreprint-kit-v2/analysis/summarize_releases.py` は `attestation_verified_releases = len(tsa)`（=8）を出力していたが、これは
**attestation の検証件数ではなく、TSA 再検証8件**（demo 4版 × bundle/anonymous 各1件）である。
匿名DL→attestation（`gh release verify` / `verify-asset`）の実測記録は CI・Issue #5 および本リポジトリ外の証拠台帳にあり、
公開済み本文の主張「全資産 attestation VERIFIED」は別の手順で裏付けられている。対して、解析コードが誤ったキー名で集計していたという事実は本ERRATUMで記録する。

本リポジトリの作業ツリーでは修正済み（`tsa_reverify_passes`）として統合し、公開済み release A v2 は変更しない。

## ER-2: paper B v2 — 再現手順のプレースホルダ

`manuscripts/openpreprint-kit-robustness-eval/v2/paper.md` の §再現 は `python <this dir>/analysis/...` という placeholder だった。
本リポジトリの作業ツリーでは `analysis/reverify_v2.py` と `renewal.py issue ...` の実コマンドに修正済み。公開済み B v2 は変更しない。

## ER-3: 公開ランナーの pre-flight 順序（安全性欠陥、修正済み）

`scripts/publish_manuscript.py` はステージング→資産整合確認→公開書込み→bundle 構築（`prepare_release.py` 厳密検証）の順だった。
公開コミット後に未承認/未宣言資産が拒否される可能性があった。修正: bundle 構築と引用検証を公開書込みより前に移動し、
不正入力で一度も GitHub API/コマンドを呼ばないことを回帰テストで固定（`tests/test_publish_manuscript_preflight.py`）。
**過去の公開実行（paper A v2/B v1/B v2）で未承認資産が混入した形跡はない**（当該公開では全ファイルが `research-assets.yaml` 宣言済み・`public_confirmed: true` を満たし、leakscan で秘密情報なしを確認）。

## ER-4: 論文リポジトリの branch protection 未設定

`openpreprint-kit-paper` / `openpreprint-kit-robustness-eval` は `protected=false`（作為的な公開後）。
事後設定は「公開前保護」の証明にはできない。所有者承認の下で設定し、API 読戻しで確認する。

## ER-5: 依存関係・監査の記録

- CodeQL open alerts = 0（main `e164021ec4d75330a500d861e22fb799024d7f3a`、PR #44 マージ直後）
- Dependabot alerts = 0（owner 承認で有効化、2026-11-14）
- pip-audit 0 件（requirements.lock 22 deps）
- Windows 上の unittest discover は 14 ERROR + 3 FAIL（symlink/POSIX権限/改行コード、試験環境依存; CI Linux は 372/372 PASS、PR #40 時点）

## 備考

- 公開Releaseの v1/v2 を上書き・削除・再作成していない。既存証拠（publication-report.json / continuation-report.json / FAIL記録）はそのまま保持。
- 本文の数値主張（"5 releases" など）は、証拠台帳と実測レコードに基づく。ER-1/ER-2 のみがコード/本文の誤り。
