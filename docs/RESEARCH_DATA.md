# 論文・データ・解析・記録を一緒に検証する

## この機能の完成範囲
公開資料の明示的な目録、決定的ZIP、ファイル別のSHA-256と容量、解析の参照関係を
論文の版とPDFハッシュに結び付けます。外側の `manifest.json` はschema 2となり、
既存RFC 3161処理はこの最終manifestを時刻証明の対象とします。
旧schema 1（論文だけ）の検証互換性は保持します。

**編集不能を実現する機能ではなく、信頼できる証拠と比べて改変を検出する機能です。**
ハッシュとmanifestを一緒に書き換えれば、単なる整合性チェックは通ります。
独立に入手したmanifest指紋、または独立に選択したCA/CRLによる時刻証明の検証が必要です。
論文PDFだけの指紋では、関連データの真正性は保証できません。

## 1. 公開データの宣言

ルートの `research.json` に公開するファイルだけを列挙します。フォルダー全体、
glob、URL参照の自動取得、記載した解析コマンドの実行は行いません。
テンプレートの空配列は「資料の宣言なし」を意味し、「研究にデータは不要」を保証しません。
`examples/research-data/research.json` は実在者と無関係な合成データの例です。

```json
{
  "schema_version": 1,
  "artifacts": [{
    "id": "measurements",
    "kind": "dataset",
    "visibility": "public",
    "path": "examples/research-data/measurements.csv",
    "version": "1",
    "title": "Synthetic measurements",
    "description": "time_s [s], value [dimensionless]. Invented example rows.",
    "license": "CC0-1.0",
    "sensitivity": "non-sensitive",
    "publication_approved": true
  }],
  "activities": []
}
```

`kind` は `dataset/code/protocol/environment/record/supplement`。
データの版、単位・列の意味・収集条件の説明、資料ごとのライセンスを記録します。
プロジェクトのMITライセンスを、参加者データ等に自動適用しません。

activitiesには `id/inputs/outputs/code/environment/command/description` を指定します。
参照はartifact idで結び付け、`paper` は現在の論文を表す予約済み出力です。
未知の参照、複数の生成元、循環、データをコードと偽る型は拒否します。
これは著者の申告を検査する機能であり、実験や解析の実行を証明しません。
`DECLARED_NOT_EXECUTED` として表示します。W3C PROVのentity/activityの考え方を参考に
していますが、PROV準拠の交換形式を実装したとは主張しません。

```bash
python scripts/research_bundle.py
python scripts/prepare_release.py --output dist
python scripts/verify_release.py dist
python scripts/timestamp.py stamp dist --policy timestamp-policy.json
python scripts/timestamp.py verify dist --policy timestamp-policy.json
```

既存の論文・引用ファイル等に `research-manifest.json` と `research-data.zip` が加わります。
公開データはZIP内の `artifacts/<id>/<filename>` に格納し、秘密ファイルを自動収集しません。
11資産（時刻証明込み）を公開前に再取得して照合するワークフローです。
最大100資料、公開ファイル25 MiB、合計100 MiB、JSON 1 MiB。ZIPは非圧縮固定形式で、
検証時には展開・実行せず、余分なファイル、重複、リンク、暗号化、圧縮、容量違反を拒否します。
これを超えるデータの外部保管・復元プロトコルは別途設計が必要です。

## 2. 健康記録・非公開記録

**原本・患者識別子・秘密の照合情報は、GitHubにも、このチャットにも渡さないでください。**
公開リポジトリにpushした時点で公開されています。Releaseの検査や.gitignoreでは
過去に公開した情報を取り消せません。`non-sensitive` の指定は人間の確認事項であり、
このツールは個人情報を自動判定・匿名化しません。分類が `health` 等の公開指定は拒否します。

原本はアクセス制御・暗号化・バックアップのある保管場所で管理し、下記はそこで実行します。
`/secure/...` は自分で用意した保管場所の例です。ツールは元ファイルを変更しません。

```bash
python scripts/private_record.py commit /secure/record.csv \
  --receipt /secure/record-v1.opk-private.json
```

