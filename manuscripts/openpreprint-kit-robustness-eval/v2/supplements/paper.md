---
title: 'OpenPreprint Kitにおける改変検出・時刻証拠・障害復旧の実証評価 — 追加実験（v2）'
author: 'Unjuno'
date: '2026年11月15日 / v2候補 / 未査読'
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

本稿は、v1 で報告した20否定ケース・復元・信頼境界の評価に続き、v1 の結果から未解決だった2つの技術的問いを追加実験で解く。第一に、同一PKI・同一TSA証明書・同一問合せ/応答の下で CRL の鮮度だけが検証成否を分けるかを、fresh/stale の CRL で対照実験した。fresh CRL（nextUpdate=2026-12-13）では検証PASS、stale CRL（nextUpdate=2020-01-01）では OpenSSL が `Verify error: CRL has expired` で拒否することを実測した。第二に、保存済み公開物に対する前方RFC 3161更新（`renewal.py`）を、合成デモの preservation ZIP（SHA-256 `106d5363…ffa26c`）に適用し、チェーンの検証成功と TSA 署名時刻を記録した。v1 からの実質的差分は E-V2-1（CRL ライフサイクル対照）と E-V2-2（前方更新の実測）である。

**キーワード:** CRL鮮度、失効確認、RFC 3161更新、限界、実証

## 1. 背景と問い

v1 の結果、古いCRLは拒否されることを確認した（ケース15）が、「fresh CRL で正しく受理されるか」と「同じPKI・同じ問合せに対し鮮度だけが成否を分けるか」は未記録だった。また、前方更新（forward renewal）が実際の保存ZIPに対して有効にチェーンを延長できるかは、v1 では評価対象外だった。本稿はこれら2問を、実測に基づいて解く。v1 の記述および結論のうち、本稿で追加実験対象とした箇所以外は変更しない。

## 2. 実験計画（固定）

- **対象実装**: `c51aa55edfeb41e43b2c86982765c5d0777771ed`（main、CI: Validate/Quality/CodeQL success）
- **環境**: Windows（CPython 3.12.10, OpenSSL 3.5.6）、ローカル合成PKI（自作CA、RSA-2048）と FreeTSA（E-V2-2の実通信、バイト一致のみで内容の真正性は主張しない）
- **仮説 H1**: 同一PKI・同一TSA証明書・同一問合せ/応答の下、CRLの鮮度（nextUpdate）のみが検証成否を分ける。
- **仮説 H2**: 保存済みの検証済み preservation ZIP は、前方RFC 3161更新で「古い証拠を結ぶ新しい時刻証拠」のチェーンを新規取得できる。
- **期待**: H1: fresh→PASS / stale→REJECT。H2: issue & verify が PASS。
- **中断条件**: 実TSAへの通信が失敗した場合や、ローカルPKIの構築に失敗した場合は、その時点で記録を確定し対象を再検討する。
- **モック/ローカルPKI/実通信の区別**: E-V2-1はローカル合成PKI（実暗号処理）、E-V2-2は実TSA（FreeTSAへの問合せのみ。リポジトリへの書込なし）。

## 3. 結果

### 3.1 E-V2-1 CRL鮮度対照（同一PKI・同一TSA証明書・同一問合せ）

| 条件 | CRL last/next | 検証結果 |
|:--|:--|:--|
| fresh | 2026-11-13 → 2026-12-13 | **VERIFIED**（TSA署名時刻 2026-11-14T16:18:23Z） |
| stale | 2019-12-01 → 2020-01-01 | **REJECTED**（`OpenSSL ... ts_verify_cert: Verify error: CRL has expired`） |

fresh 側は leaf の有効性確認を含め正常に通過し、stale 側は CRL の鮮度のみを理由に拒否された。これにより、v1 ケース15の拒否は「証明書チェーンまたは問合せの不備」によるものではなく、CRL鮮度に帰因することが対照によって示された。なお、失効確認は OpenSSL の `ts_verify_cert` 内で行われ、アプリケーション層の検証コードの挙動ではない。

### 3.2 E-V2-2 前方RFC 3161更新（保存ZIP）

対象: `Unjuno/opk-demo-acceptance-a` の v1 の preservation ZIP（SHA-256 `106d536371c9286952eca1cf96fff542cc5de949c0673956818f52f13cffa26c`）、`renewal.py issue`（`--apply`、FreeTSA）。

