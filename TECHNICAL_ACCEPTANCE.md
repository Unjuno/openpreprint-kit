# OpenPreprint Kit — TECHNICAL_ACCEPTANCE

作成日: 2026-11-17 (JST)
**対象SHA: `811dc84367c88a81dbf062fa5d262f5d10a41180`**
正式受入基準: [docs/V1_ACCEPTANCE.md](docs/V1_ACCEPTANCE.md) — **緩和・置換していない**。本文書は技術品質の補助記録であり、G0〜G7 の合格判定を代行しない。

## 1. 対象と必須機能

| 項目 | 内容 |
|---|---|
| 対象 | 固定 main SHA 上のツール本体、公開処理、時刻証拠、ZIP保管、観測記録 |
| 必須機能 | 厳密YAML/JSON取込、manifest+SHA256SUMS整合、CFF/BibTeX外部検証、PDF構造検査、RFC3161検証、Immutable Release公開、匿名取得・復元、観測署名、ACL |
| 除外 | 初公開時刻、著作者確認、科学的正確性、ピアレビュー、長期保存保証 (V1_ACCEPTANCE §1/§6 に倣う) |

## 2. 環境

| 項目 | 値 |
|---|---|
| OS | Windows (日本語ロケール / cp932) |
| Python | 3.12.10 (3.10 互換は CI の Validate 3.10 で確認、ローカルは 3.12 のみ) |
| OpenSSL | 3.5.0 (`C:\msys64\ucrt64\bin\openssl.exe`) |
| 主要依存 | PyYAML 6.0.3, asn1crypto 1.5.1, pypdf 6.21.4, (試験のみ Hypothesis 6.170.15) |
| Lean | `leanprover/lean4:v4.35.0` (固定、`formal/lean-toolchain`) |

## 3. 試験結果

| 試験 | 結果 | 証拠 |
|---|---|---|
| 全 unittest (修正後) | **393 試験 / 15 skip / OK** (280.199s、`PYTHONUTF8` 未設定) | ローカル実行ログ |
| 新規回帰試験 | 8/8 PASS | `tests/test_hardening_regressions.py` |
| Hypothesis 特性 | 7/7 PASS (100–150 examples each) | `tests/test_hypothesis_properties.py` |
| Python vs Lean 差分 | **28/28 MATCH** | `formal/VERIFICATION_RESULTS.txt`, `formal/lean_results.txt` |
| Lean ビルド | `Build completed successfully` (6 jobs)、`sorry/admit/axiom` なし | 同上 |
| CI (固定SHA) | Validate 3.10/3.12・Quality/audit・CodeQL・selftest・portable すべて success | `43832249370` 他 |
| CodeQL | open alerts **0** | `gh api .../code-scanning/alerts` |

### OS / skip の内訳 (15件、いずれも意図的な環境ゲート)

- symlink権限 unavailable: 10件 (Windows runner で symlink 特権が必要)
- POSIX シェルランチャー統合: 5件 (Windows では `.sh` を実行しない)
→ 必須スキップ 0 (V1_ACCEPTANCE G0 の「必須スキップ0」は満たす、と解釈するが独立レビュー待ち)。

### 異常系

既存20件の否定ケース (改変・誤CA・nonce不一致・失効TSA・古いCRL・ZIPtraversal・重複member・symlink等) は維持・誤受理0。
加えて AUD-01〜08 の再現8件と Hypothesis 7性質を追加。

## 4. Lean で証明した性質 / 未証明

- 証明: 29定理 (ReleaseAssets 11 / StateTransition 8 / EvidenceBinding 10)。詳細は [formal/README.md](formal/README.md)。
- 共通テストベクトル: `formal/vectors.json` → `GeneratedVectors.lean` を自動生成。Python 側は本番 `preflight.preflight()` と `observation.receipt_digest()` を直接呼び、他2領域は本番ルールを純粋入力へ忠実に再表現 (ソース行をコメント明記)。
- **モデルと本番Pythonは異なる実装**。等価性は28ベクトル + Hypothesis 7性質による部分確認であり、全入力領域の証明ではない。
- 未証明/仮定: SHA-256衝突耐性、Ed25519偽造耐性、RFC3161/X.509/CRL暗号検証、GitHub API応答、実時刻、観測者の独立性、CA選定、OSのsymlink/junction挙動。

## 5. 技術品質ゲート (正式 G0–G7 とは別枠)

| ゲート | 判定 | 根拠 |
|---|---|---|
| TQ-1 修復済み欠陥の回帰 | **PASS** | 8/8 回帰試験 PASS |
| TQ-2 未解決重大・高リスク欠陥 | **PASS** | 0件 (監査 §5) |
| TQ-3 全試験成功 | **PASS** | 393/393 (15 skip は環境ゲート) |
| TQ-4 形式検証のカーネル検査 | **PASS** | Lean 4.35.0 ビルド成功、sorry/admit/axiom なし |
| TQ-5 Python-Lean 対応 | **PASS** | 28/28 ベクトル一致 |
| TQ-6 リポジトリ台帳の作成 | **PASS** | REPOSITORY_MAP.md |
| TQ-7 独立人間による G4/G5/G7 | **UNKNOWN** | 本監査は自己検証。独立監査者の選任・実測は未実施 |
| TQ-8 公式G0–G7の独立承認 | **UNKNOWN** | RELEASE_READINESS の PARTIAL/BLOCKED を変更せず |

