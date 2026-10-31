# OpenPreprint Kit

**GitHubを論文公開の本体にする、再利用可能なプレプリント公開キット。**

現行ソフトウェアはv0.3統合候補です。**一般利用向けv1.0の運用受入は未完了**です。
[完成判定表](docs/RELEASE_READINESS.md)と[ロードマップ](docs/ROADMAP.md)に未達条件を示します。
論文の版番号（v1、v2）とキットのソフトウェア版番号は別です。

## 機能と限界

| 機能 | 状態 |
|---|---|
| メタデータ、ORCID、PDF存在/ヘッダー検査 | 実装。ORCID本人確認や完全なPDF構文検査ではない |
| CFF/BibTeX、metadata、manifest、SHA-256 | 決定的生成とオフライン整合検査 |
| RFC 3161 | 要求、HTTPS送信、署名/連鎖/nonce/OID/現在のCRLの検証 |
| GitHub公開 | 手動起動。公開前APIガードとdraft再ダウンロード検証 |
| レビュー/応答/訂正/懸念/撤回 | 版とPDF/報告書ハッシュに結合。CIで既存記録の変更を拒否 |
| 読者ページ | 静的HTML生成。撤回・懸念を明示。自動デプロイなし |
| 実TSA・実論文での運用、独立レビュー | 未確認/未実施 |
| 独立公開時刻観測、DOI、長期保存 | 未実装 |

## 利用開始

配布元のSettings → General → Template repositoryを有効にし、論文ごとに
Use this templateからPublic Repositoryを作ります。`preprint.yaml`と`paper/paper.pdf`を設定します。
初期状態は仮データとv0であり、そのまま公開できません。

```bash
python -m pip install -r requirements.txt
python scripts/validate.py --strict
python scripts/research_record.py
python scripts/prepare_release.py --output dist
python scripts/verify_release.py dist
```

Python 3.10以上、OpenSSL 3、PyYAML 6、asn1crypto 1.5.1を使用します。
ハッシュ整合検査と研究記録/読者ページの処理はPython標準ライブラリで動作します。

## 時刻証明と公開

[時刻証明手順](docs/TIMESTAMPS.md)に従い、独立に確認したCA/CRLとTSA方針から
`timestamp-policy.json`を設定します。同梱されていたという理由だけでCAを信頼しないでください。

```bash
python scripts/timestamp.py stamp dist --policy timestamp-policy.json
python scripts/timestamp.py verify dist --policy timestamp-policy.json
```

論文リポジトリでImmutable Releasesを有効にし、対象リポジトリの**Administration:read**を持つ
短命なtokenをActions secret **OPK_ADMIN_READ_TOKEN**へ設定します。ソースやチャットには貼りません。
完成原稿だけを対象にActions → Publish preprint releaseを手動起動します。

検査 → bundle → APIで公開前条件確認 → TSA → draft → 9資産を再取得・検証 →
immutability再確認 → 公開 → 公開後確認。権限不足・API障害・証明不成立では停止します。
確認と公開は原子的ではありません。公開後の失敗で公開を巻き戻せたとは主張しません。
[運用手順](docs/OPERATIONS.md)に復旧方法と必要権限を記載しています。

9資産はPDF、metadata JSON、CITATION.cff、BibTeX、manifest、SHA256SUMS、Release説明、
RFC 3161要求と応答です。旧7資産も整合検査できます。添付CFFだけではリポジトリの引用ウィジェットは設定されません。
`time_attestation: null`は時刻証拠をJSON内に埋め込まない意味で、外部sidecarを検証して判断します。

## レビューと訂正

[査読・訂正方針](docs/REVIEW_POLICY.md)に従い、公開許諾を得た報告を`reviews/evidence/`へ置き、
`reviews/record.json`へ追記します。名前と日時は申告情報であり、CI成功やAI評価を「査読済み」とは表示しません。
原版を消して修正せず、新版と理由を残します。機密査読は公開リポジトリで行いません。

```bash
python scripts/build_site.py downloaded-release --repository OWNER/PAPER --output site
```

ActionsのBuild reader siteでも生成できます。ページには撤回・懸念を表示し、原本を保持します。
ページ単独でタイムスタンプを検証したとは表示しません。研究記録は元の時刻証明とは別の未署名スナップショットです。

## テスト・問題修正

```bash
python -m unittest discover -s tests -v
```

試験は一時CA/TSAと合成データを使用し、GitHub APIの異常系は模擬応答で検査します。
実サービスの運用実証ではありません。CIはPython 3.10/3.12で検査し、試験済みソースとログを14日保存します。
[貢献手順](CONTRIBUTING.md)の再現テスト→修正→全件試験→人間のレビューを運用に組み込みます。
秘密情報は公開Issueへ出さず、[SECURITY.md](SECURITY.md)を確認してください。

## 保証とライセンス

存在時刻、一般公開時刻、著作者資格、科学的正しさは別です。[脅威モデル](docs/THREAT_MODEL.md)を参照してください。
学術出版（版・引用）、暗号学/PKI（署名・信頼）、保存・分散システム（独立観測）を分離しています。
ツールはMIT。論文・図表・データの利用条件は研究者が別に指定してください。
