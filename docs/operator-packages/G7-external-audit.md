# 外部監査者パッケージ（G7）

**目的:** 実装者と独立した外部のセキュリティ/プライバシー監査者が、固定ソース SHA に対する監査を実施し、署名付き監査報告を提出する。
**注意:** AI によるセキュリティレビューは補助であり、署名付き外部監査報告には代替しない。

## 依頼文（所有者→外部監査者）

> 対象は OpenPreprint Kit（GitHub: Unjuno/openpreprint-kit、固定SHA `<FIXED_SHA_AT_AUDIT_START>`（監査開始時にGitHubの完全な40桁SHAを読み戻して記録し、その後は変更しない）、main）です。スコープは下記の監査項目です。実署名のある監査報告（重大・高リスクの未解決0件を受入条件とし、未解決があればFAIL/NO-GOと理由を報告）をお願いします。低リスクの指摘も歓迎です。監査中に公開拡大・仕様変更が判明した場合は停止し、私へ連絡してください。

## 対象の固定

- Repository: `https://github.com/Unjuno/openpreprint-kit`
- SHA: `<FIXED_SHA_AT_AUDIT_START>`（監査開始時点の完全な40桁のGitHubコミットSHA。署名付き報告にも同じSHAを記載）
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

- **監査者の署名付き監査報告があり、重大・高リスク未解決が0件であること。** 未解決の重大・高リスク指摘は、所有者が例外を承認してもG7をPASSにできない。未解決事項は理由・影響を報告してNO-GOとする。公開Issueには秘密情報を掲載せず、適切に制限された保管先の原文と、公開可能な監査要約・指紋を参照すること。
- 失効・期限切れ・CA更新・証拠更新・旧失効証拠保存・GitHub接続なしの実復元について、**実測した試験結果**、原ログ、対象資産・固定SHA・時刻、担当責任者と点検周期が記録されること。計画書のみではPASSにできない。
- これが無い限り G7 は PASS にしない。低いリスクのみの報告でも正式な署名が無ければ PASS にしない。