| 項目 | 値 |
|:--|:--|
| issue | **PASS** |
| chain SHA-256 | `1eaae7e2ad3239a516b4731d14515be6bd5748caa45a038a59aebcdea2a6f993` |
| verify | **PASS**（tsa_policies=[1.2.3.4.1]、tsa_signed_times=2026-11-14T16:14:04Z） |
| historical_ltv | NOT_ESTABLISHED |

この操作は「新しい時刻証拠を既存証拠に結合して保存可能にする」ものであり、TSA/CAの失効後の歴史的LTV、著者の本人確認、初公開時刻、保存先の耐久性は証明しない。

## 4. 失敗・反証・限界

- E-V2-1はローカル合成PKIの結果であり、実TSA/CAの運用挙動の一般化ではない。
- `Verify error: CRL has expired` は OpenSSL の実装挙動であり、本キット固有の安全性保証ではない。
- E-V2-2の FreeTSA へのリクエストは最小限の存在時刻証明であり、データの内容を保証しない。
- 同一運用者・同一端末であり、独立検証・独立監査は未実施。
- 本稿は v1 の記述を部分的に更新するが、v1 における「20ケースすべて拒否」「復元一致」「誤受理0」の結論自体は変更していない。

## 5. 再現性

```bash
# E-V2-1（同一PKI・同一TSA証明書・同一問合せでの CRL 鮮度対照）
python manuscripts/openpreprint-kit-robustness-eval/v2/analysis/reverify_v2.py

# E-V2-2（保存ZIPに対する前方RFC 3161更新）
python scripts/renewal.py issue <v1-preservation.zip> \
  --expected-archive-sha256 106d536371c9286952eca1cf96fff542cc5de949c0673956818f52f13cffa26c \
  --source-policy <trusted-policy.json> \
  --repository Unjuno/opk-demo-acceptance-a --version v1 \
  --renewal-policy <trusted-policy.json> \
  --out renewal-chain.json --apply

# 否定試験結果の再集計（v1）
python manuscripts/openpreprint-kit-robustness-eval/v1/analysis/analyze_robustness.py
```

実験記録: `v2/data/{e-v2-1-crl-lifecycle.json, renewal-experiment.json, negative-suite-results.json}`。対象実装: `c51aa55edfeb41e43b2c86982765c5d0777771ed`。

環境: Windows（CPython 3.12.10、OpenSSL 3.5.6）。データ: `v2/data/{e-v2-1-crl-lifecycle.json, renewal-experiment.json}`。対象実装: `c51aa55e…`。

## 6. 結論

CRL鮮度のみを変更した対照実験（E-V2-1）により、「古いCRLは拒否される」という v1 の観測が、チェーン・問合せ・証明書の誤りではなく鮮度に基づくことが確認された。また、保存ZIPに対する前方RFC 3161更新（E-V2-2）が実際に機能し、issue/verifyの双方がPASSした。これらの結果は、保存と失効を同時に扱う実運用での要因特定に資するが、独立監査・独立観測・LTV・著者確認を代替するものではない。

## 7. UNKNOWN

| 項目 | 状態 |
|:--|:--|
| 他TSA（実運用の別CA）での失効/CA更新挙動 | UNKNOWN |
| CRL配布の継続性・責任者 | UNKNOWN |
| 実GitHub障害時の復旧 | UNKNOWN |

## 著者・AI支援・公開状態

AI支援で作成された未査読のv2候補。著者表示「Unjuno」（所有者申告、本人確認・独立証明ではない）、本文CC BY 4.0、コード・データは資産別ライセンスに従う。公開・版上げ・G2判定には、著者の最終承認と独立した検証担当の署名が必要である。

## 参考資料

[1] Unjuno. *OpenPreprint Kitにおける改変検出・時刻証拠・障害復旧の実証評価（v1）*. （本キット同梱、2026年11月）.

[2] OpenPreprint Kit. E-V2-1/E-V2-2 の実験記録（本キット `manuscripts/openpreprint-kit-robustness-eval/v2/data/`）.

[3] Adams, C., Cain, P., Pinkas, D., Zuccherato, R. *RFC 3161 — Time-Stamp Protocol (TSP)*. IETF RFC 3161 (2001). DOI: 10.17487/RFC3161.

[4] OpenSSL Project. *ts(1) — Time Stamping Authority tool*. https://docs.openssl.org/master/man1/openssl-ts/ （2026-11-14確認）.

[5] OpenPreprint Kit. `renewal.py`（前方RFC 3161更新）. https://github.com/Unjuno/openpreprint-kit/blob/main/scripts/renewal.py .
