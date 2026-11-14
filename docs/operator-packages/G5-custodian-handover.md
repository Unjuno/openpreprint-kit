# 別管理保管者パッケージ（G5）

**目的:** 別管理の保管者が P1/P2 で得られた公開証拠を受領・保管し、GitHub が利用不能でも対象4版の保全バイトを新環境へ復元できることを実証する。
**注意:** 「台帳が存在する」ことや「所有者が SHA-256 を計算した」ことは G5 の PASS ではない。保管者による実際の受領・再計算・保管記録が必要。

## 受領対象（台帳: CUSTODY_LEDGER.json, 2026-11-14, 304 files）

最小保管セット（パスは `OpenPreprintKitEvidence/` 配下）:

| 種別 | パス | SHA-256 |
|---|---|---|
| 第1論文 v1 保存ZIP | `first-paper-49figapb/publication/first-paper.opk.zip` | `66cccf52d0bdacc7f5bcf8ea4c23931824f94aaf715932d9aff282328752a5c4` |
| 初回FAIL記録（不変） | `first-paper-49figapb/publication/publication-report.json` | （上書き禁止） |
| 継続記録 | `first-paper-49figapb/publication/continuation-report.json` | 添付 manifest 参照 |
| 合成パイロット証拠 | `synthetic-pilot-2026-11-14/evidence/`（registry-{1,2}/{v1,v2}/evidence.opk.zip ほか） | 下記 ZIP SHA 参照 |
| demo-a v1 ZIP | `repository-1/v1/evidence.opk.zip` | `106d536371c9286952eca1cf96fff542cc5de949c0673956818f52f13cffa26c` |
| demo-a v2 ZIP | `repository-1/v2/evidence.opk.zip` | `b0ef4bbef5374b51cb1ca47b23a5fdefdb05c21cd56431f3c536937ea26e5add` |
| demo-b v1 ZIP | `repository-2/v1/evidence.opk.zip` | `a5dd4ca6d0525760f31907cef7083c9dec4395ea68d30af41dddf4cb40477541` |
| demo-b v2 ZIP | `repository-2/v2/evidence.opk.zip` | `44d7ff369f557b691c785bb911f76d85eb64636829e13359b5affa02e1e9f4f9` |
| 否定試験 | `negative-suite-2026-11-14/`（spec・results・PKI） | 添付 manifest 参照 |
| TSA信頼スナップショット | `*/trust/{ca.pem,crl.pem}` | FreeTSA pinned `2151b611…` |
| Issue #5 記録 | `issue5-*.md` | 添付 manifest 参照 |

全304ファイルの SHA-256 は `CUSTODY_LEDGER.json` に記録済み（`CUSTODY_LEDGER.json` 自身の内容も照合可能）。秘密鍵・トークン・患者原本・個人情報は含まない（含まれていたら受領拒否）。

## 保管者の手順

1. **受領**: 上記セットを Owner 端末から取得する（USB/帯域外転送を推奨。GitHub 非経由）。
2. **再計算**: `CUSTODY_LEDGER.json` の全エントリを local SHA-256 と照合。1件でも不一致なら受領を拒否し Owner へ報告。
3. **保管**: 保管場所・管理責任者・点検周期（例: 月次）・事故対応責任者・連絡先を `CUSTODY_HANDOVER.md` の §3 に記入し、owner へ返送。
4. **ミラー**: 別管理 GitHub アカウント/組織の `OWNER/EVIDENCE-MIRROR` を作成し（別アカウント・別管理権限）、4版の preservation ZIP と `custody.json` を Immutable Release として保存（`docs/GITHUB_PRESERVATION.md` §3 `github_mirror.py publish` 手順）。注意: 同一アカウントの別 repo は「別管理」ではない。
5. **オフライン復元実証**: GitHub に接続しない新規環境（別PC/VM、ネットワーク遮断）で `preserve.py restore` + SHA-256/TSA 検証により 4版を復元し、完全照合する。ログを保全する。
6. **記録返送**: 受領確認・再計算結果・ミラータグ・復元ログ・SHA-256 を Issue #5 に添付。

## PASS 条件

- 保管者が自身の管理下で受領し、再計算一致・保管・点検周期・事故責任者を記録したこと。
- 別管理ミラーの全4版保存と、GitHub 非接続の4版復元が実測で成功したこと。
- ミラーと別経路に期待SHA-256が保管され、復元がそれに一致すること。
- 署名付き保管・復元記録が Issue #5 にあること。
- これが無い限り G5 は PASS にしない。

## Owner 未依頼の場合の停止条件

保管者が選任できない場合、技術的な引渡し準備が完成していても G5 は BLOCKED のままとする。Owner が保管者を選んだ時点で本パッケージに沿って実施する。
