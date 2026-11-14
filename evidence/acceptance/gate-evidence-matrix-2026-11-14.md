# OpenPreprint Kit v1.0.0 — ゲート証拠判定表（2026-11-14）

対象 main: `84ca91cd6829e2d3d1c5a0f113f475c1d869bf73` / 判定者: 所有者+AI（同一オペレータ、独立監査ではない） / 環境: Windows + GitHub Actions Ubuntu 24.04, macos-15, windows-2025.

**総合判定: P1（第1論文公開）= PASS / P2 = PARTIAL（owner承認のsynthetic解釈下だが正式判定未了） / P3 = BLOCKED / P4（v1.0.0）= NO-GO。**

| ゲート | 判定 | 根拠（実測） | 欠けているもの | 次に必要なこと |
|---|---|---|---|---|
| G0 コード・配布品質 | **PARTIAL** | main CI 全成功（Validate 3.10/3.12・Quality/audit・CodeQL・self-application・portable smoke）。Actions 全SHA固定。依存ハッシュロック（requirements.lock 321件）。CodeQL open alerts=0。pip-audit 0 vuln（22 deps） | レビュー担当の独立承認。Dependabot 有効化済み（owner 2026-11-14、open alerts=0） | owner が警告0件を読んで承認 + Dependabot の可否を記録 |
| G1 所有者設定・再利用 | **PARTIAL** | Template=true（toolkit）。template由来公開repo 3件（paper/demo-a/demo-b）、全て admin=true・immutable=true・template origin 一致。toolkit main: deletion/non_fast_forward 禁止・PR必須・必須checks strict。 Required approvals=0（owner選択、独立人間レビューではない） | paper/demo repo は branch rules なし。独立レビューの仕組み | owner が protection/approvals 現状を承認・記録 |
| G2 実公開・版管理 | **PARTIAL** | 5 immutable Releases（paper v1 + demo×4）。全資産 attestation VERIFIED（gh release verify + verify-asset ×11/release）。匿名DL byte一致 ×5。offline integrity OK ×5。TSA PASS ×5。demo v1 は v2 後も不変。承認済み本短報 1件を含む。owner 2026-11-14「synthetic2repo解釈」承認 | 原基準は「2論文repo各2版」— paperはv1のみ、demo 2 repoはsynthetic。厳格なA案では正式4版に合致せず、紙面v2と別実論文v1/v2が不足 | **A案確定（owner 2026-11-14: 原基準維持）**。必要なのはpaper v2 **かつ** 第2実論文v1/v2の新規3件の実公開、権利・内容の著者承認、発行者と別の検証担当による判定（docs/operator-packages/G2-optionA-publication.md）。G2は基準変更なしではsyntheticでは埋まらない。
| G3 TSA・否定試験 | **PARTIAL** | 5 Release の RFC 3161 再検証 PASS（TSA時刻実測）。2環境8回以上の正常検証（Windows + Ubuntu live-acceptance #43583374274）。固定20ケース23判定・誤受理0（再照合: spec 20/20 一致、false accept 0、古いCRLは `CRL has expired` で拒否）。CA指紋 2151b611… pinned、policy OID 1.2.3.4.1 | TSA運用担当の信頼選定承認。検証担当による最終 PASS 判定 | owner が TSA/検証担当を指名して判定 |
| G4 独立公開観測 | **BLOCKED** | 観測者候補・手順書完成（operator-packages/G4） | 著者と管理/鍵/環境を異にする実在の観測者 | 観測者選任 → 4版匿名取得・署名・RFC 3161・鍵指紋別経路確認 |
| G5 複製・オフライン復元 | **BLOCKED** | CUSTODY_LEDGER.json（304 files SHA-256）、CUSTODY_HANDOVER.md 作成済み（未保管） | 別管理保管者（別アカウント/組織/物理保管）。ミラー・4版復元未実施 | 保管者選任 → 受領・保管 → 別管理GitHubミラー → GitHub非接続4版復元 |
| G6 編集・個人情報管理 | **PARTIAL** | ライセンス分離文書化（CC BY 4.0 / MIT）。著者申告のみ。資料完成（G6 package） | 権利/同意/COIの人間確認。人間レビュー1件・訂正演習1件・撤回演習1件 | 編集担当選任 → 実施・記録 |
| G7 独立監査・証拠寿命 | **BLOCKED** | 固定SHA CI全成功・CodeQL 0・pip-audit 0（技術試験のみ）。監査 package 完成（G7）。証拠寿命試験の一部（renewal 試験）は CI で合成のみ実施 | 実装者と別の外部監査者・署名付き監査報告。失効/CA更新/復旧試験の実測と責任者確定 | 外部監査者選任 → 監査実施・署名 |

**凡例**: PASS=証拠+承認あり／FAIL=基準違反／PARTIAL=証拠不完全（人間承認欠落含む）／BLOCKED=担当者・権限・実証不能／UNKNOWN=観測不能。実行不能な項目は推測で埋めない。
