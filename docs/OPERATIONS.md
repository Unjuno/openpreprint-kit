# 運用手順と障害時の処置

## 初回に人間が設定する事項
- 配布元をTemplate repositoryにし、論文ごとのPublic Repositoryを作る。
- 完成したPDF、正しい著者、論文ライセンスを設定する。
- 使うTSAと信頼するCA/CRLを選び、`timestamp-policy.json` を設定する。
- 論文リポジトリのImmutable Releasesを有効にする。
- 対象リポジトリだけを対象とする短命なGitHub App tokenまたはfine-grained tokenを準備。
  必要な権限は **Administration: read** と通常のMetadata: read。
  Actions secret **OPK_ADMIN_READ_TOKEN** に登録する。チャット、Issue、ソースに貼らない。
  このトークンは設定を変更するためではなく、公開前に設定を読むためだけに使う。
- `validate` の成功を必須にするbranch rulesetと、信頼できる人間のPRレビューを設定する。
  コードにCIを置くだけでは、管理者の直接pushや設定変更を防ぐルールは有効にならない。

## 公開前チェック
```bash
python scripts/validate.py --strict
python scripts/research_record.py
python scripts/prepare_release.py --output dist
python scripts/verify_release.py dist
```
GitHub ActionsのPublishを手動起動すると、APIで公開リポジトリ、現在の既定ブランチ、
immutability、版の未使用を確認する。その後TSAで証明し、draftを作成する。
ダウンロードした資産を再検査し、immutabilityを再確認してから公開する。
404以外のエラーを「未使用」と解釈しない。設定読取権限がなければ停止する。
確認と公開の間はGitHubの原子的トランザクションではない。公開後の確認も残す。
管理者の同時設定変更・意図的な操作を完全に防ぐとは主張しない。

## 読者ページ
既存のReleaseをローカルにダウンロードして実行するか、ActionsのBuild reader siteを起動する。
```bash
python scripts/build_site.py downloaded-release --repository OWNER/PAPER --output site
```
生成物は静的HTMLと原本のコピー。自動デプロイやPages設定変更は行わない。
Actionsでは`reader-site` artifactを得る。Pagesなどに配置する際は運用責任者が公開設定を行う。
撤回・懸念を上部に表示する。HTMLを実行せず、報告書はプレーンテキストとして表示する。
このページだけでタイムスタンプを検証したとは表示しない。古いページには後日の通知がない場合がある。

## 不具合の修正ループ
Issueで再現条件・対象版・期待結果・実結果を記録 → 失敗する回帰テスト → 最小修正 →
全テスト → 人間のコードレビュー → マージ → 必要なら新しいRelease → 再発防止策を追記。
論文の内容修正とツールの不具合修正を区別する。重大な研究結果の訂正は通知記録にも残す。

## 代表的な停止と処置
| 停止理由 | 処置 |
|---|---|
| Administration読取が403/404 | tokenの対象リポジトリ・権限・失効・immutability設定を確認。検査を無効化しない |
| 既定ブランチが変わった | 新しい内容を確認して、現在のコミットで起動し直す |
| TSA通信/証明書/CRL検査が失敗 | TSAの障害・時計・CAとCRLの出所と期限を確認。信頼pinを盲目的に更新しない |
| draftが残った | 公開状態と資産を確認し、運用責任者が未公開draftだけを整理する。公開版を上書きしない |
| 公開後immutability確認が失敗 | 既に公開済み。成功と扱わず、通知を出して設定・証拠を保全。公開前状態へ戻せたと主張しない |
| 記録が追記以外の変更 | 古い報告を修正せず、訂正イベントと新しい報告を追加する |

## 保存と復元
各公開版の9資産、信頼policyの出所、CA/CRLの取得記録、研究記録と報告書をGitHub外にも保存する。
バックアップは作るだけでなく、別ディレクトリ/別環境へ復元して整合検証する。
現在のタイムスタンプ検証は現在有効なCRLと証明書を要求し、数十年後の長期検証を保証しない。
CI artifactは14日で期限切れになり、永続アーカイブではない。

API根拠: https://docs.github.com/en/rest/repos/repos#check-if-immutable-releases-are-enabled-for-a-repository
