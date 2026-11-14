# 独立観測者パッケージ（G4）

**目的:** 著者/所有者と独立した実在の観測者が、対象4版を匿名取得し Ed25519 で署名する。
**注意:** AI・同一アカウント・同一端末・所有者の別ランナーは「独立観測者」ではない。署名は実在の人間が行うこと。

## 依頼文（所有者→観測者）

> あなたは OpenPreprint Kit の第1論文(v1)と合成受入デモ4版（計5版）を、私の GitHub から匿名 HTTPS で取得し、あなた自身の Ed25519 秘密鍵で署名して、取得した観測記録と署名を私に返してください。鍵はあなたが一意に保持し、複製・共有・預託しないでください。私の側では秘密鍵を受け取りません。完了したら、公開鍵指紋を「別経路」（例: 電話・対面・別メール）で私に伝え、私と別の検証担当が確認します。署名入り観測証拠とあなたの独立性確認書をもって G4 の PASS となります。

## 対象5版（正式4版は G2 決定後に確定。現時点の承認済みセット）

| # | Repository | Release | Tag target | 取得URL |
|---|---|---|---|---|
| 1 | Unjuno/openpreprint-kit-paper | v1 | 804cb76a4cf5eea65349fc7a8f01e2ce00e1176d | https://github.com/Unjuno/openpreprint-kit-paper/releases/tag/v1 |
| 2 | Unjuno/opk-demo-acceptance-a | v1 | a27ab50f8effca89abdc72ce5d6744c1510e8697 | https://github.com/Unjuno/opk-demo-acceptance-a/releases/tag/v1 |
| 3 | Unjuno/opk-demo-acceptance-a | v2 | 86f3cf2e4afe507253cb9346b0489d1edf175072 | https://github.com/Unjuno/opk-demo-acceptance-a/releases/tag/v2 |
| 4 | Unjuno/opk-demo-acceptance-b | v1 | 78e8ef8dfaec8506a6de0391fcd6de80afd13686 | https://github.com/Unjuno/opk-demo-acceptance-b/releases/tag/v1 |
| 5 | Unjuno/opk-demo-acceptance-b | v2 | 6c281c97a180e951517b935a392915e06901ba34 | https://github.com/Unjuno/opk-demo-acceptance-b/releases/tag/v2 |

（G2 で A案が選ばれた場合、paper v2 が追加された時点で対象を差し替える。）

## 観測者が行う手順

1. **鍵生成（観測者のみ）**: `openssl genpkey -algorithm ED25519 -out observer-witness.key`（`chmod 600`）。公開鍵: `openssl pkey -pubout -in observer-witness.key -out observer-witness.pub`
2. **取得**: 各 Release の資産11件を匿名 HTTPS で取得（`gh release download` またはブラウザ。トークン不要であることを確認）。バンドルは `paper.pdf` の SHA-256 と `SHA256SUMS` で検証できる。
3. **署名**: 観測記録（下記フォーマット）を JSON 正準形で保存し、`openssl pkeyutl -sign -rawin -in observation.json -inkey observer-witness.key -out observation.sig`
4. **RFC 3161 付与**: 観測記録のダイジェストに対して独立に選定した TSA（FreeTSA 可、ただし**観測者自身が信頼選定**すること）へタイムスタンプを請求し、TSR を観測記録と同じ場所に保存する。
5. **返送**: `observation.json`, `observation.sig`, `observer-witness.pub`, TSR, 取得した全資産の SHA-256 を返送。

## 観測記録のフォーマット（例）

```json
{
  "schema_version": 1,
  "signed_by": "<観測者名/識別子>",
  "repository": "Unjuno/openpreprint-kit-paper",
  "version": "v1",
  "source_commit": "804cb76a…",
  "observed_interval_start_utc": "…",
  "observed_interval_end_utc": "…",
  "anonymous_https": true,
  "files": {"<name>": {"sha256": "…", "size_bytes": 0}, …},
  "paper_sha256": "0860b735…",
  "public_availability": "WITNESS_ASSERTS_ANONYMOUS_RETRIEVAL",
  "first_publication": "NOT_PROVEN",
  "authorship": "NOT_PROVEN"
}
```

## 独立性確認書（観測者が署名）

> 私は、著者 Unjuno / OpenPreprint Kit 所有者とは独立した管理・鍵・実行環境で上記観測を実施した。私は観測鍵の唯一の保有者であり、鍵の複製・共有・預託は行っていない。観測は誰にも改ざんされていない。初公開時刻・著者本人確認・査読・科学的正しさは証明しない。

## 検証者（所有者と別の担当）の確認項目

- Ed25519 署名が `observer-witness.pub` で検証できること
- 公開鍵指紋（SHA-256）を別経路で観測者と突合すること
- 観測記録の全ファイル SHA-256 が取得物と一致すること
- 観測 TSR を信頼済み TSA ポリシーで検証できること（HTTP 通信ではなく、独立した信頼設定で）
- 観測者が秘密鍵を開示していないこと
- 観測記録・TSR・鍵指紋を Issue #5 に添付すること

## PASS 条件

- 対象4（または5）版すべての署名付き観測記録 + TSR + 鍵指紋の別経路確認 + 検証担当の署名が Issue #5 に記録されること。
- これが無い限り G4 は PASS にしない。署名が無効・鍵の管理が曖昧・別経路確認が無い場合は FAIL/BLOCKED。
