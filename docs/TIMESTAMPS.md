# RFC 3161 — 使い方と検証範囲

## 何を証明するか

`manifest.json` の**正確なバイト列**をSHA-256で処理し、外部TSAにRFC 3161要求を送ります。
manifestにはPDF・書誌情報・引用情報など5資産のハッシュがあり、それらをまとめて結びつけます。
`timestamp.tsq`（要求）と `timestamp.tsr`（応答）は後から添付する2つのsidecarです。
manifestにsidecar自身を含めると循環するため、含めません。存在するだけで検証済みにはなりません。

検証成功が意味するのは「選択したCA/TSAを信頼するという前提で、対象内容に対する時刻の署名が有効」です。
一般公開、最初の投稿、著作権、研究の正しさ、ORCIDの所有権は証明しません。
自己署名のテストTSAも、利用者がそのルートを明示的に信頼すれば暗号検証は通ります。
したがって `VERIFIED` を「独立した公的機関のお墨付き」と読み替えてはいけません。

## 実装前提

Python 3.10以上、OpenSSL **3系**、`asn1crypto==1.5.1`、PyYAML 6系。
ASN.1構造の読み取りはasn1crypto、署名・証明書連鎖・EKU・失効検査はOpenSSLが担当します。
TLS接続はOS/PythonのHTTPS信頼設定、TSA署名検証は明示したCA bundleを使います。両者は別です。
検証機の時計が正しいことを前提とし、生成時刻が検証機の時計より300秒以上未来なら拒否します。

## 信頼ポリシーの設定

`timestamp-policy.example.json` を `timestamp-policy.json` にコピーして編集します。
サンプルURL/OID/指紋は実運用値ではありません。実際のTSAは自動選択されません。

| 項目 | 意味・条件 |
|---|---|
| `schema_version` | 整数1。booleanは不可 |
| `tsa_url` | 最終HTTPS POST URL。平文HTTP、資格情報、クエリ文字列、fragment、redirectは不可 |
| `ca_file` | 検証に必要な公開CA証明書PEM bundle。policyファイルからの相対パスまたは絶対パス |
| `ca_sha256` | **PEMファイル全体**のSHA-256。64桁小文字hex。別経路で信頼を確認する |
| `crl_file` | 全発行者の現在有効なCRLを連結したPEMファイル。失効・期限切れ・不足は拒否 |
| `policy_oid` | TSAが運用する実際のタイムスタンプpolicy OID。要求と応答で一致が必要 |
| `timeout_seconds` | 1〜60の整数。HTTPSのソケット操作と各OpenSSLプロセスのタイムアウト（秒） |

CA bundleは必要な中間CAとルートを含められます。応答中の証明書を新たな信頼ルートに格上げしません。
TSAが返さない証明書連鎖は、独立確認したCA bundleで補ってください。
HTTPにはPDF本体やGitHubトークンを送りません。ハッシュ、nonce、policy等を含む要求だけを送ります。
環境変数のHTTPプロキシは利用しません。応答は最大1 MiB、ジョブ全体は10分で停止します。

## 通常の利用

```bash
python -m pip install -r requirements.txt
python scripts/prepare_release.py --output dist
python scripts/timestamp.py stamp dist --policy timestamp-policy.json
python scripts/timestamp.py verify dist --policy timestamp-policy.json
```

最後のコマンドはネットワーク接続を行いません。ただし検証時点で新鮮なCRLを、事前に用意する必要があります。
`stamp` が失敗した場合、検証できないトークンは添付しません。既存証拠は上書きしません。

## オフライン取込・手動のTSAとのやり取り

```bash
python scripts/timestamp.py request dist --policy timestamp-policy.json --out request.tsq
# 選択したTSAにrequest.tsqを送り、RFC 3161の応答をresponse.tsrとして受け取る。
python scripts/timestamp.py attach dist --policy timestamp-policy.json \
  --query request.tsq --response response.tsr
python scripts/timestamp.py verify dist --policy timestamp-policy.json
```

`request.tsq` はbundle外に作ります。検証前に証拠をbundleへ移動しないでください。
検証した応答だけが `timestamp.tsq` / `timestamp.tsr` として追加されます。
途中でプロセス/マシンが停止し片方だけ残った場合、検証は失敗します。未公開bundleを作り直してください。

## 検証結果の読み方

| 出力 | 意味 |
|---|---|
| `status: VERIFIED` | 指定した信頼ポリシーの下で、内容・署名・連鎖・nonce・OID・CRL検査が通った |
| `tsa_time_utc` | TSAが署名したUTC生成時刻。検証機が測った投稿日時ではない |
| `accuracy_microseconds` | 署名されたaccuracyをマイクロ秒単位に変換。未記載は `null` |
| `existence_upper_bound_utc` | UTC生成時刻に申告accuracyを加えた保守的な上限。accuracy不明なら `null` |
| `revocation` | 現在有効な全連鎖CRLでの検証。歴史的な失効状態の保証ではない |
| `public_availability / authorship: NOT_PROVEN` | 一般公開と著作者資格は保証対象外 |

単位の確認例: `accuracy=seconds:1` は1,000,000マイクロ秒で、上限時刻は生成時刻の1秒後です。
この変換は自動試験で確認します。accuracy未記載を「誤差ゼロ」とみなしません。

CLIは成功時0、検証不能/不正入力時1（引数の使い方の誤りはargparseにより2）を返します。
`verify_release.py` の成功は内部のハッシュ整合だけです。時刻の成功とは別に判断してください。

## 現在の制約

CRLは**現在**有効でなければ拒否します。証明書も現在と署名時点の両方で有効期間内である必要があります。
期限切れの古い署名を長期保存証拠から検証する仕組み、OCSP、自動CRL更新、証拠更新、
独立観測は未実装です。`-no_check_time` 等で検査を省略して成功に見せる方針は採りません。
ローカル試験は一時CA/TSAとOpenSSLによる本物の署名検査です。HTTPS送信部はモックも使い、
公開TSAとの実通信を完了したとは主張しません。

## 一次資料

- RFC 3161: https://www.rfc-editor.org/rfc/rfc3161.html
- RFC 5816（署名証明書識別の更新）: https://www.rfc-editor.org/rfc/rfc5816.html
- OpenSSL ts: https://docs.openssl.org/3.0/man1/openssl-ts/
- asn1crypto TSP定義: https://github.com/wbond/asn1crypto/blob/master/asn1crypto/tsp.py
