# OpenPreprint Kit — 現在の受入状態

更新日: **2026-11-15 JST**。記録時の基準コミット: `811dc84367c88a81dbf062fa5d262f5d10a41180`（最新 main は GitHub で確認）。

**第1論文v1 (P1) は正式公開済み。正式4版（2実論文repo×各2版）も公開・再検証済み。キットv1.0.0 (P4) は NO-GO。**
ソフトウェアの試験合格を、本番公開の成功・第三者監査・長期保存の証明と混同しない。

基準: [V1_ACCEPTANCE.md](V1_ACCEPTANCE.md) (G0–G7)。工程: [ROADMAP.md](ROADMAP.md)。完了台帳: [Issue #5](https://github.com/Unjuno/openpreprint-kit/issues/5)。過去のスナップショット [2026-11-13 manual status](../evidence/acceptance/release-status.json) は履歴としてのみ参照し、現在の判定には用いない。

## 実公開リリース（2026-11-14）

| # | Repository | Release | Release ID / タグ SHA | 公開時刻 | Immutable |
|---|---|---|---|---|---|
| 1 | [openpreprint-kit-paper](https://github.com/Unjuno/openpreprint-kit-paper) | **v1**（承認済み本短報、変更禁止） | 444659219 / `804cb76a4cf5eea65349fc7a8f01e2ce00e1176d` | 2026-11-13T19:39:48Z | ✓ |
| 2 | openpreprint-kit-paper | **v2**（実運用評価、AI支援執筆・所有者承認） | RE_kwDOVtdYwc4ajOkk / `6ec47ec58e9dc733956615343aad16caca4bb8ee` | 2026-11-14T16:48:30Z | ✓ |
| 3 | [openpreprint-kit-robustness-eval](https://github.com/Unjuno/openpreprint-kit-robustness-eval) | **v1**（改変検出の実証評価） | RE_kwDOVubJxs4ajPQ0 / `940bd77d02318e9d95fa5cb7db568804de2d1860` | 2026-11-14T16:53:04Z | ✓ |
| 4 | openpreprint-kit-robustness-eval | **v2**（追加実験: CRL鮮度対照・前方TSA更新） | RE_kwDOVubJxs4ajPhz / `2631782a109bf47572e4310ae0da32f26aec3de9` | 2026-11-14T16:54:53Z | ✓ |

- 各Releaseの全11資産の attestation（`gh release verify` / `verify-asset` ×11）・匿名DL byte一致・オフライン復元・TSA再検証は再実測済み。
- 論文 repo は事後的に branch protection を設定（deletion/force-push禁止、PR必須、必須 checks `validate (3.12)/(3.10)/audit`, strict=true）。事後設定は公開前保護の証明ではない。
- 第1論文専用ランナーの初回失敗（cffconvert PATH）は owner 承認後の同一コード経路継続で完了。FAIL 記録は保持。
- `publish_manuscript.py`（汎用ランナー）を PR #42 で統合。pre-flight 順序欠陥を PR #45 で修正。回帰テスト分離を PR #46 で完了。

## G0–G7 の判定（2026-11-15、自己評価＋実測証拠）

| ゲート | 判定 | 残る証拠・形
|---|---|---|
| G0 コード・配布品質 | PARTIAL | main CI 全成功（Validate 3.10/3.12・Quality/audit・CodeQL・self-application・portable smoke）。Actions SHA固定。依存ハッシュロック。CodeQL 0 alerts、pip-audit 0 vuln。**レビュー担当の独立承認が未**。Dependabot alerts は owner 承認で有効化済み（0件） |
| G1 所有者設定・再利用 | PARTIAL | 2つの論文 repo（paper / robustness-eval）＋ toolkit template を読戻し。Immutable=true、paper/robustness-eval ともに事後 branch protection 設定済み。Required approvals=0 は所有者選択であり独立人間レビューではない |
| G2 実公開・版管理 | PARTIAL | 正式4版（2実論文repo×各2版、承認済み本短報を含む）公開・attestation・匿名DL一致・v2後もv1不変を実証。**発行者と別の検証担当による判定が未** |
| G3 TSA・否定試験 | PARTIAL | 5版のRFC 3161再検証 PASS、2環境8回以上の正常検証（Windows + Ubuntu live-acceptance #43583374274）、固定20否定ケース誤受理0（spec固定・23判定）。TSA運用担当の信頼選定承認・検証担当の判定が未 |
| G4 独立公開観測 | BLOCKED | 別管理鍵・環境の実在観測者が正式4版を匿名取得・署名・RFC 3161。手順書: `docs/operator-packages/G4-independent-observer.md` |
| G5 複製・オフライン復元 | BLOCKED | 別管理保管者の受領・再計算・別管理GitHubミラー・GitHub非接続4版復元。台帳304 files完備（`CUSTODY_LEDGER.json`）だが未保管。手順書: `G5-custodian-handover.md` |
| G6 人間の編集・個人情報管理 | PARTIAL | ライセンス分離文書化済み・維持。人間の権利/COI確認・レビュー1件・訂正/撤回演習が未。手順書: `G6-human-review.md` |
| G7 独立セキュリティ・証拠寿命 | BLOCKED | 外部監査者による固定SHA監査・失効/CA更新/復旧の実測試験と署名。手順書: `G7-external-audit.md` |

**P1 PASS。P2（G2）は骨格実証済み・独立検証未。P3 BLOCKED。P4 NO-GO。v1.0.0 完成宣言はしません。**

## 残る作業（独立した人間が必要）

1. 検証担当による対象4版の G2/G3 判定と Issue #5 での署名記録
2. G4（独立観測者）・G5（別管理保管者）・G6（編集担当）・G7（外部監査者）の選任と実測
3. G0/G1 の独立承認（Required approvals=0 の妥当性含む）
4. 全 PASS 後に、キット本体 `v1.0.0` 不変 Release の発行（owner 承認）と再取得検証

## 文書の訂正履歴

- 2026-11-14: paper A v2 公開後の ER-1（解析集計ラベル誤り）・ER-2（B v2再現手順）・ER-3（ランナー pre-flight 順序欠陥）は `evidence/acceptance/erratum-2026-11-15-public-releases.md` に記録。公開済み asset は変更せず。
