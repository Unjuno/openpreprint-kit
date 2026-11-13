# OpenPreprint Kit — 現在の受入状態

確認日: **2026-11-14 JST**。現行ソフトウェアの固定参照元: `5e49b38ede242ca4cafebf4e4aaab09c3bbac890`（後続の修正PRは別評価）。

**第1論文v1（P1）は正式公開済み。キットv1.0.0（P4）は NO-GO。**
論文の公開が成立したことと、再利用可能なキットの全受入条件が満たされたことは別の判定である。

唯一の受入基準は [V1_ACCEPTANCE.md](V1_ACCEPTANCE.md) の G0〜G7。実行順と担当は [ROADMAP.md](ROADMAP.md)。完了台帳は [Issue #5](https://github.com/Unjuno/openpreprint-kit/issues/5)。以前の [2026-11-13手動スナップショット](../evidence/acceptance/release-status.json) は履歴として保持し、未公開という古い判断を現在の事実に流用しない。

## P1 の公開と検証

| 対象 | 確認された値・根拠 |
|---|---|
| 専用論文repo | [Unjuno/openpreprint-kit-paper](https://github.com/Unjuno/openpreprint-kit-paper)。Public |
| v1 Release | [Release ID 444659219](https://github.com/Unjuno/openpreprint-kit-paper/releases/tag/v1)。2026-11-13T19:39:48Z公開。GitHub APIで `draft=false`, `immutable=true` |
| Releaseの対象ソース | `804cb76a4cf5eea65349fc7a8f01e2ce00e1176d`（論文repoのコミット。ツール本体のmainとは別） |
| 11資産 | GitHub RESTで11個の資産名・個別SHA-256が閲覧可能 |
| `paper.pdf` | 187,502 bytes、GitHub API digest `sha256:0860b735379fb1b9b223f5d535442dae8421f456d7ae1c6bf6ce8d3141a1b07c`。承認済みPDFと一致 |
| attestation / 新TSA / 匿名取得 / 保存ZIP復元 | [所有者の実行記録](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-6863092530)による成功。TSA署名時刻 `2026-11-13T19:39:35+00:00`。保存ZIP SHA-256 `66cccf52d0bdacc7f5bcf8ea4c23931824f94aaf715932d9aff282328752a5c4`。これらの暗号学的/復元試験を本記録の作成者が別環境で独立再実行したとは主張しない |
| 公開方法 | **最初の実行は Windows PATH 欠陥で `SOURCE_COMMITTED` にて FAIL**。所有者が継続を承認し、既存repoを削除・再作成せず同じコード経路で続行。失敗記録を保持し、`continuation-report.json` に残りの工程を記録 |
| 第三者保証 | 公開時刻の最初の瞬間、著作者本人確認、科学的正しさ、独立査読、証人/保管者の独立性はいずれも未証明 |

元のFAIL記録をPASSに上書きしない。実証済みの公開内容を変更・再発行しない。今後の確認は[読み取り専用の復元手順](FIRST_PAPER_QUICKSTART.md)による。

## ソフトウェア実装と所有者設定

- 公開・復旧ロジック（PR #29）、受入基準（#30）、公開ソースと資産の一致（#31）、Windows/macOS/Linux共通ランチャー（#32）および公開前証拠再検証（#33）はすべてmainへ統合済み。
- main `5e49b38ede242ca4cafebf4e4aaab09c3bbac890` に対して、[Python 3.10/3.12](https://github.com/Unjuno/openpreprint-kit/actions/runs/43461763874) 各362テスト、[品質](https://github.com/Unjuno/openpreprint-kit/actions/runs/43461763750)、[CodeQL実行](https://github.com/Unjuno/openpreprint-kit/actions/runs/43461763691) が成功。CodeQL実行成功は未解決警告0件を意味しない。
- 元repoのTemplateは有効、[protect-main](https://github.com/Unjuno/openpreprint-kit/rules/27207738) はActive。削除/force-push禁止、PR必須、Python 3.10/3.12と`audit`が必須。Required approvals=0は所有者が明示的に選択した暫定値で、G1の独立人間レビュー条件は未達。
- Windows実公開で発見された `venv/Scripts` 非継承と `cffconvert` の解決不備、cp932とUTF-8の違いは、ソフトウェアの修正・回帰テスト対象とする。**新たなCIが成功するまで修正済みとは断定しない。**

## G0〜G7の判定

| ゲート | 現状 | 残る終了証拠 |
|---|---|---|
| G0 コード・配布品質 | PARTIAL | Windows実運用欠陥の修正と最終SHAのCI、CodeQL警告のトリアージ、人間の承認、重大・高リスク未解決0 |
| G1 所有者設定・再利用 | PARTIAL | Template由来の公開論文repoを合計2件、新repo双方の不変設定、ブランチ保護/必須レビューの読戻し |
| G2 実公開・版管理 | PARTIAL | 現在1repo×1版。2repo×各2版の計4 Immutable Releases、全版attestation、匿名取得・旧版保持 |
| G3 TSA・否定試験 | PARTIAL | P1で実TSAを使用。4公開版、2環境で8回以上の正常検証、固定20異常系の受入結果が不足 |
| G4 独立公開観測 | BLOCKED | 管理/実行環境と鍵が独立した人間による4版の署名・時刻証拠 |
| G5 保存・オフライン復元 | BLOCKED | P1で所有者自身の復元記録あり。別管理のGitHubミラーと保管者、計4版のオフライン復元は未実施 |
| G6 人間の編集・権利 | PARTIAL | 著者表示/ライセンス承認は既存。実人間のレビューと権利/COI確認、訂正・撤回演習 |
| G7 独立監査・証拠寿命 | BLOCKED | 外部セキュリティ/プライバシー監査、旧CRL/CA/鍵更新と障害復旧の運用試験、保守責任者の確定 |

**P1 PASS（公開と所有者実行証拠の範囲）。P2 BLOCKED。P3 BLOCKED。P4 NO-GO。**

## 次の優先行動

1. P1のオリジナルFAIL記録・継続レポート・公開ZIPと独立して保存したSHA-256を、実行者とは別の管理下に複製する。管理主体が分かれない単なるコピーはG5の独立保管証明ではない。
2. WindowsのPATH/引用検証問題を修正し、Linux・Windows・macOSで暗号学的な模擬公開・負の対照・実CFF検証を再試験する。公開済みv1は再発行しない。
3. 2番目のTemplate由来repoと総計4版の受入（R04/R05）を、別の利用担当者の承認の下で実行する。
4. 独立観測者（R06）、別管理保管者（R07）、人間レビュー・外部監査（R08）の選任と、証拠寿命・事故対応の検証を進める。

論文の存在時刻・GitHubの公開日時・科学的妥当性・人間が独立して見た事実は異なる。AI自身の確認を「独立監査」とみなして全ゲートPASSにしない。
