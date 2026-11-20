# Codex 引き継ぎ: v1.0.0 発行（Computer Control 用）

作成日: 2026-11-21
依頼: 所有者が Codex による実操作で v1.0.0 を発行する。AI による実操作はこの作業について許可済み（影響範囲外）。
**本資料は引き継ぎであり、発行そのものではない。エージェントはまだ発行していない。**

## 0. 現在の確定状態（証拠付き）

| 項目 | 値 |
|---|---|
| main | `837e0c49131ed594218b202374482b1ea375529b` |
| 必須 CI | 7/7 success（validate 3.10/3.12、audit、CodeQL Python、Lean、Windows/macOS regression） |
| open PR | 0 |
| 受入 | 2026-11-21 の緩和基準で全ゲート PASS、`独立性=UNPROVEN` |
| 品質証拠 | `docs/QUALITY_EVIDENCE_2026-11-21.md`（原ログURL・SHA・テスト件数） |
| 公開済み | 論文 v1 `444659219` / v2 `445442340`（Immutable、変更禁止） |
| キット Release | **未発行**（`Unjuno/openpreprint-kit` には Release 0件） |

## 1. 発行の前提条件（未配置のため、揃えないと実行不可）

1. **`timestamp-policy.json`** をリポジトリルートに配置（ワークフローが `test -f` で要求）。
   - `schema_version`, `tsa_url`, `ca_file`, `ca_sha256`, `crl_file`, `policy_oid`, `timeout_seconds`
   - CA/CRL は独立に選定した信頼できるものを配置し、pin を一致させる。
2. **GitHub Actions secret `OPK_ADMIN_READ_TOKEN`**（Administration: read を持つ短命 token）を所有者アカウントで設定。
3. **`preprint.yaml` の実メタデータ**を設定（現状 `v0` / プレースホルダ）。
   - `version` を発行タグ（例 `v1.0.0`）に、`title` / `authors` / `abstract` / `license` を実値に。
4. **Immutable Releases が有効**であることを Settings > General > Releases で確認。
5. **2つの GitHub アカウント**が利用可能であること（使い方は §3）。

## 2. 実行手段（コマンド）

### 2-1. 設定（アカウント A = 所有者）
```bash
# リポジトリ設定で以下を実施（UI または gh api）
# - Settings > General > Releases > Enable release immutability
# - Settings > Secrets and variables > Actions > New repository secret:
#     OPK_ADMIN_READ_TOKEN
```
`timestamp-policy.json` と CA/CRL、`preprint.yaml` の実メタデータを commit & push（main に直接 push せず PR 経由。所有者が承認・マージ）。

### 2-2. 発行ワークフローの起動
```bash
gh workflow run publish.yml --repo Unjuno/openpreprint-kit --ref main \
  -f acknowledge_immutable_enabled=true
gh run list --repo Unjuno/openpreprint-kit --workflow publish.yml --limit 3
gh run watch <RUN_ID> --repo Unjuno/openpreprint-kit --exit-status
```
ワークフローは次を実行: 全テスト → `research_record.py` → `research_package.py --check` → `prepare_release.py` → `verify_release.py` → `citation_validation.py` → `preflight.py` → RFC 3161 stamp/verify → draft Release 作成 → 匿名再ダウンロード・byte 照合 → immutable 再確認 → draft=false へ昇格。

### 2-3. 発行後の検証（アカウント B でも可）
```bash
gh release view v1.0.0 --repo Unjuno/openpreprint-kit \
  --json tagName,isDraft,isImmutable,assets,publishedAt
gh release verify v1.0.0 --repo Unjuno/openpreprint-kit
gh release download v1.0.0 --repo Unjuno/openpreprint-kit --dir /tmp/verify-v1
python scripts/verify_release.py /tmp/verify-v1
python scripts/citation_validation.py /tmp/verify-v1
python scripts/timestamp.py verify /tmp/verify-v1 --policy timestamp-policy.json
```
検証結果を `docs/QUALITY_EVIDENCE_2026-11-21.md` または Issue #5 に追記（Release ID、asset 数、immutable、anonymous DL byte 一致）。

## 3. 2アカウントの扱い（重要）

- **アカウント A**: 所有者。リポジトリ設定、secret 設定、ワークフロー起動、出版物の操作を担当。
- **アカウント B**: 読み取り専用の検証（匿名取得・`gh release view`・ダウンロード照合）に使用してよい。
- **禁止**: アカウント B を「独立レビュアー」として記録しない。アカウントの切り替え・作り分けは独立レビューではなく、`独立性=UNPROVEN` のままとする。架空レビュアー名・AI 自己点検も独立レビューに計上しない（V1_ACCEPTANCE.md 前文注、REVIEW_POLICY.md 注意書き参照）。

## 4. 禁止事項

- 既存の Immutable Release（論文 v1 `444659219` / v2 `445442340`）の変更・削除。
- `main` への直接 push / force-push。
- 検証のバイパス（`-no_check_time` 等での成功演出、ガード無効化、SKIP の強制）。
- 架空のレビュアー・署名・承認の作成。
- 発行に失敗した場合の「巻き戻し」主張（公開は原子的ではない）。
- v1.0.0 以外のタグの再利用。

## 5. 停止条件

- 前提条件（§1）が揃っていない場合は発行しない。
- ワークフローが FAIL した場合は原因を特定し、検証を緩めずに修正してから再実行。
- 発行は所有者の最終承認（本依頼）の範囲内で行う。エージェントは承認を超える操作をしない。

## 6. 引き渡し地点

作業開始: main `837e0c49131ed594218b202374482b1ea375529b`、open PR 0、必須 CI 7/7 success。
完了定義: v1.0.0 Immutable Release が作成され、全資産の署名・匿名取得・byte 一致・ attestation が確認され、証拠が台帳に追記された時点。