出力は `id/kind/visibility/commitment` のみです。出力JSONのオブジェクトだけを
`research.json` のartifactsに加えます。ファイル名・生ハッシュ・診療日時・秘密nonceは
公開目録には入れられません。privateのkindは `record`、idは生成された `pr-...` です。
原本とreceiptはGit作業ツリーまたはキット内部では拒否します。隠しファイルだけに
依存する対策ではありませんが、ユーザーによる別経路のアップロードまでは防げません。

receiptはローカルに排他的に新規作成し、POSIXでは所有者だけ読書きできる0600とします。
WindowsのACL設定、暗号化保管、利用者認証、監査、法的適合性はこのコマンドの機能ではありません。
一つのファイルは100 MiB以下。全テストは合成値だけを使います。

### 照合手順

1. 取得した公開一式で、別途信頼したTSA policyを用いて `timestamp.py verify` を実行する。
2. その検証済み `research-manifest.json` から対象idのcommitment.digestを取り出す。
3. 原本と秘密receiptを保持する権限者が、下記をローカルで実行する。

```bash
python scripts/private_record.py verify /secure/record.csv \
  --receipt /secure/record-v1.opk-private.json \
  --commitment <検証済み目録から取得した64桁のdigest>
```

単にreceipt自身に書かれた値を期待値として使っても、独立な真正性確認にはなりません。
必要ならTSAとは別の信頼経路で受け取ったmanifestの指紋も検査できます。

```bash
python scripts/verify_release.py downloaded-release \
  --expected-manifest-sha256 <別経路で信頼した64桁のmanifest指紋>
```

### 秘密情報と限界

方式識別子 `opk-private-sha256-v1`。32バイトのOS由来乱数nonceを秘密として保存し、
固定ドメイン、ランダムid、区切り、nonce、原本SHA-256の32バイト値を結合してSHA-256を取ります。
文字列のUTF-8化や改行変換はせず、原本の正確なバイト列が対象です。
ドメインは `OpenPreprint-Kit/private-record/v1` のASCIIバイト列と末尾のNUL。
idのASCIIバイト列の後にもNULを置きます。nonceと原本ダイジェストはhex文字列ではなく生バイトです。

これは独自のバージョン付きcommitment形式であり、第三者暗号監査済みとはしていません。
通常の健康値の生ハッシュを公開すると候補値を総当たり比較できるため、その方式は採りません。
nonceを公開するとこの保護が弱まるので、receiptは秘密として暗号化保管・バックアップしてください。
receiptを失えば照合できません。公開idの数・関連付け・公開時点からの推測も残ります。
必要最小限の証拠だけを公開するか、公開自体をしない判断が必要です。

時刻証明は、証拠に対応する内容がその時点までに存在したことを支えるものです。
測定値の正しさ、実際の診療日時、記録者の本人性、データの網羅性、同意・倫理承認は証明しません。
電子カルテ、医療機器、個人情報保護認証、同意管理サービスではありません。

## 3. 訂正と記録の保持

原本を上書きせず、訂正内容を別ファイル・別private receipt・別artifact idとして保存します。
同じ論文の次版で、新しい資料版と導出関係を記録し、新たに時刻証明を取得します。
旧版のRelease、原本、receipt、証拠は保存します。最新ファイルだけを残すと旧版の照合はできません。
公開後の修正理由は既存のreview/correction記録にも追記します。後日の訂正記録を、元の
論文タイムスタンプが証明していたことにはしません。repo削除・未アンカー履歴の巻戻し・
証明書の長期満了への対策は、外部保存と長期検証の未完了ゲートに残します。

## 根拠となる仕様

- RFC 3161, DOI 10.17487/RFC3161: https://www.rfc-editor.org/rfc/rfc3161.html
- W3C PROV-Overview: https://www.w3.org/TR/prov-overview/
- Python secrets: https://docs.python.org/3.12/library/secrets.html

本実装の試験結果は指定コミットのCIを参照してください。実TSAや実際の健康記録で
運用実証したとは表示しません。
