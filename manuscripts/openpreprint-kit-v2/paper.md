---
title: 'OpenPreprint Kit: GitHub上の論文・研究データを検証可能にする公開キット — 実運用評価（v2）'
author: 'Unjuno'
date: '2026年11月14日 / v2候補 / 未査読'
lang: ja-JP
fontsize: 10pt
papersize: a4
geometry: margin=22mm
CJKmainfont: Noto Serif CJK JP
mainfont: Liberation Serif
monofont: DejaVu Sans Mono
colorlinks: false
header-includes:
  - \PassOptionsToPackage{pdfstartview={}}{hyperref}
---

## 要旨

本稿は、文献[1]の初期設計短報（v1、固定コミット `940d0d06d957cd0708f644a595911bdbc3fffa64` のCI 274試験）を実運用に持ち込んだときに何が実証され、何が壊れ、何が未達のまま残ったかを報告する。2026年11月13日から14日にかけて、第1論文v1が公開され、その後ツールキットに対して2系統の公開実証（合成デモ2リポジトリ×2版、計4つの不変Releaseと、承認済み第1論文の正式公開）が完了した。公開はImmutable Release、GitHub Release/asset attestation、RFC 3161時刻証拠（FreeTSA）、匿名再取得、SHA-256照合、保存ZIPのオフライン復元によって検証できることが実測された。一方で、Windowsでの公開処理停止、Immutable設定の読戻し競合、単一運用者による検証の独立性の欠如、という3つの限界が実証によって明らかになった。本稿の新規性は274件という初期CI数値ではなく、実公開の障害分析と、独立した人間による最終受入が未完了であるという限界の明示にある。

**キーワード:** プレプリント、実運用、不変Release、RFC 3161、障害分析、限界

## 1. 背景と目的

v1は「GitHub上の論文・研究データの検証可能な公開」という設計を、固定コミットのCIログ274件に基づく内部評価として提示した。本v2では、同一キットを実際の公開に適用したときの挙動を記録し、(a) 設計が意図した保証のうち実際に成立したもの、(b) 実装と運用で破綻したもの、(c) 依然として成立していないもの、を区別する。評価対象はツールキット自身の公開物であり、外部の研究課題ではない。利用した一次資料は、GitHub公開API、保存された原ログ、保存ZIPの復元結果、および Issue #5 の記録である。

## 2. 方法と実行環境

**対象公開物は5つの不変Releaseである。** 承認済み第1論文（`Unjuno/openpreprint-kit-paper` v1、Release ID 444659219）と、受入試験のための合成デモ2リポジトリ（`Unjuno/opk-demo-acceptance-a/b`、v1/v2各2版）。デモは実研究ではなく、合成素材・合成コードのみで構成される。評価環境はWindows（CPython 3.12.10、OpenSSL 3.5.6）と GitHub Actions Ubuntu 24.04（run #43583374274）の2系統である。検証に使ったのはGitHub API、匿名HTTPSダウンロード、保存ZIPのオフライン復元（`preserve.py restore`）、FreeTSAによるRFC 3161証拠の再検証である。旧v1の274件は、固定コミットの歴史的レコードとしてのみ参照し、本稿の結論の根拠には用いない。

| 区分 | 内容 |
|:--|:--|
| H（仮説） | 実公開後も資産・タグ・ダイジェストが固定される；時刻証拠と保存ZIPは再検証可能である |
| T（最小試験） | 5 Releaseのattestation検証・匿名DL・復元、2環境での正常検証、20否定ケース、5版のTSA再検証 |
| D（判定） | すべて期待どおり拒否・一致した；一部のPASS主張は独立人間なしでは成立しない |
| C（対立条件） | 同一運用者による複製検証、TSAの信頼根置換、Releaseすり替え、CRL期限切れ |
| U（不確かさ） | TSA時刻精度（証明書にaccuracy未記載）、CRL鮮度、独立性（同一端末・同一GitHubアカウント） |

## 3. 結果

### 3.1 不変Releaseと公開制御

5つのReleaseはいずれも `draft=false`、`immutable=true` で公開され、
匿名HTTPSで再取得した全資産のSHA-256がGitHub公開APIの資産ダイジェストと一致した（paper v1: paper.pdf = `0860b735…1a1b07c`）。各Releaseに対し `gh release verify` と全11資産の `gh release verify-asset` が成功した。引用情報（CITATION.cff・citation.bib）、研究データ、解析コードを結ぶマニフェストは、再ダウンロードに対して完全一致した。

### 3.2 時刻証拠とオフライン復元

5版すべてのRFC 3161証拠は、保存した信頼ポリシー（FreeTSA CA指紋 `2151b611…`、policy OID `1.2.3.4.1`）で再検証PASSと記録された。紙面v1の保存ZIP（SHA-256 `66cccf52…`）はGitHub非接続の新規環境相当で復元でき、復元バイトは匿名DLと一致した。合成デモ各版でも同様の復元・照合・TSA検証を完了した。

### 3.3 異常系の拒否

20の否定ケース（23判定）を実行し、誤受理は0件だった（§4.3）。実装上確認できた拒否例には、PDF改変、研究データ・解析コード・manifestの改ざん、資産欠落、余計なファイル、別リポジトリ・別版の取り違え、CA指紋不一致、Policy OID不一致、nonce不一致、署名バイト反転、失効TSA、期限切れTSA、古いCRL、危険なZIP（パストラバーサル／重複member／symlink）、観測鍵の誤り、署名後の観測改変が含まれる。

### 3.4 発見された障害と修正