※ TQ-7/TQ-8 は「代替した」ではなく「代替できない」ことを記録している。

## 6. 正式 G0–G7 の扱い

| ゲート | 現状 (RELEASE_READINESS 2026-11-15 を踏襲) | 本監査の変更 |
|---|---|---|
| G0 | PARTIAL (独立レビュー承認未) | 技術的証拠を追加。判定は変更せず |
| G1 | PARTIAL | 変更せず |
| G2 | PARTIAL (発行者と別の検証担当が未) | 変更せず |
| G3 | PARTIAL (TSA運用/検証担当の承認未) | 変更せず |
| G4 | **BLOCKED** (独立観測者) | **自己検証で代替しない** |
| G5 | **BLOCKED** (別管理保管者) | **自己検証で代替しない** |
| G6 | PARTIAL (人間のレビュー/演習未) | 変更せず |
| G7 | **BLOCKED** (外部監査者) | **自己検証で代替しない** |

**G0〜G7 全PASS ではないため P4 (キット v1.0.0) は NO-GO を維持する。**

## 7. 証拠 SHA-256

| file | sha256 |
|---|---|
| `scripts/publish_manuscript.py` | `b2c9eb1fdfd8fd128c5f68899b464d5c9d8f51d258621dd13f7d0e5c38143c06` |
| `scripts/owner_setup.py` | `631948ef43775a481b19b44835b30d2b37d4afad79d8d6b208db4ad87a31f145` |
| `scripts/research_package.py` | `dfd9e8778406e4bac5b39bcf810d4618fe9c096e47b8dbe77141ba73634d0316` |
| `scripts/citation_validation.py` | `f4eba138d264d0e1f701d6323bc061b20ed9244147c55d3ae87fddf083d6a3b9` |
| `tests/test_hardening_regressions.py` | `f488bfc3cf38a40ea2925f154c4a0934bd146f7ee916411873012b23a007d01f` |
| `tests/test_hypothesis_properties.py` | `9bd31c92d5e38cb9edf12339576ee37ea6678cfa2678608b35e7c859f739a989` |
| `formal/lean_results.txt` | `ef787ea4c6f34e14bed4e06e13cc310adcd33e9e9d10b1f1c935766577d4eb32` |
| `formal/vectors.json` | `c4bf1efdae083fe6a2e0b3a14f7b8af85a058a0f312a2ef0787111d64dff3147` |
| `formal/VERIFICATION_RESULTS.txt` | `5992f6e953dae99277073b97c4049292a4aa99fc17fee7acca6400e1f344f974` |
| `formal/OpenPreprintFormal/ReleaseAssets.lean` | `d054024faf018cd0547ee5ce69e59cd23ef96148bef4450e1041364f738ad0fd` |
| `formal/OpenPreprintFormal/StateTransition.lean` | `6b9485b09e851116b254223fd5fd65fc513b541c911f139ec591650ee2268997` |
| `formal/OpenPreprintFormal/EvidenceBinding.lean` | `f96c48c2f000f6de6f2f5779a76e2b351f73349889bdbacbd1b806095deb3d93` |
| `formal/lean-toolchain` | `ca5f1f601d34c49079e38d7e7041eb0f2a9c227fbc1df0f404820069a052330c` |
| `docs/V1_ACCEPTANCE.md` (不変更) | `9fd1a889191d6c2f5024bf758c008105084296698a2772cb85d34c1b830f3135` |
| `docs/RELEASE_READINESS.md` (不変更) | `2a7f78af346b43edee1e1ba3453539e596676e83274a4dcf15347b6619bc5c15` |
| `evidence/acceptance/first-paper-v1-release-observation-2026-11-14.json` | `2e029607e93298baa00b59a04aecfcea6685e322f649dcf6b9e0c94cf0a5c02b` |
| `evidence/acceptance/gate-evidence-matrix-2026-11-14.json` | `e840e960f7457795ae96dcd537564417a2ccb14c26e8391c7adf5442b3166896` |
| `evidence/acceptance/unresolved-blockers-2026-11-14.md` | `dd4c2b99aed0d19aa54861dc2a7c427653adc7f54d399558a2e2e0616b1325b4` |

## 8. 正式 v1.0.0 までの未達一覧

1. G0: 独立レビュー担当による固定SHAの承認
2. G1: 各所有者による設定の読戻し・テンプレート由来の独立確認
3. G2: 発行者と別の検証担当による4版の判定・署名
4. G3: TSA運用担当の信頼選定と検証担当の判定
5. G4: **独立 observed 管理者の匿名取得・署名・別鍵検証** (自己検証禁止)
6. G5: **別管理GitHubミラー + 台帳/ハッシュの別経路保持 + GitHub非接続4版復元** (自己検証禁止)
7. G6: 実人間のライセンス/COI確認・レビュー1件・訂正/撤回演習
8. G7: **外部監査者による固定SHA監査とライフサイクル試験** (自己検証禁止)
9. 全PASS後に本体 `v1.0.0` 不変Releaseを発行 (所有者承認) し再取得検証

## 9. 承認を要する操作 (未実施)

- 固定 main への統合 / PR マージ
- 権限変更、リポジトリのアーカイブ・削除
- Release 発行
- 合成デモ (`opk-demo-acceptance-a/b`) のアーカイブ
- 開いている PR / 古いブランチの閉鎖・削除

すべて所有者の明示承認を待つ。
