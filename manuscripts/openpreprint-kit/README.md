# 最初の短報：OpenPreprint Kitの自己適用

[短報草稿](paper.md)はOpenPreprint Kit自体の設計と検証を記述する、3ページ相当の日本語技術報告です。評価対象は **940d0d06d957cd0708f644a595911bdbc3fffa64** に固定します。自身の論文、試験ログ、データ、再計算コードをキットへ渡す最初の実利用ケースです。

## 状態と公開境界

- **編集草稿・未査読。正式な論文Releaseではありません。** 原稿をmain/PRへ置くこと、CI artifacts、PDFの生成を不変Releaseの公開と混同しません。
- 本文の著者表示はプロジェクトアカウントUnjunoという名義案です。所属・学位・ORCIDは推測していません。
- `preprint.yaml` は意図的に **v0 / UNSPECIFIED**。著者と利用条件の確認がないまま公開されないよう、厳格な公開検査では停止します。
- `proposed-preprint.yaml` は **ローカル検証専用のメタデータ案**。CC-BY-4.0は提案であって、この草稿による利用許諾ではありません。候補バンドルは公開承認を代行しません。
- ルートのキット用テンプレートを本論文で上書きしません。正式公開時は専用の論文リポジトリを用意し、このディレクトリの入力を対応するルートの場所へ展開します。現時点で専用リポジトリは未作成です。
- Google Driveは使いません。オンラインの原稿・データ・公開証拠はGitHubに置きます。秘密鍵・個人の健康記録は含めません。

## データを再集計する

Python 3.10以降の標準ライブラリだけで実行できます。

```bash
python manuscripts/openpreprint-kit/analysis/summarize_ci.py
```

`data/baseline-ci.txt.gz` の圧縮前後のSHA-256、試験名の一意性、末尾の総数と成功状態を検査し、274件・26モジュールを再集計します。`data/provenance.json`に出所と対象コミットを、`data/test-counts.csv`に全内訳を記録しています。原ログは品質CI 43222595349の保存物です。実行時間を性能ベンチマークには用いません。

## PDFを生成する

必要な組版環境: Pandoc、XeLaTeX、Noto Serif CJK JP、Liberation Serif、DejaVu Sans Mono。フォントファイル自体は配布しません。組版ツールとフォント差によりPDFのバイト列は変わり得るため、正式版は生成したPDFそのものをハッシュで固定します。

```bash
cd manuscripts/openpreprint-kit
SOURCE_DATE_EPOCH=1794441600 pandoc paper.md --from markdown \
  --pdf-engine=xelatex --output paper-draft.pdf
```

SOURCE_DATE_EPOCHは再現可能な組版用定数であり、存在時刻の証拠ではありません。`paper.md`ではLaTeXのページ表示用OpenActionを付与しないよう明示しています。初回にこの設定が検査で拒否されたため、PDF検査を弱めず組版側を修正しました。

## キットへの自己適用

専用の一時ディレクトリへキットの`scripts/`をコピーし、次のように配置します。

```text
work/
  scripts/                 # 固定したキットのソース
  paper/paper.pdf           # 実際に組版した短報
  data/                     # 本ディレクトリのdata一式
  analysis/summarize_ci.py
  supplements/paper.md
  supplements/LICENSE-NOTICE.txt
  preprint.yaml
  research-assets.yaml
```

通常は草稿の`preprint.yaml`を使うため公開検査が止まります。**スキーマとバンドル処理だけを試験する場合**、一時ディレクトリに限って`proposed-preprint.yaml`を`preprint.yaml`として配置します。著者・ライセンスの承認、TSA発行、GitHub公開は行われません。

```bash
python scripts/prepare_release.py --output candidate-bundle
python scripts/citation_validation.py candidate-bundle
python scripts/verify_release.py candidate-bundle
```

これらのコマンドは元データと各候補ファイルの内容整合性を検査するだけです。時刻証拠がないものに`existence`や`public-observation`のPASSを与えてはいけません。PDF変更・研究データ変更・manifest変更・ファイル欠落が拒否されることも別コピーで試します。

`notes/self-application.json`には今回の試験結果とPDF/manifestの指紋を記録しました。原稿自身の指紋を原稿内に書く循環を避けるため、この生成後の記録は論文の入力研究アーカイブには含めません。原稿を変えたら再試験して別記録を作成してください。

## 第1論文を最初の受入テストとしてCI実行する

この短報は単なる機能紹介ではなく、**キットで実際の原稿・実際の研究資産を処理する自己適用試験**でもある。GitHub Actions
[`first-paper-selftest.yml`](../../.github/workflows/first-paper-selftest.yml)は、原稿や検証スクリプトの変更時および手動実行時に、Pandoc/XeLaTeXで本稿を組版し、次を検査する。

1. 原本のCIログを保存済みSHA-256で照合し、評価対象274件・26モジュールを再集計する。
2. 著者・利用条件が未承認の草稿を厳格公開検査が拒否することを確認する。
3. **一時ディレクトリだけ**で提案メタデータを用いて候補バンドルを作成し、PDF・研究資産7点・CFF/BibTeXを検証する。これを承認とみなさない。
4. PDF・データ・manifestの変更と引用の欠落について、4件すべてで拒否を確認する。
5. `LOCAL_SELF_APPLICATION_ONLY`と明示したJSON結果を保存する。実際のTSA発行、Immutable Release公開、独立観測がない限り、`existence`や`public-observation`の合格とは表示しない。

ローカルで同じ試験を行うコマンド（論文用のPDFはPandoc等で組版する）。

```bash
python scripts/first_paper_selftest.py \
  --manuscript manuscripts/openpreprint-kit \
  --paper-pdf /path/to/first-paper-draft.pdf \
  --report /tmp/first-paper-selftest.json
```

このコマンド自体は任意の適正な構造のPDFを受け取るので、**本文がMarkdownと意味的に一致することまで証明できない**。GitHub Actionsでは同じジョブ内で対象`paper.md`を組版することで入力を固定する。CIのPDFとJSONは14日間の短期成果物であり、**正式な論文Releaseではない**。第三者査読や論文ライセンス承認も行わない。

## 正式公開に移る条件

著者・ライセンス確定、専用リポジトリとImmutable Releases設定、信頼根を別途確認したRFC 3161取得、全資産の再取得検証が必要です。公開通知はこの正式な論文Releaseを対象とし、草稿掲載を公開完了とは扱いません。独立観測・独立監査・学術査読は引き続き別の工程です。