**INC-1（Windows公開停止）。** P1公開時、公開は `SOURCE_COMMITTED` で停止した。原因は `cffconvert==2.0.0` を分離venvに入れながら、引用検証が素の名前 `cffconvert` で起動しており、WindowsではvenvのScripts/がPATHに無かったことである。所有者承認の下で同じコード経路をPATH修正だけを加えて継続し、既存repoの削除・再作成・FAIL記録の上書きを一切行わずに公開を完了した。恒久修正（PR #34）は `cffconvert` を実行中のPythonの場所から解決するようにし、子プロセスに `PYTHONUTF8=1` と venv Scripts を渡すようにした。

**INC-2（immutable読戻し競合）。** 合成パイロット実行で、`PUT immutable-releases` 成功後の即時 `GET` が `enabled:true` を返さず、公開処理がリポジトリ作成直後に停止した。競合は数秒〜数分で解消したが、読戻しには有限リトライが必要だった。bounded retry（6回/2秒間隔、PR #35）を導入して解決した。

これら2件は、実公開において自動処理が「設定の反映前に読み戻す」種類の競合と、ローカル環境のPATH仮定という、**設計レビューには現れない運用上の故障モード**を露呈した。

### 3.5 未完了の受入

独立した人間による受入（G4/G5/G6/G7：観測者・保管者・編集者・外部監査）が未実施であり、現在の証拠は単一オペレータによる検証であるという限界をはっきり述べる。TSAはFreeTSAを用いたが、これは特定信頼機関への依存を意味する。issue #5は証拠の台帳であり、Issue #5の存在やCI成功を「独立監査済み」や「完成」と読み替えてはならない。

## 4. 考察

### 4.1 仮説の検証状況

Hの「資産・タグ・ダイジェストの不変性」と「時刻証拠・保存ZIPの再検証可能性」は、各版で成立した。一方、C（同一コードによる共通誤り、信頼根の誤設定、全体すり替え）に対しては、陰性対照としてのみ機能しうる（単一コードベース・単一検証者である限り、独立した再実装による交差検証はない）。U（TSA精度・CRL鮮度・独立性）は計測不可能であり、数値化しない。

### 4.2 別環境での正常検証

Windowsローカルに加え、Ubuntu 24.04 のGitHub Actions run #43583374274（public-tsa / fresh-verification）でも合成版の実TSAスタンプと新runnerでの復元が完了した。2環境8回以上の正常検証の条件を満たすが、環境は2つとも同一GitHubアカウント配下であり、独立性は主張しない。

### 4.3 失敗・反証・限界

- 20否定ケースの判定はすべて「拒否」であり、**誤受理0**をもって安全性全般を主張するものではない。未試験の入力・実装上の共通原因・別TSAへの信頼移行を本結果から外挿してはならない。
- 古いCRLの拒否は「OpenSSLが CRL 失効を report した」ことによるものであり、暗号方式そのものの安全性ではない。
- 本稿は独立監査・査読・著者本人確認を経ていない。AI支援で作成されたことを明示する。

## 5. 再現性とデータ

- 対象実装 main: `c51aa55edfeb41e43b2c86982765c5d0777771ed`（CI: Validate 3.10/3.12=372/372、Quality/audit、CodeQL success）。
- データ: `data/release-matrix.json`（5 ReleaseのID/commit/attestation照合）、`data/tsa-reverification.json`（5版のTSA再検証）、`data/incident-analysis.json`（INC-1/2）。
- 実験プログラム: `manuscripts/openpreprint-kit-robustness-eval/`（改変検出・PKI・復元の記録）。
- 第1論文v1は変更禁止で公開済みである。本稿はその再公開ではない。

## 6. 結論

OpenPreprint Kitの初期設計は、実公開に耐え、資産不変性・時刻証拠・復元可能性という中核的主張のいくつかを、実測可能な形で提供することを示した。同時に、環境依存（Windows）・設定競合（Immutable読戻し）・検証の独立性の欠如という、設計段階には見えなかった障害と限界が露呈した。完成ではなく、第1論文を足場とした検証チェーンの継続と、独立した人間による受入を次の段階とする。

## 著者・AI支援・公開状態

本稿はAI支援で作成された未査読のv2候補である。著者表示は「Unjuno」（所有者による申告。本人確認・独立証明ではない）、本文と原稿のライセンスはCC BY 4.0、コード・データは資産別ライセンスに従う。独立査読・独立監査は未実施である。人間の最終確認と承認なしに公開・版上げ・スコープ拡大を行ってはならない。

## 参考資料

[1] Unjuno. *OpenPreprint Kit: GitHub上の論文・研究データを検証可能にする公開キット — 初期設計短報（v1）*. OpenPreprint Kit Release v1 (2026-11-13). https://github.com/Unjuno/openpreprint-kit-paper/releases/tag/v1 .

[2] GitHub. *Immutable releases*. https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases （2026-11-14確認）.

[3] GitHub. *Release integrity verification*. https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/verify-release-integrity （2026-11-14確認）.

[4] Adams, C., Cain, P., Pinkas, D., Zuccherato, R. *RFC 3161 — Internet X.509 Public Key Infrastructure Time-Stamp Protocol (TSP)*. IETF RFC 3161 (2001). DOI: 10.17487/RFC3161.

[5] OpenPreprint Kit. 本稿の一次証拠（5 Releaseのattestation/TSA/匿名DL結果）一式. Issue #5（2026-11-14）. https://github.com/Unjuno/openpreprint-kit/issues/5 .

[6] OpenPreprint Kit. 受入試験記録（否定20ケース・PKI・復元）. PR #32–#40（2026-11-14）.
