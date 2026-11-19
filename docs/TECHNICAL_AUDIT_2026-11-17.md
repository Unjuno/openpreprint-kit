# OpenPreprint Kit — 技術監査報告 2026-11-17

対象SHA: `811dc84367c88a81dbf062fa5d262f5d10a41180`
受入基準: [V1_ACCEPTANCE.md](V1_ACCEPTANCE.md) (緩和・置換していない)
作業ブランチ: `hardening/formal-verification-20261117` (固定 main への統合は未実施。PR提案待ち)

## 1. 監査範囲と方法

- 固定 main と公開済み4 Release を `gh api` 読取り専用で再確認 ([REPOSITORY_MAP.md](../REPOSITORY_MAP.md))。
- 试验: Windows / Python 3.12.10 / OpenSSL 3.5.0 (`C:\msys64\ucrt64\bin`)。
- 基线: 378 试验 / 15 skip (元のまま)。修復後: **393 试验 / 15 skip / 全 PASS**。
- CI: 固定SHAで `Validate (3.10/3.12)`, `Quality/audit`, `CodeQL`, `first-paper-selftest`, `portable-first-paper` が success。
  CodeQL open alerts = 0。Run例: `43832249370`, `43832249377`, `43832249420`。
- 监査手法: 3並列エージェントによる信頼境界の精読 + 実行可能な再現 + Hypothesis 特性試験 + Lean 形式モデルとの差分。

## 2. 信頼境界の洗い出し

| 境界 | 実装 | 検証していること | 検証していないこと |
|---|---|---|---|
| 公開前検証 | `preflight.py`, `publish_manuscript.py` | repo公開性・immutable設定・HEAD固定・tag空き | API応答の真正性、設定の原子的ロック |
| 公開処理 | `publish_manuscript.py`, `pilot.py`, `first_paper_publish.py` | ドラフトDL一致・全資産attestation・公開後再取得 | 公開と検証の原子性 (文書で明言) |
| 時刻証拠 | `timestamp.py` | nonce/OID/imprint/UTC/CRL/証明書連鎖を独立policyで検証 | 初公開時刻、暗号学的根本安全性 |
| ZIP | `preserve.py`, `custody.py`, `github_mirror.py` | allowlist・重複・symlink・サイズ・hash-then-parse | 台帳自体の真正性 (外部pin必須) |
| ACL | Windows secret ACL (PR #49で修正済み) | SIDベースの正確なACL | 別管理者の独立性 |
| 観測記録 | `observation.py` | Ed25519署名+key pin、主張限定、Both-binding、TSA manifest一致 | 観測者の誠実さ・初公開時刻 |

## 3. 発見した欠陥と修正・回帰試験

重大・高リスクの未解決欠陥は **0**。中程度以下の7件を修正し、各々に再現→修正→回帰試験を付けた。

| ID | 深刻度 | 箇所 | 欠陥 | 影響 | 修正 | 回帰試験 |
|---|---|---|---|---|---|---|
| AUD-01 | 中 | `publish_manuscript.py:274` | 公開後に Release オブジェクトを読戻さず repository 設定だけで `PASS` と報告 | 可変Releaseが不変と誤認され、pin証拠が後から無効化され得る | 公開後 `GET .../releases/tags/{version}` で `immutable/draft/tag_name/assets` を検証し `release_immutable_readback` を記録 | `test_mutable_public_release_is_rejected`, `test_immutable_public_release_reports_readback` |
| AUD-02 | 中 | `publish_manuscript.py:230`, `preflight.py:110` | git tag の空き確認が `_commit_inputs()` の**後** (.source push 後) | 不正入力で public 既定ブランチに孤立commitが残る | 早い段階で `GET /git/ref/tags/{version}` を追加し、書込み前に両方の占有チェック | `test_occupied_git_tag_blocks_before_write` |
| AUD-03 | 中 | `owner_setup.py:46` | 設定後の GET で public/admin/canonical を再検証していない (TOCTOU) | 非public・非admin リポジトリに PASS または書込み | 読戻しにも初期と同じ identity/visibility/admin ガードを適用 | `test_owner_setup_readback_flip_is_rejected` |
| AUD-04 | 低 | `publish_manuscript.py:323` | `--plan` と `--publish` の併用が「exactly one」ガードをすり抜け、exit 0 で何もしない | 自動化が公開要求を認識できない | `sum(bool(...)) == 1` に変更 | `test_plan_cannot_be_combined_with_publish` |
| AUD-05 | **高** | `research_package.py:108` | collect 後 create_research までの間に ancestor を外部ディレクトリへの symlink/junction に差し替えても、leaf しか再検証しない | 公開研究アーカイブに外部の機密ファイルが混入し、catalog が整合しているため検証を通過する | 読取り直前に leaf+ancestor+resolve containment+junction を再検証する `path_is_safe()` を追加 | `test_ancestor_swap_after_collect_is_rejected` |
| AUD-06 | 中 | `citation_validation.py:98` | BibTeX が非空文字列だけで、metadata に結合されていない | 改変・誤生成された引用が PASS で公開される | title/author/note を検証済み metadata に結合 | `test_mismatched_bibtex_is_rejected` |
| AUD-07 | 低 | `citation_validation.py:73` | 重複JSONキーを許容 (他 verifier は拒否) | validator 間の解釈不一致、fail-open | `object_pairs_hook=unique_object` を適用 | `test_duplicate_metadata_keys_rejected` |
| AUD-08 | 中 | tests 23ファイル | `Path.read_text()` がロケール既定 (cp932) を使用し、UTF-8 ファイルを読めない | 日本語 Windows で 7 tests が ERROR / G0 の OS  porta 性違反 | 全テストの read_text に `encoding='utf-8'` を明示 | 全394試験を `PYTHONUTF8` 未設定で実行し PASS |
| AUD-09 | **高 (CI FAIL)** | `tests/test_hypothesis_properties.py` | Hypothesis未インストール環境で、`skipUnless` に関わらずクラス定義時に `@settings`/`@given` が評価され `NameError` | PR #51 の Validate (3.10/3.12) と Quality (Ubuntu/Windows) が **FAIL** (run `44028158017`, `44028158061`) | 未インストール時に無効デコレータと strategy スタブを定義し、モジュール import を成功させる | `test_hypothesis_module_imports_without_dependency` (subprocess で依存を隠して import) |

すべての再現は実行済み。回帰試験は [tests/test_hardening_regressions.py](../tests/test_hardening_regressions.py) に集約 (9件)。
AUD-09 は継続サイクル Step 1 で古い成功ログを流用せず CI を読み直した結果、新たに発見した**自作の回帰**である。
旧 FAIL の run ID (`44028158017`, `44028158061`) は過去の事実として保持し、削除・上書きしない。修正後 run で再判定する。

## 4. 异常入力・状態遷移・競合試験

- Hypothesis 7性質 / 100–150 examples each: [tests/test_hypothesis_properties.py](../tests/test_hypothesis_properties.py)
  - 重複キー拒否、receipt の data+signature への結合、repo 検証の不変条件、safe_https の不変条件、
    **本番 preflight と Lean 状態モデルの差分**、BibTeX 正規化の冪等性、HEX 正規表現の一致。
- 既存の否定試験 (20件固定・誤受理0) は変更せず維持。
- 競合/TOCTOU: AUD-02, AUD-03, AUD-05 を明示的に再現・修正。

## 5. 未解決の重大・高リスク欠陥

**0件。** よって技術監査単体では NO-GO の新規根拠は追加しない。
ただし正式 G0–G7 の独立承認 (特に G4/G5/G7) は未達であり、P4 は引き続き NO-GO。
