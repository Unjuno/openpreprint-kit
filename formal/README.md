# OpenPreprint Kit — Lean 4 形式検証モジュール

## 固定ツールチェーン

`lean-toolchain`: `leanprover/lean4:v4.35.0` (elan が固定。ダウンロードではなくローカル既設 toolchain を使用)
`lakefile.toml`: `openpreprint_formal` / `lean_lib OpenPreprintFormal`

再現コマンド (Windows / POSIX 共通):

```bash
cd formal
lake build OpenPreprintFormal
lake build OpenPreprintFormal.GeneratedVectors
lake env lean ModelEval.lean > lean_results.txt
python differential.py
```

`VERIFICATION_RESULTS.txt` は 2026-11-17 の実測出力をそのまま保存したもの。
`lean_results.txt` は `#eval` の出力、28/28 ベクトルが Python と一致。

## モデル化した3領域

| モジュール | 領域 | 対応する本番コード |
|---|---|---|
| `OpenPreprintFormal/ReleaseAssets.lean` | Release資産集合と版・リポジトリIDの一致 | `verify_release.py`, `preflight.py`, `publish_manuscript.py` |
| `OpenPreprintFormal/StateTransition.lean` | 公開前検証と状態遷移の安全性 | `preflight.py`, `publish_manuscript.py` |
| `OpenPreprintFormal/EvidenceBinding.lean` | 観測記録・署名・証拠の相互結合 | `observation.py`, `verify_evidence.py` |

`GeneratedVectors.lean` は `vectors.py` が `vectors.json` から自動生成する (手編集禁止)。
`ModelEval.lean` は同じベクトルを Lean モデルで評価して `lean_results.txt` を出す。

## Lean カーネルが検査した定理

### ReleaseAssets (11本)
- `accept_is_deterministic` — 受入判定は決定论的
- `accept_decomposes` — 受入 = 6条件 + 任意ピン一致の分解
- `accept_requires_repo_match` / `accept_requires_version_match` — 受入には固定 repo/version 一致が必須
- `accept_requires_valid_repo` / `accept_requires_valid_version` — 受入には正しい識別子が必要
- `accept_requires_asset_set_valid` / `accept_requires_manifest_match` — 資産集合・manifest の一致が必須
- `pinned_valid_digest_implies_binding` — 有効な外部ピンと受入があれば digest がピンに結合
- `evidence_only_set_is_accepted` / `missing_payload_is_rejected` / `extra_unknown_asset_is_rejected` — 資産 allowlist の完全性

### StateTransition (8本)
- `published_is_terminal` — published は終端状態
- `published_requires_prior_verification` — 未 published から published へは検証済み状態を経由する
- `preflight_failure_keeps_draft` — preflight 失敗では draft のまま
- `forced_update_blocks_publish` — HEAD 強制更新後は publish しない
- `occupied_tag_blocks_verification` — tag/Release 占有時は verify しない
- `nonpublic_or_nonimmutable_blocked` — 非 public / 非 immutable では verify しない
- `phase_never_regresses` — phase は後退しない (rank 単調)
- `advance_is_deterministic` — 遷移は決定论的

### EvidenceBinding (10本)
- `digest_injective` — モデル化された digest は単射
- `envelope_binds_signature` / `envelope_binds_data` / `receipt_digest_is_binding` — 受領 digest が本文と署名の両方に結合
- `envelope_lengths_are_bound` — 長さプレフィクスによりフィールド境界が確定
- `parsed_claims_are_bounded` / `overclaim_is_rejected` — 主張は限定語彙のみ、過剰主張は受理されない
- `verify_implies_identity_bind` / `verify_implies_content_bind` / `verify_implies_timestamp_bind` / `verify_implies_signature_over_record`
- `substituted_timestamp_rejected` — 別版の TSA 証拠を差し替えると検証失敗

## 証明できた性質 / 仮定 / モデル外 / 未証明

### 証明できた性質
上記 29 本。いずれも `sorry` / `admit` / 独自公理なしで Lean カーネルが検査。

### 仮定 (モデル内の単純化)
- 資産は11種類の有限列挙 (実運用のファイル名は `verify_release.py` の定数)
- 版は正規の数字列、repo は OWNER/REPO の単純化された文字 class
- 時刻は `RepoView.headSha` などのスナップショットであり、API の実通信はしない
- digest を単射なラッパーとしてモデル化 (暗号学的性質の証明ではない)

### モデル外の入出力 (明示)
- 実際の SHA-256 衝突耐性、Ed25519 の偽造耐性、RFC 3161 / X.509 / CRL の暗号検証
- GitHub API の応答、HTTP リダイレクト、OS の filesystem / symlink / junction
- 実時刻、TSA の精度、CA の信頼選定、観測者の独立性
- 本番 Python の完全なコードパス (モデルは対応する判定構造のみを写す)

### 未証明 / 未達
- 暗号安全性 (証明していない。assumption としても置いていない)
- 本番 Python と Lean モデルの全入力領域での等価性 (28ベクトル + Hypothesis 7性質による部分確認のみ)
- G4 / G5 / G7 の独立人間による検証 (本モジュールは代替しない)
