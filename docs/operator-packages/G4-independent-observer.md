# G4 独立公開観測 — 実装整合の正規手順

**目的**：承認された**正式G2対象4版**を、著者・所有者とは別の実在の人間が、別管理環境と独立したEd25519秘密鍵により匿名取得・署名し、RFC 3161で署名済み観測記録に時刻証拠を付与する。

**前提**：G2 A案（変更されていない正式基準）では、既存第1論文v1に加え第1論文v2と第2実論文v1/v2が必要。Synthetic A/Bの5件を正式4版へ自動的に読み替えない。対象repo、タグ、期待ソースコミットと原指紋を**所有者以外の検証者が別経路で確定**する。正式対象が揃わない場合は、既存Syntheticの観測を予行演習として行えてもG4はBLOCKED。

## 観測者への依頼

> 著者/所有者と異なる管理者・実行環境・秘密鍵で、確定済みの4版を匿名HTTPS取得し、OpenPreprint Kitの既存`observation.py`で各版のEd25519署名とRFC 3161観測タイムスタンプを生成してください。秘密鍵を渡さないでください。公開鍵指紋は電話・対面等の別経路で検証担当へ伝え、各観測フォルダーと原資産の指紋を返してください。独立性・実行環境・時刻・結果を人間として署名してください。

## 実行前の準備（観測者のみ）

- 別管理のOSとPython 3.10以上、OpenSSL 3、リポジトリのハッシュロック依存を用いる。ログに認証情報・署名秘密鍵を残さない。
- TSA信頼ポリシーは観測者自身が別途選定した公開CA指紋・有効な署名付きCRLを用意し、JSONに相対指定されたCA/CRLファイルを`observation.py`から検証する。付属のアーカイブを自動的に信頼根にしない。
- 自分の保護されたディレクトリで`openssl genpkey -algorithm ED25519 -out witness-private.pem`および`openssl pkey -in witness-private.pem -pubout -out witness-public.pem`を実行する。秘密鍵ファイルへのアクセスを観測者だけに制限する。
- `openssl dgst -sha256 witness-public.pem`で公開鍵ファイルの正確なSHA-256を計算する。検証者に**別経路**で64桁の指紋を渡す。`witness-private.pem`はリポジトリ・Issue・観測出力に含めない。

## 正規CLI：1版ずつ実行する

次のコマンドは観測者が**自分の環境**で実行する例（Linux/macOSシェル）。`OWNER/PAPER`、`v1`、入出力ディレクトリ、信頼設定を正式対象に置き換える。Windowsでは引用符をPowerShell用に調整し、同等のCLI引数を渡す。

```bash
python scripts/observation.py record \
  --repository OWNER/PAPER --version v1 \
  --out /secure/observations/paper-v1 \
  --policy /trusted/tsa-policy.json \
  --signing-key /secure/keys/witness-private.pem \
  --timestamp-observation
```

生成出力には、匿名取得・元ReleaseのRFC 3161証拠を確認した`bundle/`、`observation.json`、`observation.sig`、`observation.tsq`、`observation.tsr`を**すべて**含む。公開鍵は観測フォルダーの**外側**で管理する（検証器はフォルダー内の余分なファイルを拒否する）。異なる版には別の出力ディレクトリを選ぶ。出力先の既存ディレクトリは上書きしない。

`observation.json`は実装が生成する**固定スキーマ**（`OBSERVATION_FIELDS`）のみを受け付ける。`signed_by`や`source_commit`の任意追加は禁止。ソース来歴は含まれる`bundle/preprint-metadata.json`の`source_claim`とmanifest等で検査される。手でJSONを組み立てない。

**観測RFC 3161の署名対象**：`scripts/observation.py`の`receipt_digest()`が、ドメイン分離と長さプレフィックスを使って**実バイトの`observation.json`とEd25519の`observation.sig`の両方**を結合したSHA-256。JSONだけをTSRへ送る手順とは異なる。改変・再署名後の差し替えは禁止。

## 独立した検証担当の確認

別経路で受け取った公開鍵指紋と、検証対象repo・tagを信頼入力として指定する。観測フォルダーは原状のまま読み込む。

```bash
python scripts/observation.py verify \
  --observation /secure/observations/paper-v1 \
  --public-key /trusted/witness-public.pem \
  --expected-public-key-sha256 INDEPENDENTLY_PINNED_64_HEX \
  --expected-repository OWNER/PAPER --expected-version v1 \
  --policy /trusted/tsa-policy.json \
  --require-observation-timestamp
```

受入検証は署名のみでなく、公開鍵ピン、版・リポジトリID、原ReleaseのTSA、bundleの全資産、`observation.sig`と観測TSQ/TSRの結合、独立性証拠を確認する。観測者の開始/終了時刻は**本人申告時計**であり、TSAは「署名済み主張の存在」を時刻で裏付けるだけ。初公開時刻・観測者の誠実性・著作権・科学的正しさは証明しない。

## PASS条件

- 正式G2対象4版それぞれについて、5構成要素が揃った観測出力、検証器PASS、別経路の鍵指紋、資産ダイジェスト、実行日時と環境が記録されていること。
- 観測者と著者の管理・鍵・実行環境の分離が実在する人間により確認され、独立した検証担当の署名付き判断がIssue #5から参照できること。
- 秘密鍵・機微データを公開しないこと。必要な公開情報（鍵の公開部分・証拠URI・要約・ハッシュ）と非公開の連絡情報を区別すること。

該当者が不在、正式な4版が不足、署名・TSA・独立性の証拠が欠落している場合、**G4はBLOCKED/PARTIALであってPASSではない**。

正本：`scripts/observation.py`、`docs/PRESERVATION_AND_WITNESS.md`、`docs/V1_ACCEPTANCE.md`。
