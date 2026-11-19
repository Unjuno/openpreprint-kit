# OpenPreprint Kit — TECHNICAL_ACCEPTANCE

作成日: 2026-11-17 (JST)
**対象SHA: `cbd537527f5e4c037cad7a1284d24830ee0b91e2`**
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
| 全 unittest (修正後) | **403 試験 / 15 skip / OK** (再実行)、`PYTHONUTF8` 未設定) | ローカル実行ログ |
| 新規回帰試験 | 18/18 PASS (AUD-01〜17、AUD-11にマージ改変ケースを含む) | `tests/test_hardening_regressions.py`, `tests/test_hardening_regressions_iter3.py`, `tests/test_hardening_regressions_iter4.py` |
| Hypothesis 特性 | 7/7 PASS (100–150 examples each) | `tests/test_hypothesis_properties.py` |
| Python vs Lean 差分 | **33/33 MATCH** | `formal/VERIFICATION_RESULTS.txt`, `formal/lean_results.txt` |
| Lean ビルド | `Build completed successfully` (6 jobs)、`sorry/admit/axiom` なし | 同上 |
| CI (固定SHA 811dc84) | Validate 3.10/3.12・Quality/audit・CodeQL・selftest・portable すべて success | `43832249370` 他 |
| CI (PR #51 旧 commit 889ff4b) | **FAIL** (AUD-09: Hypothesis未依存環境で `NameError: settings`) — 過去の事実として保持 | `44028158017`, `44028158061` |
| CI (PR #51 修正後 0efeada) | Validate 3.10/3.12・Quality (Ubuntu+Windows)・CodeQL・selftest・portable **すべて success** | `44107268710`, `44107268574`, `44107268524` |
| CI (PR #51 旧 1ad50ce) | **FAIL** (macOS job timeout 25 > guard 15) — 修正して履歴保持 | `44169617220` |
| CI (PR #51 最新 695b232) | Validate 3.10/3.12・Quality (Ubuntu/Windows/**macOS**)・CodeQL・selftest・portable **すべて success** | `44172420938`, `44172420972`, `44172421056` |
| CI (PR #51 current HEAD cbd5375) | Validate 3.10/3.12 / Quality / Windows+macOS+Ubuntu portable / CodeQL / Lean proofs / self-application **all success** (self-application timeout 15→25 min) | `44478578595`–`44478578777` |
| CodeQL | open alerts **0** | `gh api .../code-scanning/alerts` |

### OS / skip の内訳 (15件、いずれも意図的な環境ゲート)

- symlink権限 unavailable: 10件 (Windows runner で symlink 特権が必要)
- POSIX シェルランチャー統合: 5件 (Windows では `.sh` を実行しない)
- macOS: 3件 (Windows固有ACL等)、Ubuntu: 3件。いずれも環境ゲートであり必須試験の欠落ではない。
→ 必須スキップ 0 (V1_ACCEPTANCE G0 の「必須スキップ0」は満たす、と解釈するが独立レビュー待ち)。

### 異常系

既存20件の否定ケース (改変・誤CA・nonce不一致・失効TSA・古いCRL・ZIPtraversal・重複member・symlink等) は維持・誤受理0。
加えて AUD-01〜17 の再現17件と Hypothesis 7性質を追加。


## 3a. 2026-11-19 追加ハードニング（本PR内）

| 作業 | 結果 | 証拠 |
|---|---|---|
| AUD-05 再評価: POSIX 側は `dir_fd` を基点とする `O_NOFOLLOW` ウォークで読取、Windows は `CreateFileW` + `GetFinalPathNameByHandleW` で最終パスを検証。祖先差し替え/葉 symlink/junction 拒否を回帰テスト化 | 完了 | `scripts/research_package.py`、`tests/test_research_package.py` |
| GitHub ミラー `_verify_public_source` へ annotated tag 対応の tag→commit 解決を追加（深度上限 5、不正な target/ref は拒否） | 完了 | `scripts/github_mirror.py`、`_resolve_tag_commit()`、`tests/test_github_mirror.py` (4 新規テスト) |
| 更新チェーン `verify_chain()` へ署名時刻の順序検証を追加（同一 policy: 非減少／異なる OID: 厳密増加／不正な時刻: 拒否、`time_order` 属性を返す） | 完了 | `scripts/renewal.py`、`docs/TIMESTAMP-TIME-ORDER.md`、`tests/test_renewal.py` (6 新規テスト) |
| Lean 4 形式検証を**必須 CI** に統合（`lean-proofs.yml`）：`lake build OpenPreprintFormal`、sorry/admit/axiom 戦術行の拒否、ベクトル再生成決定性検査、Python–Lean 差分検査 | 完了 | `.github/workflows/lean-proofs.yml`、PR #51 head `cbd5375`（CI 全成功） |
| first-paper-selftest の timeout を 15→25 分に引上げ（texlive の `Building format(s) --all` がフレッシュランナーで 15 分を超えることを確認） | 完了 | `.github/workflows/first-paper-selftest.yml` |
| ローカル実行: `unittest discover -s tests` → **416 件 / 23 skip / OK** | 完了（本機） | 実行コマンドと時刻は本ファイル §3 の更新を参照 |

**AUD-05 残存 TOCTOU の評価**: 従来の `path_is_safe()` → `read_bytes()` という2操作間の競合窓を、ハンドルベースの検証読みへ置換した。


## 4. Lean で証明した性質 / 未証明

- 証明: 32定理 (ReleaseAssets 12 / StateTransition 8 / EvidenceBinding 12)。詳細は [formal/README.md](formal/README.md)。
- 共通テストベクトル: `formal/vectors.json` → `GeneratedVectors.lean` を自動生成。Python 側は本番 `preflight.preflight()` と `observation.receipt_digest()` を直接呼び、他2領域は本番ルールを純粋入力へ忠実に再表現 (ソース行をコメント明記)。
- **モデルと本番Pythonは異なる実装**。等価性は28ベクトル + Hypothesis 7性質による部分確認であり、全入力領域の証明ではない。
- 未証明/仮定: SHA-256衝突耐性、Ed25519偽造耐性、RFC3161/X.509/CRL暗号検証、GitHub API応答、実時刻、観測者の独立性、CA選定、OSのsymlink/junction挙動。

## 5. 技術品質ゲート (正式 G0–G7 とは別枠)

| ゲート | 判定 | 根拠 |
|---|---|---|
| TQ-1 修復済み欠陥の回帰 | **PASS** | 18/18 回帰試験 PASS (AUD-10〜17 の履歴ガード誤PASS・パス回避を含む) |
| TQ-2 未解決重大・高リスク欠陥 | **PASS** | 0件 (監査 §5) |
| TQ-3 全試験成功 | **PASS** | 403/403 (15 skip は環境ゲート) |
| TQ-4 形式検証のカーネル検査 | **PASS** | Lean 4.35.0 ビルド成功、sorry/admit/axiom なし |
| TQ-5 Python-Lean 対応 | **PASS** | 33/33 ベクトル一致 (verified→published 遷移を含む) |
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
| `scripts/research_package.py` | `820831451a6181ac5f7373ebb774117db27ae30728791c42b72744490e966dc6` |
| `.github/workflows/quality.yml` | `ebb15d166e6f8612a44f772ddaefddca474aa9e088204525ca0b3c5e6d9751f9` |
| `scripts/validate.py` | `7af553deb20ee66fd620875425f55603f1413c1e9b8025f10e58c5511bd78add` |
| `scripts/prepare_release.py` | `92ec64adc714699b2e39b0bab7dd1d295226a98c2291467cce837bb24c115e25` |
| `scripts/pdf_validation.py` | `d84e7d83c27935cc83e45a260fa365acf083889173d5ae3775490809572ed9ba` |
| `scripts/private_seal.py` | `cba152d68f2f56db84a7c14090f2d611be50f41cc9a4e5a72520feaae4e3ad79` |
| `tests/test_hardening_regressions_iter4.py` | `1ef3fa48e80e66d78338254f143fefabaae26caa51a4a1efe016334ed1c8e1ea` |
| `docs/TECHNICAL_AUDIT_2026-11-18-CYCLE6.md` | `9146c432dbe4832bf6ef482b2538a2d646a9f4db10729553b08f3b715e7c35e7` |
| `docs/TECHNICAL_AUDIT_2026-11-18-CYCLE5.md` | `83ad3e2650aced33478d644a3ecb0e3acfb3e5e451fd16313744500be2e71bcd` |
| `docs/TECHNICAL_AUDIT_2026-11-18-CYCLE4.md` | `58263fe708b25e7af8627689def2a044a46c38435afd1236f2e09b4853863bb2` |
| `scripts/commitment_history.py` | `5bc74df7cea008d010a5e3ba503dbf6b2963cd84c5bed4686e4d0252c2a55275` |
| `scripts/research_record.py` | `3da86eea83d660fd7f410041446d092fc535645c7de4e5b047d8346d2290676e` |
| `scripts/github_mirror.py` | `ec85a583a2f686b3477b86f682216de192ef35cae4a4f7add77b5020bdf39c21` |
| `scripts/renewal.py` | `68812d05071b1f70286fcdf78797d2108ee8f7f866da2f125fafd51df8dee2ab` |
| `docs/TIMESTAMP-TIME-ORDER.md` | `6e806c631a2f691025fd7716bd5d5c15417b7f2226f5d8ea524cbcf337261111` |
| `.github/workflows/lean-proofs.yml` | `bcbbc7b74c2d269ea45a3e3af85d5132010e526db4d62c1ae16e46cf70a19dea` |
| `.github/workflows/first-paper-selftest.yml` | `2a14a718e5e6d4c71000f60c0322477a9ef0a025ed7a1bab08b6f56ed78e9f51` |
| `tests/test_github_mirror.py` | `3679263c0a2ade100c1d7f5bfe4e88ab36c8f3d89040487f9433ceba143ffee6` |
| `tests/test_research_package.py` | `33cd47c22433ee851757003afe7512183b0222c9c042eecd82e2c244a81ae367` |
| `tests/test_renewal.py` | `3e51cfb59069e7adfb1aca1576748bec168406c445a9ff56d1948b371ba2d4eb` |
| `scripts/first_paper_selftest.py` | `1ac9d884444e0f69cad10b96cc0ffd368b858184bbff91353ab69b761d50f287` |
| `scripts/citation_validation.py` | `f4eba138d264d0e1f701d6323bc061b20ed9244147c55d3ae87fddf083d6a3b9` |
| `tests/test_hardening_regressions.py` | `0879b8f78b602f4ddb81affcd9725697765f89d12ea1cfba4ecc5b76b6e5ae8e` |
| `tests/test_hardening_regressions_iter3.py` | `f4c10fc746bfcd1bcc6c9f8611dd0b2dfae7d79f33ed4910b5010cc2e0b0724c` |
| `tests/test_hypothesis_properties.py` | `a9f171a0b89b0edc52e12c87d73e621791a7ced5481d980e9cb5f85bd7a83d03` |
| `formal/lean_results.txt` | `1e8d435df5354052ec0df1dbc49662b5b88e3c6b9fee4e283f2f2c41b0a97a82` |
| `formal/vectors.json` | `23dcde263ca4f52a13f469d65ae41368e3645289b5dcbc9968c1d99727896785` |
| `formal/VERIFICATION_RESULTS.txt` | `be6506a5b374f1c0ada4a94a27e0ea01091ef9fd2f19b0cc8f18547822e07bb1` |
| `formal/OpenPreprintFormal/ReleaseAssets.lean` | `d054024faf018cd0547ee5ce69e59cd23ef96148bef4450e1041364f738ad0fd` |
| `formal/OpenPreprintFormal/StateTransition.lean` | `6b9485b09e851116b254223fd5fd65fc513b541c911f139ec591650ee2268997` |
| `formal/OpenPreprintFormal/EvidenceBinding.lean` | `f96c48c2f000f6de6f2f5779a76e2b351f73349889bdbacbd1b806095deb3d93` |
| `formal/lean-toolchain` | `ca5f1f601d34c49079e38d7e7041eb0f2a9c227fbc1df0f404820069a052330c` |
| `docs/TECHNICAL_AUDIT_2026-11-18.md` | `0eb70284314f465aa5ea6004e0cb7b934204f2eef01a9918b32feb9c529a8610` |
| `docs/TECHNICAL_AUDIT_2026-11-17.md` | `0f803e5138fd9b2e9069b10405addc1bd9b853957e1ba8ee60e28729bfa93fb3` |
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

## 10. 次回の最優先作業と完了条件

| 優先度 | 課題 | 原因 / 現状 | 完了条件 |
|---|---|---|---|
| 1 | CI での Hypothesis 実行 — **完了** | 旧CIは test-only 依存が無く7特性がskip。Hypothesis 6.170.15 は **Python >=3.11 必須** | 3.12ジョブのみ hash固定lockを導入。run `44109219645` の validate(3.12) で **7特性すべて ok / 394 tests / OK(skipped=3)**、validate(3.10) は7件を正しくskip。Quality/CodeQL も success (`44109219720` 他) |
| 2 | 旧 FAIL の履歴保持 | run `44028158017` / `44028158061` は AUD-09 修正前の FAIL。削除せず記録済み | 修正後 run `0efeada` 以降の全 success と併せて台帳に残す（完了） |
| 3 | macOS 全 unittest — **PASS（完了）** | `quality.yml` に macos-regression(3.12) を追加（hash固定lock + Homebrew OpenSSL 3）。run `44172420938` で **403 tests / OK(skipped=3)**、OpenSSL 3.5.9、macOS 15。Windows/Ubuntu/Audit も同runで success | 完了。過去の FAIL run `44169617220`（timeout-guard違反 25>15）は修正して保持 |
| 4 | G4 / G5 / G7 の独立検証 | 外部の独立人間が必要。AI 自己検証は不可 | 独立観測者・保管者・監査者の選任と署名入り証拠が揃う（所有者の手配が必要） |

最新 head `695b232` で CI 全5ワークフロー success。macOS 全 unittest も success（run `44172420938`, 403 tests / 3 skips）。過去の cancelled/queued/FAIL（`44116478457`, `44122897522`, `44169617220`）は削除せず履歴として保持。
次回の最優先は優先度4のG4/G5/G7（所有者による独立検証者の選任）。変更は引き続き PR #51 で提案し、固定 main への統合は所有者の承認を待つ。




