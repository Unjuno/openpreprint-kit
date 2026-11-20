# OpenPreprint Kit — REPOSITORY_MAP

対象_MAIN SHA: `afbd55b475b7b583bc319a0f76c3555f0539b5fa`（2026-11-21 同期。旧基準 `811dc84367c88a81dbf062fa5d262f5d10a41180` は PR #51 の開始点として履歴保持）
作成日: 2026-11-17 (JST)。情報源: `gh api` / `gh repo list` の読取り専用照会 + ローカル evidence。
**本ファイルは台帳であり、削除・アーカイブ・PR/ブランチの閉鎖は一切行わない。**

## 1. 区分

| 区分 | 意味 | 置信境界 |
|---|---|---|
| A 本体 (kit) | ツール本体・テンプレート・正式受入基準 | 2026-11-21 緩和により v1.0.0 は所有者の最終承認で公開判断可能（未発行） |
| B 正式論文 | 所有者承認済みの公開論文・評価論文。不変Releaseで固定 | G2/P1 の対象。書換え禁止 |
| C 合成デモ | `pilot.py` が生成した受入演習用リポジトリ | 実論文ではない。削除しない |
| D 将来の独立保管先 | 別管理者の不変証拠ミラー。**現時点で実体なし** | 2026-11-21 の緩和で G5 の必須条件ではない（独立性 UNPROVEN） |

## 2. リポジトリ台帳

| repo | 区分 | 可視性 | Template | Release / tag | CI参照 | 依存 | 証拠URI |
|---|---|---|---|---|---|---|---|
| [Unjuno/openpreprint-kit](https://github.com/Unjuno/openpreprint-kit) | A 本体 | public | **有効** | **Release 0件 / tag 0件** (v1.0.0 未発行) | `validate (3.10/3.12)`, `quality/audit`, `CodeQL`, `first-paper-selftest`, `portable-first-paper`, `live-acceptance`, `website` | `requirements.lock` / `requirements-build.lock` (SHA-256固定)、Actions SHA固定 | [Issue #5 完了台帳](https://github.com/Unjuno/openpreprint-kit/issues/5)、[owner検証ログ](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-6863092530)、`docs/V1_ACCEPTANCE.md` |
| [Unjuno/openpreprint-kit-paper](https://github.com/Unjuno/openpreprint-kit-paper) | B 正式論文 (承認済み本短報) | public | 無効 | v1 id `444659219` (2026-11-13T19:39:48Z), v2 id `445442340` (2026-11-14T16:48:30Z)。各11資産、`draft=false immutable=true` | 同上9 workflow | 本体テンプレート由来 | [v1](https://github.com/Unjuno/openpreprint-kit-paper/releases/tag/v1) · [v2](https://github.com/Unjuno/openpreprint-kit-paper/releases/tag/v2) · `evidence/acceptance/first-paper-v1-release-observation-2026-11-14.json` |
| ~~Unjuno/openpreprint-kit-robustness-eval~~ | B 正式論文（履歴） | **削除済み (2026-11-21)** | — | v1 id `445445172`, v2 id `445446259`（各11資産、不変） | — | 本体テンプレート由来 | Release ID は履歴記録として保持 |
| ~~Unjuno/opk-demo-acceptance-a~~ | C 合成デモ（履歴） | **削除済み (2026-11-21)** | — | v1 id `444720691`, v2 id `444721932` | — | `pilot.py --publish-synthetic` が生成 | Release ID は履歴記録として保持 |
| ~~Unjuno/opk-demo-acceptance-b~~ | C 合成デモ（履歴） | **削除済み (2026-11-21)** | — | v1 id `444723249`, v2 id `444724581` | — | 同上 | Release ID は履歴記録として保持 |
| `ARCHIVER/EVIDENCE` (未作成) | D 将来の独立保管先 | — | **テンプレートにしないこと** | 未作成 | 未設定 | `github_mirror.py` / `custody.py` が想定 | `docs/GITHUB_PRESERVATION.md` の手順のみ。**実体なし = 独立性 UNPROVEN の根拠（必須ではない）** |

## 3. 合成デモの取扱い

- `opk-demo-acceptance-a/b` と robustness-eval は、所有者により **2026-11-21 に手動削除済み**（REST API で 404 を確認）。Release ID は履歴記録として保持する。
- アーカイブの可否: 削除により不変Releaseと証拠URIの解決性は失われている。再検証が必要な場合は Release ID と保全済み証拠を使う。
- 将来の独立保管先 (D) は既存のどの repo でもない。2026-11-21 の緩和により G5 の必須条件ではなくなった（独立性 UNPROVEN として明示）。

## 4. オープンPR / 古いブランチの分類

**一切の削除・閉鎖・force-pushは行わない。** 下表は提案のみ。

| repo | PR/ブランチ | 分類 | 理由 |
|---|---|---|---|
| 本体 | PR #50 Add GitHub collaborative peer review workflow | マージ済み (2026-11-19T17:13Z) | G6 のレビュー過程の記録と関係。2026-11-21 の緩和で独立人間の選任は必須ではない |
| 本体 | PR #19 bump pypdf 6.21.4→7.0.0 | クローズ (2026-11-19) | 7.1.0 を採用する PR #55 に置換。`requirements.lock` は pypdf 7.1.0 に再固定済み |
| 本体 | PR #9 bump bibtexparser 1.4.3→2.1.0 | マージ済み (2026-11-19T17:32Z) | `requirements.lock` は bibtexparser 2.1.0 に再固定済み、全 CI 成功 |
| 本体 | PR #10 verifiable paper/data provenance | 保持 | 既に `research_package.py` 等として統合済みの可能性。差分確認までは閉鎖しない |
| 本体 | `feature/*`, `fix/*`, `docs/*`, `gold/*`, `audit/*` の多数 (38本) | 延期 | 固定SHAへ統合済みの履歴ブランチ。削除は履歴証拠の毀損になり得る |
| 本体 | `dependabot/pip/*` | 解決済み | PR #9 / #55 でロック再固定・全CI成功。現在 open の dependabot PR はなし |
| 論文/デモ各 | dependabot PR #1–#4 (各4件、計16件) | 延期 | 公開済み不変Releaseには影響しないが、テンプレート由来の依存を更新すると再現性が変わる |
| 論文/デモ各 | `main` + 4 dependabot ブランチ | 保持 | `main` は公開ソースの基准 |

## 5. 確認日と限界

- 2026-11-17 に `gh api` で Release/tag/workflow/PR/branch を読取り専用で再確認。
- 本台帳は GitHub API の可視情報のみ。attestation の実検証・匿名再取得は実施済みだが、独立管理者の確認は行っていない（G2/G4/G5 は `独立性=UNPROVEN`）。
- 2026-11-21 時点で、#51 / #57 / #58 / #59 は所有者の承認によりマージ済み。v1.0.0 Release 発行と権限変更は所有者の最終承認待ち。
