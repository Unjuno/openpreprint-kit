# G2 実証（A案）用 — 出版 runbook（2 repo 各2版）

**状態: 準備資料のみ。実行には著者（所有者）の原稿執筆と承認が必須。AIは原稿・権利承認・著者承認を生成できない。**
基準: V1_ACCEPTANCE.md G2 は **2論文repo各2版、最低4件の不変 Release、うち最低1件は承認済み本短報**。
現状: paper v1（1 repo・1版）、synthetic demo 2 repo 各 v1/v2（基準上は A案不適合）。
→ 実論文として (i) paper v2 を発行するか、(ii) 第2原稿を新規 template 由来 repo に公開する。

## オプション I — 第2原稿を新規 repo に公開（**推奨**）

ツールの第一論文フロー（P1で実証済み）をそのまま再利用できる。v2 は新規コンテンツを含むため論文の科学的妥当性・権利は著者自身が確認すること。

前提（全て owner 必須）:
- 第2原稿の本文・データ・コードが用意され、著者が **CC BY 4.0**・著者表示名・版（v1）を確認
- 第2 repo 作成の権限と公開承認（UNJUNNO/openpreprint-kit-paper と同様の手順）

手順（概要）:
1. 原稿を確定し SHA-256 を固定（`python scripts/pdf_validation.py` 等で検査）
2. `Unjuno/openpreprint-kit-<paper2>` を template `Unjuno/openpreprint-kit` から作成（公開・Immutable）
3. 承認済み公開入力（PDF・データ・コード・引用等）をコミットし、prepare_release.py / citation_validation.py / license を通過させる
4. 新規 RFC 3161 トークンを取得（PDF/manifest 指紋の証拠）
5. draft Release → 匿名DL → byte 照合 → Immutable 有効化 → 公開 → attestation 検証 → SHA-256 一致・オフライン復元
6. 各 repo を **v2** に更新（同一手順で v1 資産を不変のまま v2 Release を発行）
7. 完了条件: 2 repo とも v1/v2 が存在し、全資産 attestation・匿名DL一致・v1 は v2 公開後も不変であることを機械照合し、Issue #5 に記録

## オプション II — paper v2 を発行（**非推奨・ツール未対応**）

現状の toolkit は **v1 専用**に設計されており（承認済み v1 PDF の SHA-256 固定、`--publish` は既存 repo `Unjuno/openpreprint-kit-paper` への再公開を意図的に拒否）、v2 を安全に発行する一括コマンドは存在しない。選択肢:

- (a) 著者が **内容の v2 を執筆**し、ツールを新版対応させる修正（launcher/承認入力の差し替え、回帰テスト、owner 承認）を別 PR で行う
- (b) `prepare_release.py` 等の既存プリミティブを手順に沿って**手動実行**して v2 を publish する（その場合も全ての不可逆操作に owner 承認が必要。P1 と同じ検証を v2 にも実施すること）

どちらも「無意味な版上げ」ではなく、**v2 にふさわしい新規内容の執筆が前提**（誤記訂正・追加データ・追試など）。

## 完成判定

- 2 repo が各2版（計 ≥4 Release）を持ち、うち1件は承認済み本短報 = paper v1
- 全版の attestation・匿名DL byte一致・v1 不変性を実測
- Issue #5 に証拠を記録し、G2 の **発行者と別の検証担当**が PASS を署名
- それまでは G2 = PARTIAL（synthetic 実証では満たさない）

## 制約

- 公開・新規 repo 作成・権限変更・基準変更には owner の明示承認が必要
- 既存の不変 Release（paper v1）は削除・再作成・上書きしない
- 暗号検証を迂回して owner 承認を省略しない
- 本 runbook は準備資料であり、これ単体では G2 を PASS にしない
