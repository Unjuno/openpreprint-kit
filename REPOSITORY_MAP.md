# OpenPreprint Kit — REPOSITORY_MAP

対象_MAIN SHA: `afbd55b475b7b583bc319a0f76c3555f0539b5fa`（2026-11-21 同期。旧基準 `811dc84367c88a81dbf062fa5d262f5d10a41180` は PR #51 の開始点として履歴保持）
作成日: 2026-11-17 (JST)。情報源: `gh api` / `gh repo list` の読取り専用照会 + ローカル evidence。
**本ファイルは台帳であり、削除・アーカイブ・PR/ブランチの閉鎖は一切行わない。**

## 1. 区分

| 区分 | 意味 | 置信境界 |
|---|---|---|
| A 本体 (kit) | ツール本体・テンプレート・正式受入基準 | ソフトウェア v1.0.0 は未Release |
| B 正式論文 | 所有者承認済みの公開論文・評価論文。不変Releaseで固定 | G2/P1 の対象。書換え禁止 |
| C 合成デモ | `pilot.py` が生成した受入演習用リポジトリ | 実論文ではない。削除しない |
| D 将来の独立保管先 | 別管理者の不変証拠ミラー。**現時点で実体なし** | G5 の未達そのもの |

## 2. リポジトリ台帳

| repo | 区分 | 可視性 | Template | Release / tag | CI参照 | 依存 | 証拠URI |
|---|---|---|---|---|---|---|---|
| [Unjuno/openpreprint-kit](https://github.com/Unjuno/openpreprint-kit) | A 本体 | public | **有効** | **Release 0件 / tag 0件** (v1.0.0 未発行) | `validate (3.10/3.12)`, `quality/audit`, `CodeQL`, `first-paper-selftest`, `portable-first-paper`, `live-acceptance`, `website` | `requirements.lock` / `requirements-build.lock` (SHA-256固定)、Actions SHA固定 | [Issue #5 完了台帳](https://github.com/Unjuno/openpreprint-kit/issues/5)、[owner検証ログ](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-6863092530)、`docs/V1_ACCEPTANCE.md` |
| [Unjuno/openpreprint-kit-paper](https://github.com/Unjuno/openpreprint-kit-paper) | B 正式論文 (承認済み本短報) | public | 無効 | v1 id `444659219` (2026-11-13T19:39:48Z), v2 id `445442340` (2026-11-14T16:48:30Z)。各11資産、`draft=false immutable=true` | 同上9 workflow | 本体テンプレート由来 | [v1](https://github.com/Unjuno/openpreprint-kit-paper/releases/tag/v1) · [v2](https://github.com/Unjuno/openpreprint-kit-paper/releases/tag/v2) · `evidence/acceptance/first-paper-v1-release-observation-2026-11-14.json` |
| [Unjuno/openpreprint-kit-robustness-eval](https://github.com/Unjuno/openpreprint-kit-robustness-eval) | B 正式論文 (改変検出の実証評価) | public | 無効 | v1 id `445445172` (2026-11-14T16:53:04Z), v2 id `445446259` (2026-11-14T16:54:53Z)。各11資産、不変 | 同上9 workflow | 本体テンプレート由来 | [v1](https://github.com/Unjuno/openpreprint-kit-robustness-eval/releases/tag/v1) · [v2](https://github.com/Unjuno/openpreprint-kit-robustness-eval/releases/tag/v2) · `manuscripts/openpreprint-kit-robustness-eval/` |
| [Unjuno/opk-demo-acceptance-a](https://github.com/Unjuno/opk-demo-acceptance-a) | C 合成デモ | public | 無効 | v1 id `444720691`, v2 id `444721932`。各11資産、不変 | 同上9 workflow | `pilot.py --publish-synthetic` が生成 | [v1](https://github.com/Unjuno/opk-demo-acceptance-a/releases/tag/v1) · [v2](https://github.com/Unjuno/opk-demo-acceptance-a/releases/tag/v2) |
| [Unjuno/opk-demo-acceptance-b](https://github.com/Unjuno/opk-demo-acceptance-b) | C 合成デモ | public | 無効 | v1 id `444723249`, v2 id `444724581`。各11資産、不変 | 同上9 workflow | 同上 | [v1](https://github.com/Unjuno/opk-demo-acceptance-b/releases/tag/v1) · [v2](https://github.com/Unjuno/opk-demo-acceptance-b/releases/tag/v2) |
| `ARCHIVER/EVIDENCE` (未作成) | D 将来の独立保管先 | — | **テンプレートにしないこと** | 未作成 | 未設定 | `github_mirror.py` / `custody.py` が想定 | `docs/GITHUB_PRESERVATION.md` の手順のみ。**実体なし = G5 BLOCKED の根拠** |

## 3. 合成デモの取扱い

- `opk-demo-acceptance-a/b` は **削除しない**。公開演習の証拠であり、G2 の実証に使われた履歴である。
- アーカイブの可否: GitHub は public repo の archive を支持するが、**不変Releaseと証拠URIの解決性を失う**可能性がある。
  現時点では `archived=false` を維持し、アーカイブは **所有者の明示承認後** にのみ実施する。承認を求める提案は PR に添付する。
- 将来の独立保管先 (D) は既存のどの repo でもない。別アカウント・別管理の新規 repo を所有者が選任するまで G5 は BLOCKED のまま。

## 4. オープンPR / 古いブランチの分類

**一切の削除・閉鎖・force-pushは行わない。** 下表は提案のみ。

| repo | PR/ブランチ | 分類 | 理由 |
|---|---|---|---|
| 本体 | PR #50 Add GitHub collaborative peer review workflow | 延期 | G6 の独立人間レビュー要件と関係するが、レビュー担当の選任・承認が未 |
| 本体 | PR #19 bump pypdf 6.21.4→7.0.0 | 終了候補 (承認待ち) | `requirements.lock` は 6.21.4 固定。G0 の配布物固定と衝突。更新ならハッシュ再固定と全試験が必要 |
| 本体 | PR #9 bump bibtexparser 1.4.3→2.1.0 | 終了候補 (承認待ち) | 同上、2.1.0 は CFF 検証と無関係に破壊リスク |
| 本体 | PR #10 verifiable paper/data provenance | 保持 | 既に `research_package.py` 等として統合済みの可能性。差分確認までは閉鎖しない |
| 本体 | `feature/*`, `fix/*`, `docs/*`, `gold/*`, `audit/*` の多数 (38本) | 延期 | 固定SHAへ統合済みの履歴ブランチ。削除は履歴証拠の毀損になり得る |
| 本体 | `dependabot/pip/*` | 延期 | 上記PR#9/#19 と同じくロック固定との調整待ち |
| 論文/デモ各 | dependabot PR #1–#4 (各4件、計16件) | 延期 | 公開済み不変Releaseには影響しないが、テンプレート由来の依存を更新すると再現性が変わる |
| 論文/デモ各 | `main` + 4 dependabot ブランチ | 保持 | `main` は公開ソースの基准 |

## 5. 確認日と限界

- 2026-11-17 に `gh api` で Release/tag/workflow/PR/branch を読取り専用で再確認。
- 本台帳は GitHub API の可視情報のみ。attestation の実検証・匿名再取得・独立管理者の確認は行っていない (G2/G4/G5 は未達のまま)。
- アーカイブ/削除/Release発行/権限変更は所有者の明示承認を待つ。
