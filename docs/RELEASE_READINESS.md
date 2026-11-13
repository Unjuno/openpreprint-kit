# OpenPreprint Kit — 最新の運用受入状態

観測日: **2026-11-14 JST**。確認対象main: `f878210bdaafb68799045504ce56b22bfb11ab76`。

**判定: 第1論文v1の正式公開 P1 は BLOCKED。キットv1.0.0 P4 は NO-GO。**
ソフトウェアの試験合格を、本番の公開成功・第三者監査・長期保存の証明と混同しない。

唯一の合格基準は [V1_ACCEPTANCE.md](V1_ACCEPTANCE.md) の G0〜G7。作業の依存関係は [ROADMAP.md](ROADMAP.md)。
元の [2026-11-13 手動スナップショット](../evidence/acceptance/release-status.json) は**履歴として維持**し、その古い状態を現在の状態とは扱わない。

## 最新の確認できた事実

| 項目 | 状態・根拠 |
|---|---|
| 承認済み第1論文 | 著者表示 Unjuno、CC BY 4.0、論文版 v1。[承認PR #28](https://github.com/Unjuno/openpreprint-kit/pull/28)。PDF SHA-256: `0860b735379fb1b9b223f5d535442dae8421f456d7ae1c6bf6ce8d3141a1b07c`。再承認は不要 |
| コード統合 | 公開・復旧のPR #29、受入基準のPR #30、Git公開ソースと資産の照合PR #31、[OS共通ランチャーPR #32](https://github.com/Unjuno/openpreprint-kit/pull/32) はすべてマージ済み |
| Python 3.10 / 3.12 | 各 **362/362 テスト PASS**。[mainのCI](https://github.com/Unjuno/openpreprint-kit/actions/runs/43458103462) |
| OS互換 | Ubuntu 24.04、Windows Server 2025、macOS 15で各13のランチャーテスト＋13の**模擬GitHub公開**テスト成功。[OS別CI](https://github.com/Unjuno/openpreprint-kit/actions/runs/43458103658)。実公開を各OSで完了した証拠ではない |
| ほかのCI | [品質](https://github.com/Unjuno/openpreprint-kit/actions/runs/43458103253)、[CodeQLの実行](https://github.com/Unjuno/openpreprint-kit/actions/runs/43458103022)、[実原稿の自己適用](https://github.com/Unjuno/openpreprint-kit/actions/runs/43458103117) は成功。CodeQLの未解決警告数は別途確認が必要 |
| Template設定 | リポジトリAPIで `is_template=true` を確認 |
| ブランチ保護 | [protect-main](https://github.com/Unjuno/openpreprint-kit/rules/27207738) は Active。削除・force-push禁止、PR必須、`validate (3.10)`、`validate (3.12)`、`audit` 必須、最新base同期必須を読み戻した。Required approvals **0** は所有者の選択で、独立人間レビューの代替ではない |
| Immutable Releases | 所有者は有効化済みと申告。現在のGitHub接続からこの設定の管理API読戻しはできない。専用論文repo作成後に公開前/公開後で検証が必須 |
| 論文公開 | `Unjuno/openpreprint-kit-paper` はAPI GETで404。専用論文v1の公開Releaseは未作成／未検証。開発repoのReleaseも0件 |
| 公開前の証拠ZIP | [2026-11-14 再検証記録](../evidence/acceptance/prepublication-recheck-2026-11-14.json)。承認PDF一致、ZIP指紋一致、別途取得したFreeTSA署名付きCRLでRFC3161検証 **PASS**、復元 **PASS**、誤指紋・改変ZIP・誤CA指紋の3ケースはすべて拒否。公開時刻の証明ではない |
| 証人・保管・監査 | 独立観測者、別管理保管者、独立セキュリティ/プライバシー監査者の署名付き受入証拠は未取得 |

## G0〜G7 の判定

| ゲート | 判定 | 未達の必須証拠 |
|---|---|---|
| G0 コード・配布品質 | PARTIAL | 最終リリース対象SHAの警告トリアージ、独立承認、重大/高リスク未解決0の証拠 |
| G1 所有者設定・再利用 | BLOCKED | **テンプレート由来**の異なる公開論文repo 2件、各新repoの不変設定・保護/必須レビューの読戻し。元repoのTemplate/branch保護は確認済み |
| G2 実公開・版管理 | BLOCKED | 2 repo × 2版の計4 immutable Release、全資産のattestation、匿名取得・旧版保持 |
| G3 TSAと否定試験 | PARTIAL | **実際の公開4版**に結びつく新時刻証明、2環境8回以上の正常検証、固定20異常ケース。今回の旧・公開前証拠の検証だけでは不可 |
| G4 独立公開観測 | BLOCKED | 別管理者/鍵/環境による4つの署名・時刻証拠と鍵指紋 |
| G5 複製・オフライン復元 | BLOCKED | 別管理GitHub不変ミラーと実公開した4版の独立したオフライン復元 |
| G6 人間の編集・権利 | PARTIAL | 権利・同意・COIの記録、人間レビュー1件、訂正1件・撤回1件の演習 |
| G7 独立監査・証拠寿命 | BLOCKED | 独立セキュリティ/プライバシー監査、失効・更新・長期証拠・保守責任の試験と承認 |

## 最短の次工程

**R02 → R03（P1）を優先する。新規機能は増やさない。**

- **実行可能な準備は済み:** 第1論文の承認済みPDFと証拠ZIPはソースに保存済み。最新版でハッシュと現行CRL下の署名検証を再実行済み。公開プログラムはWindows/macOS/Linuxで模擬テスト済み。
- **不可欠な所有者実行:** GitHubアカウントの「新しい公開repoの作成」と「新repoのAdministration」ができる認証済み環境。接続済みGitHubコード操作には作成/管理のAPIがなく、以前のDesktop Commander環境には `gh` と所有者認証がなかった。権限を迂回しない。秘密情報をチャットに貼らない。
- **公開手順:** [FIRST_PAPER_QUICKSTART.md](FIRST_PAPER_QUICKSTART.md) のOS共通 `scripts/publish_first_paper.py` を使用する。プログラムが新repoを**テンプレートから作成**し、immutable設定、承認PDF、全資産、**新しい**TSA、attestation、匿名取得、復元を検証する。既存repo・既存Releaseへの破壊的再実行を拒否。
- **運用上の外部要件:** 本番P1後、別管理の観測者/保管者/監査者を募集・選任し、P2〜P4を別の終了条件として実施する。

注意：旧証拠の `source_claim=null` と事前TSAを、公開済み証明へ読み替えてはいけない。新公開先のmanifestには新TSAが必要。実装者と同一主体の検査は「独立した人間の監査」ではない。CodeQL成功は警告0件を意味しない。

過去の履歴は [旧状態文書](https://github.com/Unjuno/openpreprint-kit/blob/7b1fc1d34ede8aebeb01bd869350ef2140be528e/docs/RELEASE_READINESS.md) に保存されている。
