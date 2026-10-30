# OpenPreprint Kit

GitHub をプレプリントの公開場所として使うための、再利用可能なリポジトリテンプレートです。

> **開発初期版:** 現在含まれるのは構成ファイルとメタデータ検証機能です。暗号学的タイムスタンプ、一般公開時刻の独立証明、DOI 発行、長期保存、引用ファイル自動生成は**未実装**です。

## 目的

- **1 論文 = 1 Public Repository** として公開・版管理する。
- GitHub Releases で版ごとの PDF とメタデータを管理する。
- 公開前に論文のメタデータと PDF を検査する。
- 将来的に外部時刻認証・第三者検証・引用情報の自動生成を追加する。

## 最初の使い方

1. GitHub 上でこのリポジトリを Template repository に設定する（Settings → General → Template repository）。
2. 論文ごとに **Use this template** から新しい Public Repository を作成する。
3. `preprint.yaml` にタイトル、著者、概要、ライセンスなどを記入する。
4. `paper/paper.pdf` を追加する。
5. 以下のコマンドで公開前チェックを実行する。

```bash
python3 -m pip install -r requirements.txt
python3 scripts/validate.py --strict
```

`--strict` を付けない場合、PDF 未登録やプレースホルダーは警告として扱い、編集中のテンプレートも検査できます。GitHub Actions はこの下書き用検査を実行します。

**注意:** 現時点では、検証に成功しても時刻の存在証明や公開証明は作成されません。公開日時の保証として扱わないでください。

## 設計方針

- GitHub 以外の専用サーバー・データベースを必須にしない。
- 証明書の検証は GitHub に依存せず実施できるようにする（将来実装）。
- Git の Author Date / Committer Date は任意に指定できるため、時刻の証拠として使用しない。
- 論文そのもののライセンスと、このツールのソフトウェアライセンスを分離する。

開発段階・未実装項目は [`docs/ROADMAP.md`](docs/ROADMAP.md) を参照してください。

## ライセンス

このリポジトリ内のソフトウェアとテンプレート自体は MIT License です。**利用者が追加する論文本文・図表・研究データの利用条件は、各研究者が別に指定**してください。`preprint.yaml` の `license` は論文に適用するライセンスの識別子です。
