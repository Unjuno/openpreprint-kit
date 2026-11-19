# 第1論文：OpenPreprint Kitを自身に適用する受入テスト

**論文v1の著者表示はUnjuno、本文・原稿のライセンスはCC BY 4.0です。2026年11月13日に利用者が確認しました。** この確認はチャット上の申告であり、署名付き本人確認・権利調査・査読を意味しません。

**公開状態：2026年11月14日、未査読プレプリントv1を[GitHub Immutable Release](https://github.com/Unjuno/openpreprint-kit-paper/releases/tag/v1)として正式公開済み（Release ID 444659219）。** [本文](paper.md)、[正式候補メタデータ](preprint.yaml)、[資産別ライセンス通知](LICENSE-NOTICE.txt)が現在の入力です。`proposed-preprint.yaml`は承認前の履歴であり、正式候補には使用しません。

評価対象の実装コミットは `940d0d06d957cd0708f644a595911bdbc3fffa64` に固定しています。保存済みCIログ274件・26モジュール、集計データ、再実行コードを、現在のキットのテスト件数とは区別して報告します。

## 原稿・データの再現

Python 3.10以上で、まず証拠ログとCSVを検証できます。

```bash
python manuscripts/openpreprint-kit/analysis/summarize_ci.py
```

PDF組版にはPandoc、XeLaTeX、Noto Serif CJK JP、Liberation Serif、DejaVu Sans Monoなどが必要です。フォント自体は再配布しません。`SOURCE_DATE_EPOCH`は組版用の固定値であり、TSA時刻ではありません。

```bash
export SOURCE_DATE_EPOCH=1794528000
pandoc manuscripts/openpreprint-kit/paper.md --from markdown \
  --pdf-engine=xelatex --output first-paper-v1.pdf
python scripts/first_paper_selftest.py \
  --manuscript manuscripts/openpreprint-kit \
  --paper-pdf first-paper-v1.pdf \
  --report first-paper-v1-selftest.json
```

自己適用はPDF構造、v1の著者名・ライセンス、保持CIログの指紋と件数、7つの公開研究入力、CFF/BibTeX、PDF・データ・manifestの改変と引用欠落を検査します。承認前へ戻した`v0`/`UNSPECIFIED`の厳格公開拒否も負の対照として再試験します。`--export-candidate NEW_DIRECTORY`を付けると検証済み候補を**新規ディレクトリのみ**に書き出します。

ユーザーが指定した著者名とライセンスは承認済みですが、コードによる検査は著作権の真正性や査読を証明しません。元リポジトリのテンプレート`preprint.yaml`は引き続き`v0`/`UNSPECIFIED`であり、本論文のv1をルートへ上書きしてはいけません。

## 承認後の外部RFC 3161時刻証明

GitHub Actions [第1論文実TSAワークフロー](../../.github/workflows/first-paper-live-timestamp.yml) は、上記v1本文を再組版し、外部FreeTSAから**内容を固定した新しいRFC 3161証明**を取得し、別ランナーでCA/CRLを取得し直してZIP全資産を再検証します。2026年11月12日の未承認draftに付与された旧時刻証拠は、変更後のv1へ流用できません。

合格できる範囲は `APPROVED_MANUSCRIPT_EXISTENCE_ONLY` です。論文の存在時刻の証拠と、GitHubへの**正式な公開開始時刻**は異なります。証拠の保管先となるGitHub Actions artifactは14日間の短期成果物であり、永久保存ではありません。

## GitHub上での正式発行結果と残る保証

論文専用の公開GitHubリポジトリをTemplateから作り、Immutable Releasesを有効化して、承認済みPDF・研究データ・引用情報・**公開先のソースに結び付く新しいRFC 3161証拠**を全11資産として公開しました。GitHub APIで`draft=false`・`immutable=true`と紙面のSHA-256一致を確認できます。[所有者の詳細な実行証拠](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-6863092530)にはRelease attestation、全資産の匿名再取得、復元のPASS記録があります。ただし初回のWindows起動時は`cffconvert` PATH欠陥で停止し、所有者承認の下で手動継続しました。元FAIL記録と継続記録は別々に保持され、最初から無停止で実行できたとは主張しません。

旧プログラムを再実行して新しいv1を作り直すことはしません。別管理GitHubミラー、第三者による署名付き観測、人間のレビューとセキュリティ監査は別工程であり、現時点ではキットv1.0.0の受入条件を満たしていません。

**オンライン配布・ミラーはGitHubを使用します。** Google Driveの利用、実患者原本、非公開HMAC鍵や署名秘密鍵のアップロードはありません。AI支援の原稿であること、未査読であること、独立の著作者本人確認をしていないことを、本文でも明示します。
