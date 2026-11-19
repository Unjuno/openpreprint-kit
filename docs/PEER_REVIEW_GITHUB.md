# GitHubで公開共同査読を行う

この仕組みはGitHub IssueとPull Requestを査読ラウンドの共有記録として使います。査読ラウンドは**公開・非匿名**です。ブラインド査読や、査読者の資格・独立性・論文の正しさを自動認証するものではありません。

## 参加者

- **著者:** 対象版を固定し、全報告に公開で回答する。
- **査読者:** 異なるGitHub accountから2人以上参加し、対象PDFを読み、公開許諾済みの個別報告を提出する。
- **編集者:** 査読者と著者応答者から独立して参加者・専門性・利益相反を確認し、判断理由を記録する。

GitHubのaccount名はプラットフォーム上の履歴を示しますが、実在人物の氏名・資格・専門性は証明しません。編集者が人間として確認してください。

## 一ラウンドの流れ

1. 論文リポジトリの **Issues → New issue → Public peer-review round** でIssueを作る。immutable Release URLとPDF SHA-256を必ず記録する。
2. レビュアーは **Reviewer interest (public)** で関心表明する。編集者が専門性とCOIを確認し、異なる2人以上を割り当てる。公開できないCOI詳細はpublic Issueに書かない。
3. 各レビュアーが **Pull requests → New pull request** で `.github/PULL_REQUEST_TEMPLATE/peer-review-report.md` を選択し、報告ファイルと `reviews/record.json` への追記を提案する。PR作成者とeventのreviewer accountが一致するか人間が確認する。
4. 著者が `.github/PULL_REQUEST_TEMPLATE/author-response.md` を使って point-by-point 応答と `response` eventを追加する。
5. 別の編集者が `.github/PULL_REQUEST_TEMPLATE/editorial-decision.md` で `accept`、`revise`、`decline`、`pause` の判断を追加する。
6. 各PRのCIで報告hash、JSON形式、過去eventが変わっていないことを確認する。最後にround validatorを実行する。

レポートはUTF-8 `.md` または `.txt` とし、査読者が公開に同意した内容に限定します。非公開査読が必要なら公開repositoryのIssue/PRを使わず、管理された適切な仕組みを別に用意してください。

## 完了条件の実行

```bash
python scripts/research_record.py \
  --round-issue https://github.com/OWNER/PAPER/issues/123 \
  --version v1 --paper-sha256 64桁の小文字PDF_SHA256
```

成功時はround Issue、版、PDF hash、異なるreviewer数、応答数、最新判断を出力します。二人の異なるreviewer、著者応答、reviewer/responderとは別のeditor判断が不足すると失敗します。

## ラウンドごとの記録

`reviews/record.json` の eventに、同一の `version`、`paper_sha256`、`round_issue` を設定します。各報告・応答・判断の公開証拠ファイルは `reviews/evidence/` に保存し、SHA-256を記録します。記録はappend-onlyです。実際のGitHub作成者とevent上の actor の対応は人が確認します。

本文のバイト列が変わった場合は新しいRelease/versionで新しいラウンドを始めます。前の版のレビューは以前のPDF hashに固定されます。

## 解釈上の注意

ラウンドvalidatorが `PASS` を返す意味は、必要な構造化eventが存在し、指定されたPDF hashとIssue URLに揃っていることです。身元、独立性、専門性、実際にPDFを読んだか、議論の質、科学的妥当性は認証しません。読者ページの `EDITORIAL_ACCEPTED` なども記録された人間の編集判断を表示するだけです。GitHub PRのApprove、CI成功、AI出力は査読報告や編集判断の代用になりません。
