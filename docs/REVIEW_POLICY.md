# 査読・訂正・撤回の運用方針

本キットはプレプリントの公開と記録を支援する。学術誌でも査読認証機関でもない。
CIの成功、GitHubのApprove、ORCIDのチェックサム、AIの肯定的評価を
「独立した専門家による査読済み」の根拠にしない。

**注意書き（アカウントと時刻証拠）**: RFC 3161 / GitHub の時刻証明は、
「その時刻にその記録が存在・投稿されていた」ことの証明にはなる。
しかし、著名で信頼度の高い人物が**自身のアカウント**で査読したとしても、
本人なりすまし・利益相反・不正の可能性を完全に排除することはできない。
アカウント由来の査読記録は存在時刻の証拠として扱い、
査読の独立性・真正性の証明として過度に依存しないこと。
匿名の専門家レビューと偽った登録、および架空レビュアー名によるAI自己点検は行わない。

## 人間が担う判断
著者は原稿、データ利用許諾、倫理審査、利益相反、訂正に責任を持つ。
運用責任者はレビュー担当者の専門性・本人確認・利益相反を確認し、証拠と反論を読む。
レビュー担当者は対象版とPDFのSHA-256を記録し、方法、結果、再現性、限界を評価する。
独立性が必要な判断を著者自身が行った場合、独立した判断と表示しない。
AIによる点検は補助であり、匿名の専門家レビューと偽って登録しない。

## GitHub共同査読フロー

本フローはGitHub Issue・Pull Request・レビュー履歴を使った**公開・非匿名**査読です。秘密査読、査読者の専門性の自動認証、論文の科学的正しさの認証ではありません。Public repositoryで秘密または未許諾原稿を扱わないでください。

1. 著者または編集者が `.github/ISSUE_TEMPLATE/peer-review-round.yml` からラウンドIssueを作る。対象のimmutable Release URL、version、PDF SHA-256、期限、レビュー範囲を固定し、公開レビューへの同意を確認する。Issueにメール、患者情報、機密COIを載せない。
2. レビュアーは `.github/ISSUE_TEMPLATE/reviewer-interest.yml` から公開参加を申し出る。編集者が専門性とCOIを人間として確認し、必要なCOI詳細はGitHub公開Issue外の承認済み経路で扱う。最低2人の異なるGitHubアカウントを割り当てる。匿名性が必要ならこのPublic flowを使わない。
3. 各レビュアーが `.github/PULL_REQUEST_TEMPLATE/peer-review-report.md` を使い、公開許諾済みの報告と `reviews/record.json` への `review` eventを別々のPRで提案する。eventには同じversion、PDF SHA-256、`round_issue` URL、GitHub account、COI申告、報告ファイルのSHA-256を記録する。PR authorと報告者の一致を編集者がGitHub上で確認する。
4. 著者が `.github/PULL_REQUEST_TEMPLATE/author-response.md` から応答PRを作る。レビューevent IDへ回答し、`response` eventを追記する。報告や過去eventを編集・削除しない。
5. レビュアーとは別の編集者が `.github/PULL_REQUEST_TEMPLATE/editorial-decision.md` から判断PRを作る。`editorial_decision` eventの`decision`は `accept` / `revise` / `decline` / `pause`。判断理由を公開し、AIに採否を決めさせない。
6. `python scripts/research_record.py --round-issue ISSUE_URL --version VERSION --paper-sha256 PDF_SHA256` が、同一ラウンド・同一PDF hashに結びつく異なる2人以上のreviewer、著者応答、レビュアー/応答者とは別のeditor判断を検証する。通常CIはrecord形式、証拠hash、信頼したbaseからのappend-only履歴を検査する。これらは申告記録とGitHub上のアカウント履歴であり、査読の質の暗号学的証明ではない。
7. `revise` 後に本文バイトが変わる場合は、新しいRelease/versionと新しいレビューラウンドを始める。古いレビューは古いPDF hashに残す。

GitHub PRの **Approve** はコード差分への承認で、論文査読報告ではない。査読報告、著者回答、編集判断はそれぞれ独立した文書・eventとして残す。

### 動作確認コマンド

```bash
python scripts/research_record.py \
  --round-issue https://github.com/OWNER/PAPER/issues/123 \
  --version v1 --paper-sha256 64桁の小文字PDF_SHA256
```

合成fixtureでの試験はシステム動作の証明にのみ使い、実在論文の査読実績として登録しない。

`recorded_at` は記録者が申告したUTC時刻で、外部タイムスタンプではない。
`actor` も申告名であり、validatorは本人を認証していない。人間がGitHub accountとPR authorの対応を確認する。
`EDITORIAL_ACCEPTED`等の表示は編集判断eventの存在を示すにすぎず、科学的正しさや正式な査読認証ではない。

## 訂正・懸念表明・撤回
`correction` は訂正理由と置換先の新しい版・PDFハッシュを記録する。
`expression_of_concern` は未解決の重大な懸念を表示する。
`retraction` は対象版に撤回表示を付ける。後からレビューを追記しても撤回表示を消さない。
原則として既存PDF・報告・通知を残し、理由と新しい記録への参照を付ける。
プライバシーや権利侵害に関わる削除要請は運用責任者が別途扱い、公開してよい範囲で
除去理由の記録を残す。自動削除や法律上の判断はこのソフトウェアの機能ではない。

## 記録例（実在の査読ではない）
```json
{
  "id": "review-v1-001",
  "kind": "review",
  "version": "v1",
  "paper_sha256": "REPLACE_WITH_64_LOWERCASE_HEX",
  "round_issue": "https://github.com/OWNER/PAPER/issues/123",
  "recorded_at": "2026-10-31T00:00:00Z",
  "actor": "公開への同意を得た担当者名",
  "conflicts": "利益相反の有無と内容。未確認ならその旨を記載",
  "summary": "方法と再現性についての指摘",
  "evidence": [{"path": "reviews/evidence/review-v1-001.md", "sha256": "REPLACE_WITH_REPORT_SHA256"}]
}
```
報告書のハッシュは `sha256sum reviews/evidence/review-v1-001.md` 等で計算する。
この例のプレースホルダーは検査に通らない。架空のレビューを実績として登録しない。

## 限界
CIは信頼したbaseコミットに対する追記を要求する。しかし管理者による全履歴の
書換えに対する独立した証明ではない。研究記録は元の論文のRFC 3161証拠とは別であり、
外部署名・独立アーカイブへの固定は今後の受入項目である。機密査読はPublic Repositoryで行わない。

## 参照
- Crossref, Version control, corrections, and retractions:
  https://www.crossref.org/documentation/principles-practices/best-practices/versioning/
- COPE, Retraction guidelines: https://doi.org/10.24318/cope.2019.1.4
本方針は上記の認定や加盟を意味しない。
