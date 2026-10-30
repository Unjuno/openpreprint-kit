# OpenPreprint Kit

**GitHubを論文公開の本体にする、再利用可能なオープンソースのプレプリント公開キット。**

1論文 = 1 Public Repository。PDF、版ごとの書誌情報・引用、検証用manifest、
外部TSAによるRFC 3161の存在時刻証拠をGitHub Releasesにまとめます。

> **v0.2 開発版 / 全体は未完成。** 時刻証明のプロトコル・検証・公開ゲートを実装していますが、
> 公開TSAの選定と実接続、実論文による公開試験、一般公開時刻の独立観測、DOI・外部保存は未完了です。
> [完成条件付きロードマップ](docs/ROADMAP.md)を参照してください。

## 現在できること

| 機能 | 現状 |
|---|---|
| PDF・書誌情報の公開前検査 | 実装。ORCIDの形式/チェックサムも検査（所有権は認証しない） |
| CFF/BibTeX・metadata・SHA-256 manifest | 決定的な生成とオフライン整合検査 |
| RFC 3161 | 要求作成、HTTPS送信、応答取込、署名/連鎖/nonce/OID/CRLの検証 |
| GitHub公開 | 手動起動。未設定や証明失敗で停止。draft資産を再取得・再検証してから公開 |
| 独立した一般公開時刻・長期保存・DOI | 未実装 |

## 1. 複製して論文を置く

元リポジトリで **Settings → General → Template repository** を有効にしたうえで、
**Use this template → Create a new repository** からPublic Repositoryを作成します。
`preprint.yaml` のタイトル、著者、概要、版、論文ライセンスを編集し、`paper/paper.pdf` を置きます。
雛形は未完成の `v0` と仮データを持つため、そのままでは公開できません。

```bash
python -m pip install -r requirements.txt
python scripts/validate.py --strict
python scripts/prepare_release.py --output dist
python scripts/verify_release.py dist
```

この段階の成功はハッシュ整合の確認だけです。時刻の証明ではありません。

## 2. 外部時刻証明を設定する

[時刻証明の手順](docs/TIMESTAMPS.md)と[信頼設定](trust/README.md)に従い、
`timestamp-policy.example.json` を `timestamp-policy.json` にコピーして設定します。
独立確認したCAの指紋、TSAのpolicy OID、現在有効なCRLが必要です。
サービスを勝手に選ばないため、実運用用のTSA/CAはテンプレートに同梱しません。

```bash
python scripts/timestamp.py stamp dist --policy timestamp-policy.json
python scripts/timestamp.py verify dist --policy timestamp-policy.json
```

検証に使うpolicyを、検証対象の論文に付属していたという理由だけで信用しないでください。
**署名が有効であることと、署名者/TSAを信頼できることは別の判断です。**

## 3. GitHubで公開する

論文リポジトリの **Settings → General → Releases → Enable release immutability** を有効化します。
完成した論文だけを対象に **Actions → Publish preprint release → Run workflow** を実行します。
確認チェックを入れると、正常終了時には実際に一般公開されます。試しに押さないでください。

処理順は、厳密検査 → bundle生成 → TSA取得/検証 → draft作成 → 9資産アップロード →
ダウンロードしてバイト比較・時刻再検証 → 公開 → GitHubのimmutability状態確認、です。

**重要:** 公開前のimmutability設定は利用者の確認に依存します。公開後のAPI確認が失敗しても
公開を巻き戻せません。設定を確認してから起動してください。途中失敗時は未公開draftが残る場合があります。
同じ版を上書きせず、修正は新しい版にします。

## Releaseの9資産

| 資産 | 役割 |
|---|---|
| `paper.pdf` | 対象PDFの正確なコピー |
| `preprint-metadata.json` | 著者・論文情報・版・PDFハッシュ |
| `CITATION.cff`, `citation.bib` | 引用情報。CFFはRelease添付で、ルートの引用ウィジェットはまだ自動設定しない |
| `manifest.json`, `SHA256SUMS` | 内容のハッシュとサイズ |
| `RELEASE_NOTES.md` | 版、ライセンス、検証上の注意 |
| `timestamp.tsq`, `timestamp.tsr` | RFC 3161要求と応答。自分の信頼設定で再検証が必要 |

既存v0.1の7資産bundleは引き続き整合検証できます。
`preprint-metadata.json` の `time_attestation: null` はトークンをJSON内に埋め込んでいない意味です。
時刻証拠はsidecarを検証して判断し、このフィールドの有無から保証を推測しません。

## 動作環境・試験

Python 3.10以上、OpenSSL 3系、PyYAML 6系、asn1crypto 1.5.1。
ハッシュ整合だけの `verify_release.py` はPython標準ライブラリで動作します。

```bash
python -m unittest discover -s tests -v
```

暗号試験は一時CA/TSAの鍵を一時ディレクトリに作成します。公開TSAや実論文を使わず、
署名偽造・失効・期限切れ・違うCA・nonce不一致・内容改変などを検査します。
CIはUbuntu 24.04上のPython 3.10/3.12を対象にしています。

## 保証の境界とライセンス

存在時刻、一般公開時刻、著作者資格、論文の正しさは別です。
[脅威モデル](docs/THREAT_MODEL.md)と[ロードマップ](docs/ROADMAP.md)に未達事項を記載しています。
学術出版（版・引用）、暗号学/PKI（署名・信頼）、分散システム/保存（独立観測）を分離して設計します。

ツールとテンプレートはMIT。利用者の論文・図表・研究データのライセンスは別途設定してください。
