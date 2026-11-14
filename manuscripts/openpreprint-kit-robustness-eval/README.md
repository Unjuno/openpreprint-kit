# 改変検出・時刻証拠・障害復旧の実証評価 — 概要（論文B）

**論文B（本稿）** は OpenPreprint Kit 自身を研究対象とし、
「公開物に対する意図的な改変・信頼設定の誤り・証拠失効・途中失敗を、どの範囲で検出・拒否・復旧できるか」を
実際に実行した試験で評価する。**論文A（実運用評価 v2）の設計説明を繰り返さない。**

## つまみ

```bash
# 否定ケースの再集計（標準ライブラリのみ）
python manuscripts/openpreprint-kit-robustness-eval/v1/analysis/analyze_robustness.py

# 同梱データの確認
ls manuscripts/openpreprint-kit-robustness-eval/v1/data/
```

## v1 の試験計画と結果の要点

- 対象実装: `c51aa55edfeb41e43b2c86982765c5d0777771ed`（main、CI: Validate/Quality/CodeQL success）
- 事前固定した20ケース・23判定、誤受理0
- 実TSA（FreeTSA）＋ローカル合成PKIの失効/期限切れ/古いCRL
- 復元: 公開5版すべてで匿名DLとバイト一致
- 障害: INC-1（Windows PATH停止）、INC-2（immutable読戻し競合）— 公開拡大・削除・上書きをせずに記録を保持

## v2 の追加実験

- E-V2-1: CRL鮮度対照（fresh=VERIFIED / stale=`Verify error: CRL has expired`）
- E-V2-2: 前方RFC 3161更新（`renewal.py issue/verify` PASS、chain `1eaae7e2…`）

## 制約

- 実運用（公開）は所有者の明示承認が必要。現状は原稿・実験の公開前状態であり、未査読・未監査。
- 独立した観測者・保管者・編集者・外部監査者は未選任。AIは代替しない。
- 本 README と本文は相互参照されるが、本文の一次証拠は `data/` および Issue #5 にある。
