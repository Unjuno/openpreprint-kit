# 査読・訂正・撤回の運用方針

本キットはプレプリントの公開と記録を支援する。学術誌でも査読認証機関でもない。
CIの成功、GitHubのApprove、ORCIDのチェックサム、AIの肯定的評価を
「独立した専門家による査読済み」の根拠にしない。

## 人間が担う判断
著者は原稿、データ利用許諾、倫理審査、利益相反、訂正に責任を持つ。
運用責任者はレビュー担当者の専門性・本人確認・利益相反を確認し、証拠と反論を読む。
レビュー担当者は対象版とPDFのSHA-256を記録し、方法、結果、再現性、限界を評価する。
独立性が必要な判断を著者自身が行った場合、独立した判断と表示しない。
AIによる点検は補助であり、匿名の専門家レビューと偽って登録しない。

## 公開レビューの流れ
1. 問題・レビューのIssueを作成する。機密情報、個人データ、未許諾原稿は公開しない。
2. 合意した公開可能な報告書を `reviews/evidence/` にUTF-8の.md/.txtで追加する。
3. `reviews/record.json` のevents末尾に記録を追加する。報告書のSHA-256、
   対象版、対象PDFのSHA-256、記録者、利益相反、記録日時、要約を明記する。
4. PRのCIは形式・ハッシュ・履歴保存を検査する。運用責任者は内容を読んで判断する。
5. 著者の応答は `response` として別記録にする。反対意見を削除して合意を装わない。
6. 改訂版は新しいReleaseにする。v1のレビューをv2へ自動で移さない。

`recorded_at` は記録者が申告したUTC時刻で、外部タイムスタンプではない。
`actor` も申告名であり、ツールは本人を認証していない。`REVIEWS_RECORDED` は
報告の存在を意味し、科学的正しさや正式な査読完了の認証ではない。

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
