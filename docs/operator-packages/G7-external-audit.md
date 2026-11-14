# 外部監査者パッケージ（G7）

**目的:** 実装者と独立した外部のセキュリティ/プライバシー監査者が、固定ソース SHA に対する監査を実施し、署名付き監査報告を提出する。
**注意:** AI によるセキュリティレビューは補助であり、署名付き外部監査報告には代替しない。

## 依頼文（所有者→外部監査者）

> 対象は OpenPreprint Kit（GitHub: Unjuno/openpreprint-kit、固定SHA `3e4d373c7e4376c6d732b61e74c0b8bf2ab22d7a`、main）です。スコープは下記の監査項目です。実署名のある監査報告（重大/高リスク未解決0、または未解決リストと理由）をお願いします。低リスクの指摘も歓迎です。監査中に公開拡大・仕様変更が判明した場合は停止し、私へ連絡してください。

## 対象の固定

- Repository: `https://github.com/Unjuno/openpreprint-kit`
- SHA: `3e4d373c7e4376c6d732b61e74c0b8bf2ab22d7a`
- 関連公開物（監査対象ではなく参照）: paper v1 / demo-a / demo-b（Issues #29-#35 のPR記録）

## 監査項目

1. **サプライチェーン**: requirements.lock / requirements-build.lock のハッシュロック、Actions の SHA 固定（40-hex + 版コメント）、SBOM 相当（pip-audit 2026-11-14: 0 vuln・22 deps、CodeQL 0 open alerts — 私の報告は新規検証の一資料にすぎません）。
2. **権限**: GitHub トークン種別・scopes・branch protection・Template 設定・Required approvals=0 の妥当性。
3. **公開物の不変性**: v1 Release の assets / attestation（`gh release verify` / `verify-asset`）が固定コミットと一致すること。
4. **暗号証拠**: RFC 3161（FreeTSA, CA pinned `2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438`, policy OID 1.2.3.4.1, nonce 128-bit, CRL 検証）の実装と運用。TSA/CA 失効時の前方更新（renewal.py）の実効性。
5. **署名鍵**: Ed25519 witness 鍵の管理区分（実装者鍵を持たないこと）、鍵指紋の別経路確認。
6. **研究データ・プライバシー**: 個人/臨床データが含まれないこと、研究データのライセンス分離、再識別リスク。
7. **改変・すり替え**: 署名/資産/manifest の改変・すり替え耐性（negative suite の再現: 20ケース誤受理0、spec 同梱）。
8. **すり替え・権限侵害**: 別リポジトリへのミラー改ざん、Release タグ置換、書込権限の濫用可能性。
9. **証拠寿命**: 証明書期限切れ・CRL 失効・CA 更新・証拠更新（TSA 再スタンプ）・旧失効証拠の保持期間・GitHub 障害時復旧（offline restore 手順: `preserve.py`）。
10. **保守責任**: 鍵ローテーション・点検周期・事故対応（漏えい/改ざん発覚時の停止条件）の責任者と手順。
11. **既知の限界**: AI による検証は独立監査ではない・同一オペレータ配下・単一端末・FreeTSA 依存・GitHub 単一基盤。これらを報告に明記してください。

## 技術試験の一部（監査と独立に再測定してよい）

- CI 全成功（main `3e4d373…`: Validate 3.10/3.12 367/367、Quality/audit、CodeQL、self-application、portable smoke）。
- 否定試験 20ケース: `negative-suite-2026-11-14/`（spec・results・PKI・runner）。
- 2環境正常検証: Windows + Ubuntu live-acceptance。
- 依存: pip-audit、ハッシュロック、Actions SHA 固定の再確認コマンドはリポジトリ内スクリプト/ワークフローを参照。

## PASS 条件

- 監査者の署名付き監査報告が Issue #5 に添付され、重大・高リスク未解決0（または未解決リストと Owner 承認）が明記されること。
- 証拠寿命試験（失効/CA更新/復旧）の実施または計画と責任者が確定すること。
- これが無い限り G7 は PASS にしない。低いリスクのみの報告でも正式な署名が無ければ PASS にしない。
