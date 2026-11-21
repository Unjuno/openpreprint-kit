# 品質証拠の固定記録（2026-11-21）

目的: 「技術的に完成している」「品質が確認されている」という主張を、原ログと固定値へ結合して証明する。
**本記録は v1.0.0 の公開ではない。** 公開は所有者の最終承認を別途要する。
独立性は `UNPROVEN`（独立人間レビューは未実施）。架空レビュアー名によるAI自己点検、およびアカウントの作り分けは独立レビューに計上しない。

## 1. 固定対象

| 項目 | 値 |
|---|---|
| main | `f67dff9bb0cd6b45c9133db98d58d0f6acd16b4d`（PR #60 merge commit） |
| 技術検証の基準 SHA | `afbd55b475b7b583bc319a0f76c3555f0539b5fa` |
| tree hash（基準 SHA） | `dfb0256d628c7dbc30ec8298536e20b9c070b41b` |
| source zip SHA-256（基準 SHA） | `9af1e73b7b3580ec864ca3564c043b368a48da6e7b34e337376d6a1abd919452`（`git archive --format=zip --prefix=openpreprint-kit-afbd55b/`，再計算で一致確認） |

## 2. 必須 CI（原ログ）

main `f67dff9` の check-runs。すべて `success`。

| Check | 原ログ |
|---|---|
| validate (3.10) | https://github.com/Unjuno/openpreprint-kit/actions/runs/44811051571/job/136547370313 |
| validate (3.12) | https://github.com/Unjuno/openpreprint-kit/actions/runs/44811051571/job/136547369754 |
| audit | https://github.com/Unjuno/openpreprint-kit/actions/runs/44811051509/job/136547370370 |
| CodeQL Python | https://github.com/Unjuno/openpreprint-kit/actions/runs/44811051525/job/136547370339 |
| lean | https://github.com/Unjuno/openpreprint-kit/actions/runs/44811051634/job/136547369896 |
| windows-regression (3.12) | https://github.com/Unjuno/openpreprint-kit/actions/runs/44811051509/job/136547370403 |
| macos-regression (3.12) | https://github.com/Unjuno/openpreprint-kit/actions/runs/44811051509/job/136547369858 |

取得方法: `gh api repos/Unjuno/openpreprint-kit/commits/f67dff9bb0cd6b45c9133db98d58d0f6acd16b4d/check-runs`

## 3. 試験結果（ TECHNICAL_ACCEPTANCE.md に記録済み）

- 全 unittest: 複数環境で OK（Windows / macOS / Ubuntu、Python 3.10 / 3.12）
- 新規回帰試験: 18/18 PASS（AUD-01〜17 + AUD-11 マージ改変ケース）
- Hypothesis 特性: 7/7 PASS（各 100–150 examples）
- Python vs Lean 差分: 33/33 MATCH
- Lean: `lake build` 成功、`sorry/admit/axiom` なし（CI で毎回再実行）
- CodeQL: 0 alerts
- TASK-1〜4 の脆弱性修正と回帰試験: 完了（`TECHNICAL_AUDIT_2026-11-19.md`）

## 4. 公開物（変更なし）

| リポジトリ | Release | ID | Immutable |
|---|---|---|---|
| openpreprint-kit-paper | v1 | `444659219` | true |
| openpreprint-kit-paper | v2 | `445442340` | true |

旧 robustness-eval / demo リポジトリは 2026-11-21 に所有者が手動削除済み（REST API で 404 確認）。Release ID は履歴として保持。

## 5. 未達・未証明

- 独立性: `UNPROVEN`（独立人間レビューは未実施。架空レビュアー名・別アカウントは計上しない）
- 時刻証明の限界: RFC 3161 の署名時刻は「その時刻に当該ダイジェストが存在・投稿されていた」ことを証明するが、査読者の本人確認・独立性・真正性は証明しない。著名な人物が自身のアカウントで査読した場合でも不正の可能性は残る。アカウント由来の記録は存在時刻の証拠として扱い、独立レビューの証明として過度に依存しない（[REVIEW_POLICY.md](REVIEW_POLICY.md) の注意書き参照）
- v1.0.0: **未発行**。所有者の最終承認待ち
- 初公開時刻・著作者・科学的正確性・長期保存: 証明対象外

## 6. 判定

技術的品質ゲート: **達成**（CI 7/7 success、重大・高リスク未解決 0、形式検証・回帰試験あり）。
正式受入: 緩和基準で全ゲート PASS／独立性 UNPROVEN。公開判断は所有者の最終承認による。


