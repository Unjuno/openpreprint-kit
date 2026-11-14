# OpenPreprint Kit v1.0.0 — ゲート証拠判定表（2026-11-14）

対象 main: `34aaa790697db1892db9bafd3f47b020e9a4ad8e` / 判定者: 所有者+AI（同一オペレータ、独立監査ではない） / 環境: Windows + GitHub Actions Ubuntu 24.04, macos-15, windows-2025.

**総合判定: P1（第1論文公開）= PASS / 正式4版（A v1/v2・B v1/v2）公開済み・G2骨格は技術完了 / P3 = BLOCKED / P4 = NO-GO**

| ゲート | 判定 | 根拠（実測） | 欠けているもの | 次に必要なこと |
|---|---|---|---|---|
| G0 コード・配布品質 | **PARTIAL** | main CI 全成功（Validate 3.10/3.12・Quality/audit・CodeQL・self-application・portable smoke）。Actions 全SHA固定。依存ハッシュロック（requirements.lock 321件）。CodeQL open alerts=0。pip-audit 0 vuln（22 deps） | レビュー担当の独立承認。Dependabot 有効化済み（owner 2026-11-14、open alerts=0） | owner が警告0件を読んで承認 + Dependabot の可否を記録 |
| G1 所有者設定・再利用 | **PARTIAL** | Template=true（toolkit）。template由来公開repo 3件（paper/demo-a/demo-b）、全て admin=true・immutable=true・template origin 一致。toolkit main: deletion/non_fast_forward 禁止・PR必須・必須checks strict。 Required approvals=0（owner選択、独立人間レビューではない） | paper/demo repo は branch rules なし。独立レビューの仕組み | owner が protection/approvals 現状を承認・記録 |
| G2 実公開・版管理 | **PARTIAL** | 正式4版公開・再検証完了（paper v1 444659219/804cb76a… + paper v2 RE_kwDOVtdYwc4ajOkk/6ec47ec5… + B v1 RE_kwDOVubJxs4ajPQ0/940bd77d… + B v2 RE_kwDOVubJxs4ajPhz/2631782a…）。すべて immutable・attestation VERIFIED・匿名DL一致・TSA PASS・v2公開後もv1不変。4版の詳細・再検証ログは Issue #5 (2026-11-14) | 発行者と別の検証担当による PASS 判定 | owner が検証担当を指名し Issue #5 で判定 |
| G3 TSA・否定試験 | **PARTIAL** | 5 Release の RFC 3161 再検証 PASS（TSA時刻実測）。2環境8回以上の正常検証（Windows + Ubuntu live-acceptance #43583374274）。固定20ケース23判定・誤受理0（再照合: spec 20/20 一致、false accept 0、古いCRLは `CRL has expired` で拒否）。CA指紋 2151b611… pinned、policy OID 1.2.3.4.1 | TSA運用担当の信頼選定承認。検証担当による最終 PASS 判定 | owner が TSA/検証担当を指名して判定 |
| G4 独立公開観測 | **BLOCKED** | 観測者候補・手順書完成（operator-packages/G4） | 著者と管理/鍵/環境を異にする実在の観測者 | 観測者選任 → 4版匿名取得・署名・RFC 3161・鍵指紋別経路確認 |
| G5 複製・オフライン復元 | **BLOCKED** | CUSTODY_LEDGER.json（304 files SHA-256）、CUSTODY_HANDOVER.md 作成済み（未保管） | 別管理保管者（別アカウント/組織/物理保管）。ミラー・4版復元未実施 | 保管者選任 → 受領・保管 → 別管理GitHubミラー → GitHub非接続4版復元 |
| G6 編集・個人情報管理 | **PARTIAL** | ライセンス分離文書化（CC BY 4.0 / MIT）。著者申告のみ。資料完成（G6 package） | 権利/同意/COIの人間確認。人間レビュー1件・訂正演習1件・撤回演習1件 | 編集担当選任 → 実施・記録 |
| G7 独立監査・証拠寿命 | **BLOCKED** | 固定SHA CI全成功・CodeQL 0・pip-audit 0（技術試験のみ）。監査 package 完成（G7）。証拠寿命試験の一部（renewal 試験）は CI で合成のみ実施 | 実装者と別の外部監査者・署名付き監査報告。失効/CA更新/復旧試験の実測と責任者確定 | 外部監査者選任 → 監査実施・署名 |

**凡例**: PASS=証拠+承認あり／FAIL=基準違反／PARTIAL=証拠不完全（人間承認欠落含む）／BLOCKED=担当者・権限・実証不能／UNKNOWN=観測不能。実行不能な項目は推測で埋めない。
