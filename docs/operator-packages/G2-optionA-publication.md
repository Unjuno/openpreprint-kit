# G2 — 正式4版の現状、実論文B候補、受入手順

> **Historical state below is superseded as of 2026-11-29.** The second paper repository and three immutable Releases now exist. Current live Release IDs, tags, source SHAs, 11-asset counts, `gh release verify` results, and remaining G2 decision are in [ACCEPTANCE_SNAPSHOT_2026-11-29.md](../ACCEPTANCE_SNAPSHOT_2026-11-29.md). No existing immutable Release was changed. Do not follow the old “second repo missing / unpublished” steps as current instructions.

**正式なG2基準は変更しない。G2は現時点で `NOT CONFIRMED`。** この手順書は公開承認ではなく、原稿・権利・設定・実Releaseがそろう前に公開しない。既存Immutable Releaseは削除・変更しない。

## 正式基準と現在確認できたRelease

現行基準は [`V1_ACCEPTANCE.md`](../V1_ACCEPTANCE.md) のG1/G2。2つの実論文リポジトリに各2版、計4件以上のimmutable Releaseを要求し、最低1件は著者承認済み本短報である。v2後もv1資産を変えず、全Release・全資産のattestation、匿名取得、引用・研究資産の一致を検証する。所有者が判定できる。独立性は `UNPROVEN` と記録し、同一所有者の別アカウントを独立レビューに数えない。

| 実論文リポジトリ | Version | 状態と証拠 |
|---|---|---|
| `Unjuno/openpreprint-kit-paper` | v1 | Release ID `444659219`、target `804cb76a4cf5eea65349fc7a8f01e2ce00e1176d`。immutable/non-draft。2026-11-21 UTCの読戻しで11 assets、GitHub attestation、匿名asset digest、SHA256SUMS、release verifier、citation validation、RFC 3161が再検証済み。 |
| `Unjuno/openpreprint-kit-paper` | v2 | Release ID `445442340`、target `6ec47ec58e9dc733956615343aad16caca4bb8ee`。immutable/non-draft。上記同日読戻しで11 assets、GitHub attestation、匿名asset digest、SHA256SUMS、release verifier、citation validation、RFC 3161が再検証済み。v2の旧比較行は保存済みrelease-matrixにないため、過去matrixとの一致は主張しない。 |
| 第2の実論文 repo | v1 | `manuscripts/openpreprint-kit-robustness-eval/v1` に原稿候補・PDF・研究資産候補はある。著者/所有者承認待ち。独立repo/Releaseは現在解決できず、未発行。 |
| 第2の実論文 repo | v2 | 同 `v2` に追加実験を含む候補がある。著者/所有者承認待ち。独立repo/Releaseは現在解決できず、未発行。 |

paper v1/v2の全匿名取得・ハッシュ・release verify・RFC 3161結果は [`paper-v1-v2-anonymous-readback-2026-11-22.json`](../../evidence/acceptance/paper-v1-v2-anonymous-readback-2026-11-22.json)、SHA-256 `AD5ACFBF87E34E6C7AADFB2177FC7755EF790E849F146A416DE93079C7F5C3FB`。同じ再検証はWindows 1環境だけなので、G3全体の2環境/8正常検証/20否定ケースを満たしたとはしない。

既存の `opk-demo-acceptance-a/b` は合成デモである。これらのimmutable Releaseは履歴として保持するが、正式基準の「2つの実論文 repo」の代わりには数えない。過去に記録された `openpreprint-kit-robustness-eval` の repo URLは現在404で、別の場所・可視性・名前も未確認。404を削除の証拠に読み替えない。

## 第2論文候補の技術確認と限界

固定main `450db84d9e35772fda6af3a24592ced58df8b3ec` 上の候補を読み、次を実測した。

