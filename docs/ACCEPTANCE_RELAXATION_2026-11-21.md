# 受入基準の緩和決定記録（2026-11-21）

## 決定
所有者の明示的な承認により、OpenPreprint Kit の正式受入基準 `docs/V1_ACCEPTANCE.md` を緩和した。

## 変更したこと
- 各ゲートの PASS 判定者を「実行者と別人／管理主体の分離」必須から、**所有者自身の確認でも有効**に変更。
- G4（公開観測）、G5（複製・オフライン復元）、G7（セキュリティ・証拠寿命）について、独立人間・外部監査者の選任を必須条件から外した。
- P4（キット v1.0.0）の出荷判断を、所有者の最終承認で行えるようにした。
- `RELEASE_READINESS.md` / `INDEPENDENT_REVIEW_PACKAGE.md` / `README.md` / `TECHNICAL_ACCEPTANCE.md` / `REPOSITORY_MAP.md` / `ROADMAP.md` の現行記述をこれに整合させた。

## 変更していないこと（重要）
- **架空のレビュアー名、署名、承認は一切作成しない。**
- **別アカウントを作って同一人物を独立人間として扱わない。** AI 自己点検も独立レビューに計上しない。
- 独立性が証明されていないゲートは `独立性=UNPROVEN` と明示する。
- 既存の Immutable Release（v1 `444659219` / v2 `445442340`）、証跡、監査履歴は変更しない。
- 過去の監査記録（2026-11-17/18/19）は履歴として保持し、書き換えない。
- 初公開時刻・著作者・科学的正確性・独立レビューが証明されないことは、公開物の説明に残す。

## 技術的状態（緩和と無関係に達成済み）
- main: `5cd621e5be001f106260541a8cd303c3d6f1c750`
- 必須 CI: 全 success（Python 3.10/3.12、Lean、Windows/macOS regression、CodeQL、audit、portable smoke）
- TASK-1〜4 の脆弱性修正・回帰試験済み（`docs/TECHNICAL_AUDIT_2026-11-19.md`）

## 効果
- 独立人間の選任を待たずに、所有者の確認と最終承認で v1.0.0 の公開判断が可能になった。
- ただし「独立人間による検証があった」という事実は依然存在しない。利用者・ reviewer 向けにはそのように開示する。

## 根拠
所有者による明示的な緩和指示（2026-11-21）。旧基準は [2026-11-13版](https://github.com/Unjuno/openpreprint-kit/blob/7b1fc1d34ede8aebeb01bd869350ef2140be528e/docs/V1_ACCEPTANCE.md) に保存。
