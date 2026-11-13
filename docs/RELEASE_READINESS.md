# OpenPreprint Kit — 現在の受入状態

確認日: **2026-11-13**。対象main: `7b1fc1d34ede8aebeb01bd869350ef2140be528e`。

**第1論文公開: 未完了。キットv1.0.0: NO-GO。ロードマップ文書の完成と混同しない。**

本書は状態記録であり、合格条件は[V1_ACCEPTANCE.md](V1_ACCEPTANCE.md)のG0〜G7だけを使う。実行順は[ROADMAP.md](ROADMAP.md)。詳細スナップショットは[release-status.json](../evidence/acceptance/release-status.json)。

## 確認した事実と未確認事項

| 対象 | 確認結果・出所 |
|---|---|
| 第1論文の承認 | Unjuno / CC-BY-4.0 / v1は確定済み。[PR #28](https://github.com/Unjuno/openpreprint-kit/pull/28)。再確認は不要 |
| mainの検証 | 303件の基準回帰結果と5ワークフロー成功は既存実行の証拠。[検証CI](https://github.com/Unjuno/openpreprint-kit/actions/runs/43279522763)。今回の文書編集で新たに全試験を実行したという意味ではない |
| 本稿v1の実TSA・復元 | [run 43279522755](https://github.com/Unjuno/openpreprint-kit/actions/runs/43279522755)。候補の存在証拠であり公開証拠ではない |
| 公開コード | [PR #29](https://github.com/Unjuno/openpreprint-kit/pull/29)は未マージ、head `4905139950d07d7f43cbebfb3d581e734261e9ad`。4 CI成功。実GitHub公開を代行した証拠ではない |
| Release | 開発リポジトリのGET /releasesは0件。予定の専用論文リポジトリでの実公開は未実証。全アカウントにReleaseがないという主張ではない |
| Template | 開発リポジトリのis_template=false。所有者の設定待ち |
| 管理設定 | branch protectionと未作成公開先の不変設定は、本確認ではUNKNOWN。取得権限不足を設定不在に読み替えない |
| CodeQL | 実行成功と警告0件は別。警告トリアージ・人間の独立監査は未確認 |
| GitHub保存 | ミラー・復元コードと前方更新は実装済み。別管理者による実ミラーと長期運用は未実証 |

## G0〜G7の状態

| ID | 状態 | 残る終了証拠 |
|---|---|---|
| G0 | PARTIAL | 公開コードの最終レビュー、RCの全試験、CodeQL警告と高リスク指摘の実確認 |
| G1 | BLOCKED | Template有効化、2テンプレート由来repo、公開前不変設定、保護ブランチ/必須レビューの読戻し |
| G2 | BLOCKED | 専用論文repoの4不変版、全資産attestation、旧版維持、匿名再取得 |
| G3 | PARTIAL | 実公開4版に結び付く新TSA、8正常検証、固定20否定ケースの実行記録 |
| G4 | BLOCKED | 独立観測者の選任・4署名記録・別経路の鍵指紋確認 |
| G5 | BLOCKED | 別管理GitHubミラー、実ダウンロード4版のオフライン復元、保守責任 |
| G6 | PARTIAL | 著者/ライセンスは承認済み。人間のレビュー/COI/訂正/撤回演習は未実施 |
| G7 | BLOCKED | 実装者と別の監査、旧失効証拠と証拠更新の運用試験、重大/高リスク指摘0 |

## 直近の優先順

1. 承認済みPDFと証拠を指紋付きで確保する。元のCI成果物の期限は**2026-11-27 03:26:50 JST**。
2. PR #29の通常repo作成とG1のテンプレート由来要件の違いを公開前レビューで解消し、最終CI後に統合する。
3. 所有者が自分で許可した方法で権限操作を行い、第1論文を発行・再取得する。Desktop Commanderは使わない。作成・管理操作の制約を回避しない。
4. 並行して独立観測者・保管者・外部監査者を選任する。担当者未決定は具体的なBLOCKEDであり、コード追加では閉じない。

以前の独自番号G1〜G7は廃止。履歴は[更新前RELEASE_READINESS](https://github.com/Unjuno/openpreprint-kit/blob/7b1fc1d34ede8aebeb01bd869350ef2140be528e/docs/RELEASE_READINESS.md)を参照する。新しい証拠が出たら対象SHA・出所・判定者を記録して本書とIssue #5を更新する。基準自体は書き換えない。