- v1 `analyze_robustness.py`: 20 spec cases、23 judgments、false accepts 0。spec/results内部整合チェックPASS。
- v2 `reverify_v2.py`: fresh CRL `VERIFIED`、stale CRL `REJECTED`、renewal verify PASS、negative-suite false accepts 0、内部整合チェックPASS。
- v1 PDF: 7 pages、1,142,144 bytes、SHA-256 `c5131663c629c2214f67723005df84a8d41e2370ae0a967cdbc5055260def7ab`。v2 PDF: 5 pages、885,920 bytes、SHA-256 `ac3ac2a5211e93809ed0dd6472cda66aa91a0ccb1e79fd3bb20fc541a1f16913`。
- 手順書の別PRで、各 `preprint.yaml` は実ファイル `paper.pdf` を指すよう訂正した。`research-assets.yaml` が指す supplements を実在させ、各資産の `public_confirmed` は全てfalseにする。strict metadata validationはPASSし、研究パッケージ生成は想定どおり `public_confirmed must be explicitly true` でBLOCKする。falseは所有者の権利・同意確認が未完了であることを表し、誰かの承認を代筆しない。

これはデータの内部整合とPDFの構文を示すだけで、科学的正確さ、著作者本人性、権利、公開同意、COI、人間レビュー、査読を証明しない。candidate filesはすでにkit repoのsource treeにあり、repoがpublicであるため、この事実を「非公開」とは主張しない。専用論文repoの公開Releaseは作成していない。所有者承認とG6記録が揃うまではrelease用 `public_confirmed: true` に変更しない。

## 所有者・著者の必須判断（公開前）

1. 第2候補の本文・PDF・研究データ・解析コード・引用を読んで、v1の研究内容と著者表示を承認または却下する。これはAIの検証結果から推定しない。
2. CC BY 4.0の本文とデータ、MITの解析コードの権利・ライセンス、第三者素材、公開同意、COIを人間が確認する。実人間のレビュー過程・訂正演習・撤回演習はG6に別記する。
3. v2が意味のある差分であること、v1/v2の版管理と公開予定を承認する。metadataの版番号だけでは十分でない。
4. 第2 repoが存在するならURLを示し、template origin・public visibility・Immutable・protected branch・required CI/human reviewをread-onlyで再確認する。見つからないなら、templateから新規作成する具体的なrepo名・公開範囲と権限影響を確認してから操作を別途承認する。
5. 各論文Releaseを作る直前、設定・タグ未使用・source commit・資産指紋・新TSA証拠を再固定する。v1/v2の公開操作は各々、所有者が対象と影響を見て明示承認する。

## 公開後の技術受入手順

1. Template由来と設定を読み戻し、Immutable Release有効・branch protection/required CI/human review・公開可視性を記録する。G1設定が未達のままなら公開作業を始めない。
2. source PDF/metadata/research assetsを固定し、`research_package.py --check` と strict metadata validationを実行する。権利確認後にのみ該当資産の `public_confirmed` をtrueにする。
3. 各新しいv1/v2にsource-bound manifest/TSAを付け、draftの全assetを匿名再取得して照合する。release作成後にimmutable、attestation、匿名取得、引用・研究資産、timestampを再検証する。
4. v2公開後にpaper v1/v2両方を再取得し、v1の11資産を公開前記録と照合する。過去のv1 assetに変更があれば停止し、変更/再発行で隠さない。
5. 正式4版を固定してG3の全条件（別に選定した信頼設定、2環境8正常検証以上、事前固定した最低20否定ケースで誤受理0）、G4匿名観測記録、G5 4版オフライン復元をそろえる。現時点の2版partial recheckや自己適用artifactは残りの版を代替しない。
6. Issue #5へ対象SHA/tag、Release ID/URL、各asset digest、attestation、匿名取得と復元結果、時刻・環境・operator・independenceを追記する。

## 現在の判定と禁止事項

- G2 `NOT CONFIRMED`: 現在検証できた実論文Releaseは第一repoのv1/v2の2件だけ。第2論文repoの実Release v1/v2がない。
- G1 `NOT CONFIRMED`: 第2template-derived public paper repoが解決できず、現在確認したbranch rulesのrequired approvalsは0。
- G6 source evidence missing: candidate metadataにowner approval pendingが明記されており、`reviews/record.json` は `events: []`。
- 現行の所有者判定基準では独立検証者の署名は不要だが、人間の承認と必要なG6記録をAIや別アカウントに代行させない。独立性は `UNPROVEN` と記録する。
- 第1repoと第2repoの各v1/v2をそろえるまでG2をPASSにしない。旧synthetic Releaseで置き換えない。G0〜G7すべての正式PASSと最終発行承認まではP4 NO-GO、kit v1.0.0を発行しない。