## 7. 最終 main の固定値（2026-11-21）

- main: `789c5d8afaf275745fb81569542b7f851aaf475a`
- source zip SHA-256（`git archive --format=zip --prefix=openpreprint-kit-789c5d8/`）: `b3af6ba5e6e1baaf054672b4117582cda07d20a8d72c1c7f59dcc30661de201d`（3,298,796 bytes）
- ローカル再確認: `python scripts/validate.py` → `PASS: metadata checked (6 warning(s)); strict=False`、`python scripts/research_package.py --check` → `PASS: research catalog validated; assets=0`
- CI: 必須 7 チェックすべて success（§2 の原ログは `f67dff9` 時点。内容差分はドキュメントのみで、最終 main でも全件 success を確認）

## 8. v1.0.0 発行に必要な所有者側設定（未配置）

- **最新 main**: `f2e27950de50a497ca48351b985d60a0eb0a517a`（2026-11-21 の read-back）。
- `timestamp-policy.json`: main に未配置。信頼する CA と policy OID は独立に選定し、その CRL を検証して配置する必要がある。
- GitHub Actions secret `OPK_ADMIN_READ_TOKEN`: secret 名の登録を `gh secret list` で確認。値は読み取っていないため、token の有効性・実効 scope はこの確認だけでは証明しない。
- root `preprint.yaml`: `Untitled Preprint` / `v0` / `UNSPECIFIED` のテンプレート状態。公開する論文の実メタデータと発行版に更新する必要がある。
- Immutable Releases: GitHub REST API `GET /repos/Unjuno/openpreprint-kit/immutable-releases` の応答は `enabled=true`, `enforced_by_owner=false`。
- toolkit Release: `gh release list` は空。v1.0.0 は未発行。

Publish workflow は `timestamp-policy.json` と具体的な metadata を検証してから draft を作成する。上記の未配置項目が解消され、workflow の全検証が通るまでは v1.0.0 を起動しない。

## 9. 自己適用PDFの決定的再生成（PR #66 candidate）

対象コード: PR #66 head `23a53d8817e6f7baeeb5a42274eee1be9766f25c`。pull_request event の merge/source SHA: `926b68625c93500570c882b5065a93aaa191a528`。PR は証拠取得時点で open・未merge。

- [PR #66](https://github.com/Unjuno/openpreprint-kit/pull/66) は `xdvipdfmx` PDF trailer ID を source SHA 由来の固定値にし、self-application / live-TSA の両方で共有する。
- [PR self-application run](https://github.com/Unjuno/openpreprint-kit/actions/runs/44913111667) と [live RFC 3161 + fresh-runner run](https://github.com/Unjuno/openpreprint-kit/actions/runs/44913111617) は両方 PASS。両 artifact の原PDFは各 187,504 bytes、3ページ、SHA-256 `c9eeeadc9032afae737dbed8f3359d5eb3b6e572b3f817531d4094ee06625c2d` で一致。両者の byte 内容も一致した。PDF trailer `/ID` は両方 `2912651f0d1664500efe5a3382911804`。
- self-application の4否定ケース（manifest/PDF/research改変・citation欠落）はすべて拒否。PDFと本文の一致や著作者本人性は証明対象外。
- live TSA report: VERIFIED `2026-11-21T14:18:47Z`、pinned CA SHA-256 `2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438`、signed current CRL checked。Manifest SHA-256 `e310e0749acba90c884d4547a513b058c243ea4aa72c7bf8575b6b03f92958ed`; preservation ZIP SHA-256 `373f91151c00c30e3f1c23b31a2f72e5bd3182021edf4a1a1e0f065edabb90d5`.
- Fresh GitHub runner restored the preservation ZIP and passed release-bundle, timestamp and citation verification. No Release was created. GitHub artifacts retain for 14 days only; separate long-term/offsite custody is not established.
- Locked Python 3.12 Windows run of `test_first_paper_self_application.py`: 25 total, 23 passed, 2 skipped because Windows symlink privilege was unavailable. PR CI on the recorded head passed required validate 3.10/3.12, audit, CodeQL, Lean, Windows and macOS checks; this candidate has not been merged into main.

These results close the byte-level discrepancy for this tested source snapshot only. G0–G7 classifications remain those of the current readiness ledger; independence remains `UNPROVEN`. This evidence does not authorize or create toolkit v1.0.0.
