# RFC 3161 — 時刻精度と更新チェーンの時刻順序

更新チェーン (`renewal.py verify`) の署名時刻とその解釈について、運用上の前提を明示する。

## 署名時刻が意味するもの

各ステップの `timestamp.tsr` に含まれる署名時刻は、
「当該TSAが、その証拠ダイジェストをその時刻に見ていた」ことだけを証明する。
**提出順序そのものは証明しない**。署名時刻は TSA 固有の時計（精度は証明書の `accuracy` または `NOT_SET`）であり、
2つの異なるTSAの時計の相互関係は不明である。

## 受入条件（`_check_signed_time_order`）

| 条件 | 受入 | 理由 |
|---|---|---|
| 全ステップが同一 policy OID (同一TSA信頼) | 非減少（同一時刻許容） | 同TSAだが非減少を要求。逆転は拒否 |
| ステップ間に policy OID 変更がある | 厳密増加を要求 | 異なるTSAは信頼できる時計共有を仮定しない |
| 時刻が不正 / TZ aware でない / 空 | 拒否 | UNKNOWN を PASS と読み替えない |

戻り値は `time_order`（`NON_DECREASING_SAME_TSA_POLICY` / `STRICTLY_INCREASING_CROSS_TSA_POLICY` / `UNKNOWN`）として結果に含まれ、消費者はこれを独立性の根拠と混同してはならない。

## 歴史的LTVとの違い

前方更新チェーンは「**今**期限切れ失効していないCRL/証明書を使った検証」を都度確認できるようにする仕組みであり、
「最初の証拠時刻から今日まで無条件に検証可能だった」ことを保証するものではない。失効情報（CRL/OCSP）の更新・再取得を継続する責任は運用者にある。

## 実運用チェックリスト

- renewal時刻の単調性検証で UNKNOWN を PASS 扱いしない
- ステップごとに別 policy を適用する場合は増加のみ受け入れる
- チェーンの terminal digest は out-of-band に保持し、チェーン自体から導出しない
- チェーンは GitHub Release などの不変媒体に配置し、毎回匿名再取得で照合する


## 元証拠 → 最初の更新ステップの関係（2026-11-19 追加）

`verify_chain()` は元の preservation ZIP に含まれる existence stamp の
`tsa_time_utc` / `accuracy_microseconds` / `policy_oid` を `origin_existence_stamp` として
検証結果に含め、最初の更新ステップとの関係を `_check_origin_to_first_renewal()` で評価する。

| 状況 | 判定 | 根拠 |
|---|---|---|
| 更新時刻が元証拠時刻より combined accuracy を超えて前 | 拒否 | 前方延長ではないため証拠の誤受理 |
| 同一 policy OID で同一時刻／accuracy 内のわずかな逆転 | `NON_DECREASING_SAME_TSA_POLICY_FROM_ORIGIN` | 同一 TSA の非減少ルールを踏襲 |
| 同一 policy OID で明確に後 | `FORWARD_SAME_TSA_POLICY_FROM_ORIGIN` | 同一 TSA の時刻で前方 |
| 異なる policy OID（別 TSA）で同等／重複 | `CROSS_TSA_ORDER_NOT_PROVEN_CLOCK_SKEW` | 別 TSA の時計差は証明できないため不確実性を明示 |

`time_order_note` には「RFC 3161 の署名時刻はダイジェスト存在の境界を示すだけで、
提出順序や初公開時刻を証明しない」旨を必ず記録する。
`historical_ltv` / `first_publication` は従来どおり `NOT_ESTABLISHED` / `NOT_PROVEN` を維持する。

`issue_chain()` は出力の確定前に `verify_chain()` を呼ぶため、
元証拠より前の更新ステップは発行段階でも拒否される。
