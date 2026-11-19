# 技術監査・修正記録（2026-11-19）

対象ブランチ: `hardening/formal-verification-20261117` / PR #51
作業開始時点の PR HEAD: `b679f138b5d67f4a9158a8521130e317eda50bb1`
main: `09ffb4c87a1db030888000c046df3faca3c07498`

本文書は既存の失敗記録・監査記録を保持した追補である。G0〜G7 の正式受入を意味しない。

## 1. TASK-1 Windows ネイティブファイルハンドル（`scripts/research_package.py`）

**欠陥（HIGH）**: `CreateFileW` ほか 4 関数の `ctypes` 宣言が皆無で、既定 restype が
`c_long`（32-bit）だった。64-bit Windows で失敗時の `CreateFileW` は `-1` を返すが、
`INVALID_HANDLE_VALUE` は `2**64-1` なので比較が一致せず、無効 HANDLE のまま
`GetFinalPathNameByHandleW` / `ReadFile` / `CloseHandle` に渡されていた。
実測: `pointer size=8`, `CreateFileW.restype=c_long`, `HANDLE(-1).value=18446744073709551615`,
不在ファイルで戻り値 `-1`、比較結果 `False`。

**影響**: 正しいエラー（open failed）が containment escape として誤報告され、
HANDLE 値の上位ビットが切り詰められる可能性があった。

**修正**: `_win32_api()` を新設し 4 関数すべてに明示的な argtypes/restype を付与。
`HANDLE` restype で無効値を正しく検出、`NULL` も拒否。最終パス解決の失敗／バッファ
不足は fail-closed、短い読取りは継続、`ReadFile` の不正バイト数と size limit を検査。

**回帰試験**: `tests/test_research_package.py` に 4 件追加（signature 宣言、不在ファイルの
エラー種別、複数チャンク整合性、上限超過）。Red→Green を確認。

**なぜ既存テストが検出できなかったか**: 正常系の小さな HANDLE 値は `c_long` に収まり、
失敗経路（INVALID_HANDLE_VALUE）を通るテストが存在しなかった。また引数／戻り値の
型宣言そのものを検査するテストが無かった。

## 2. TASK-2 RFC 3161 更新チェーン（`scripts/renewal.py`）

**欠陥（MEDIUM）**: `verify_chain()` の docstring は「元の existence stamp と各更新
ステップの時刻関係」を検査すると述べていたが、実装は更新ステップ同士
（`signed_times[1:]`）しか比較しておらず、元証拠の署名時刻は破棄されていた。
元証拠より前に署名された更新ステップが「前方更新」として受理される可能性があった。

**修正**: `_source()` が existence stamp の `tsa_time_utc` / `accuracy_microseconds` /
`policy_oid` を保持し、検証結果に `origin_existence_stamp` として返す。
`_check_origin_to_first_renewal()` を新設し、
- combined accuracy を超える逆転は拒否
- 同一 TSA の非減少／前方を区別して記録
- 別 TSA の同等・重複時刻は `CROSS_TSA_ORDER_NOT_PROVEN_CLOCK_SKEW` として
  不確実性を明示（時計差を証明された順序としない）
- `time_order_note` に「署名時刻は提出順序・初公開時刻を証明しない」を明記

`issue_chain()` は出力確定前に `verify_chain()` を呼ぶため、発行段階でも拒否される。
`historical_ltv=NOT_ESTABLISHED` / `first_publication=NOT_PROVEN` は維持。

**回帰試験**: `tests/test_renewal.py` に 4 件追加（逆転拒否、別 TSA の不確実性、
同一 TSA の前方、レポート項目）。Red→Green を確認。

## 3. TASK-3 Lean CI の供給元固定（`.github/workflows/lean-proofs.yml`）

**欠陥（MEDIUM）**: `elan-init.sh` を可変の `master` ブランチから取得しており、
インストーラ自体の真正性検証が無かった。

**修正**: `leanprover/elan` の release tag `v4.4.0` に固定し、
SHA-256 `a620ff1641616222c8d37c54845492004bb84d6877cdbc944dd65c1aa685bf53`
を `sha256sum --check` で実行前に検証。`--default-toolchain none` とし、
コンパイラ版は `formal/lean-toolchain`（v4.35.0）のみを根拠に、`formal/` 内で
`lean --version | grep -Fq 4.35.0` を確認。保存済み成功結果は再利用せず、
毎回 `lake build`・vector 再生成・Python–Lean 差分を実行する既存手順を維持。

**回帰試験**: `tests/test_workflows.py` に静的ゲートを追加。Red→Green を確認。
CI の `lean` job は修正後の SHA で pass（2 回の実行とも）。

## 4. TASK-4 周辺モジュール監査

2 本の独立監査エージェントにより以下を精査（コード変更はエージェント自身は行っていない）。

- グループ A: `custody.py`, `verify_evidence.py`, `preserve.py`, `publication_recovery.py`
  → **HIGH/MEDIUM の具体的欠陥なし**。hash-then-parse の TOCTOU 対策、厳格な
  allow-list、外部 pin、原子的状態遷移、read-only gateway を確認。
  LOW のロバストネス課題（桁数上限、TimeoutExpired の traceback 等）は
  誤 PASS にはつながらないため未変更。
- グループ B: `github_mirror.py`, `source_provenance.py`, `observation.py`, `renewal.py`
  → **1 件の MEDIUM を発見・修正**。

### 4.1 `AnonymousGateway` が tag→commit 解決 path を拒否（MEDIUM）

`_resolve_tag_commit()` が使う `git/ref/tags/<tag>` と `git/tags/<sha>` が
`AnonymousGateway.api()` の allowlist に無く、既定 gateway で
`--require-source-release` を実行すると常に
`ValueError: anonymous verifier supports only public GitHub repository/release GET`
で失敗していた。新規ハードニング機能が CLI から利用不能という回帰。

**修正**: allowlist に上記 2 path を追加（tag 名は既存の tag バリデーションと同じ
パターン、SHA は 40 hex に制限。その他の git path は拒否を維持）。
**回帰試験**: `tests/test_github_mirror.py` に許容 path と拒否 path の両方を追加。
Red→Green を確認。

## 5. 検証状況

- ローカル: `python -m unittest discover -s tests`（OpenSSL 3 を PATH に追加）が
  TASK-1〜3 修正後 **425 tests / 16 skipped / OK**。
- `python scripts/validate.py` PASS、`python scripts/research_package.py --check` PASS。
- CI: 修正 SHA で全必須チェックを再実行中（最終状態は PR #51 の checks を参照）。

## 6. 未解決・制約

- 独立人間レビュー（G4/G6/G7）、別管理保管（G5）、正式受入判定は本記録の範囲外。
- すべての未知のバグが存在しないことを主張するものではない。監査範囲は上記モジュール
  と明示した経路に限定される。
