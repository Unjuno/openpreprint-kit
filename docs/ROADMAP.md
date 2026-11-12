# OpenPreprint Kit — 完成条件付きロードマップ

更新: 2026-11-06。ソフトウェアv0.3継続開発。**運用完成ではない**。
機能の追加と、実際のサービス・実論文による運用実証を別々に管理する。

| 段階 | 実装・確認状態 | 完了条件 |
|---|---|---|
| M0 公開の土台 | メタデータ、CFF/BibTeX、manifest、Release処理を実装 | 実論文での公開と外部書式検証はM2/G6へ |
| M1 存在時刻証拠 | RFC3161、CA pin、nonce/OID、署名、現在と署名時点の証明書有効性、現在の全連鎖CRLを実装 | 一時CA試験と公開TSAの実証を混同しない |
| M2 実運用確認 | 公開前APIガードを追加。実TSA・実論文は未確認 | 信頼設定、公開TSA、2複製リポジトリでv1→v2、別環境検証 |
| M3 一般公開の独立観測 | 未実装 | 別管理主体が公開URLを取得して内容と時刻を署名。Actions自身を独立観測者と称さない |
| M4 閲覧・レビュー・保存 | 静的読者ページ、レビュー/応答/訂正/懸念/撤回、追記型記録を実装 | 人間の運用試験、Pages配備、任意DOI、GitHub外の保存・復元 |
| M5 v1.0受入 | 未達 | 下記の必須ゲートを満たし、独立レビューの重大指摘を解消 |

## 今回の運用拡張
- [x] APIで公開前にimmutable設定・既定ブランチ・版重複を確認。権限不足や障害では停止。
- [x] レビュー記録の対象版/PDFハッシュ、報告のハッシュ、利益相反、申告日時を検査。
- [x] baseコミットに対して既存記録の削除・書換えを拒否。管理者の全履歴書換え耐性ではない。
- [x] 静的HTML、原版ダウンロード、引用、撤回/懸念表示。内容はescapeしJavaScriptを実行しない。
- [x] 問題・レビュー・訂正のIssueフォーム、PRチェック、修正ループ、秘密情報の報告方針。
- [x] 同一CIで検査したソースとログを保存。14日artifactを永続アーカイブと呼ばない。

## 次の実行順と必要な担当
1. 開発担当がCIと差分を確認し、検証済みの実装だけを統合する。
2. 運用責任者がTSA、公開CA/CRLの出所、policy OID、時計精度、利用条件を確認し、信頼設定を承認する。
3. 管理者がTemplate/Immutable、読取token、branch ruleset、人間のPRレビューを設定する。
4. 著者が公開許諾済みPDF・著者情報・ライセンスを設定。合成データの実TSA試験後に本番公開する。
5. 別環境で9資産を検証し、訂正・撤回・障害復旧・バックアップ復元を実施する。
6. 独立したエンジニアがセキュリティレビューを行い、全重大指摘を回帰テスト付きで解消する。

**G6の進捗:** 公開時のpypdf strict構造検査、容量・ページ数・対話型機能制限、公式cffconvertと独立BibTeXパーサーによる公開前検査を追加（GitHub CIの実行結果が合格してから確定）。
**依然として未達:** PDF/A/PDF仕様の網羅的適合性、依存配布物のhash lock、
長期失効証拠保存/再タイムスタンプ、独立公開観測、DOI・外部保存。
今回のテスト成功だけでこれらを完了扱いにしない。

最終判断は[RELEASE_READINESS.md](RELEASE_READINESS.md)のG1〜G7を用いる。
[OPERATIONS.md](OPERATIONS.md)に失敗時の処置、[REVIEW_POLICY.md](REVIEW_POLICY.md)に人間の判断を記載。

PASSは指定入力・環境での機能試験成功、FAILは再現可能な不具合、未確認は未試験を意味する。
TSA時計、CA/CRLの出所、検証機時計、GitHub可用性の不確かさが残る。
時刻トークンのaccuracyはTSAの署名した申告で、本キットが測定した誤差ではない。

## 2026-11-06 — research objects and confidential commitments

- [x] Optional public research-data, analysis-code and protocol inventory with
      individual SHA-256, licenses, explicit public-confirmation flags and
      declared dependency relationships.
- [x] Deterministic TAR archive + JSON catalog, both signed indirectly through
      the same immutable manifest and RFC 3161 token as the paper.
- [x] Private-record HMAC-SHA256 receipts with per-record 256-bit offline keys;
      no raw records or keys are uploaded.
- [x] Standard-library offline TAR member verifier, safe bounds, tampering and
      privacy regression tests; static reader catalog display.
- [ ] Real TSA + immutable Release using a synthetic paper/data/private receipt;
      the full external system integration is not yet demonstrated.
- [ ] Independent medical/privacy threat assessment, access control, legal and
      retention policy; no real patient material should be used in CI.
- [ ] Off-GitHub archival and independent public-availability observation.

See `docs/RESEARCH_OBJECTS.md`; a green CI proves behavior in the test environment,
not the accuracy of medical records or a real-world public availability time.


## 2026-11-06 — Verified timestamp, portable preservation, witness/owner tooling

- [x] Real external FreeTSA evidence for TWO synthetic paper/data/code/private
  HMAC commitment versions; OpenSSL full-chain current CRL/CA/nonce/OID validation.
- [x] Separate machine restoration of byte-identical v1/v2 evidence archives
  with independently pinned ZIP digests and independently selected trust policy.
- [x] Preserve v1 when v2 is created; reject changed paper, wrong archive pin,
  ZIP traversal, duplicate members, symlinks and secret files.
- [x] CLI for explicit owner changes to immutable Releases and toolkit template
  setting (default read-only). Actual owner activation is not assumed.
- [x] CLI for external Ed25519-signed anonymous public Release observation,
  externally pinned public key and independent TSA verification.
- [x] Hash-locked dependency and CI plan; real clean CI install required to
  claim support for Python 3.10 / 3.12.
- [ ] Actual real author-approved immutable Release; confirm GitHub published
  assets, version continuity, off-repo verification and independent observer.
- [ ] Off-GitHub external custodian with tested recovery and retention; independent
  reviewer and long-term timestamp/signature-renewal policy.

These are concrete acceptance tests, not a promise that an external operator
will remain available forever. See [PRESERVATION_AND_WITNESS.md](PRESERVATION_AND_WITNESS.md).

## 2026-11-08 — signed witness receipt time anchoring

- [x] RFC 3161 verification over arbitrary SHA-256 digests without weakening the
      original Release manifest validation.
- [x] Optional independently timestamped witness receipt binds both
      observation JSON and Ed25519 signature in a domain-separated digest.
- [x] Strict validation of the witness's expected repository/version and the
      source identity claimed by the timestamped paper metadata.
- [x] Reject partial/forged witness tokens, changed signatures, extra claims,
      TSA failure, and untimestamped receipts when strict verification is requested.
- [ ] Independent operator must actually run the observer on an anonymously
      accessible, immutable GitHub Release and retain its own keys/evidence.
- [ ] Independent storage custodian, human scholarly review and long-term
      signature-renewal process remain operational blockers.

## 2026-11-08 — Explicit evidence-scope verifier

- [x] Test-first offline `verify_evidence.py` that rejects mixed paper/witness
  copies, missing trusted TSA proof, wrong repository/version and witness key pin.
- [x] Existence-only scope does not claim public access; witness scope requires
  a separately pinned Ed25519 observer key and timestamped signed observation.
- [x] Outputs parseable JSON with `verdict`, `scope`, and explicit independent
  operator, authorship, scientific truth and first-publication disclaimers.
- [ ] Real author-approved immutable GitHub Release, independent witness
  operator, independent storage custodian and documented external audit.

`PASS` in the chosen scope does not certify compliance with G3/G4/G5/G7.

## 2026-11-08 — Independent custodian audit implementation

- [x] Bounded multi-version ZIP deposit with out-of-band input archive pins,
  exact repository/tag binding and complete RFC 3161 verification.
- [x] Deterministic catalog that must be pinned **outside** the custody store.
- [x] Read-only auditor verifies complete archive inventory, exact ZIP bytes,
  valid source metadata, and independently trusted TSA/CRL evidence per version.
- [x] Fail on missing/extra historical versions, tampering, symlinks,
  duplicate tags, stale CRLs and invalid trust sources; cannot overwrite deposit.
- [ ] ACTUAL independent custodian, retention policy, periodic audits, access
  controls, off-GitHub replication and owner-approved published Release.
- [ ] Full LTV/historical revocation archival and renewal after TSA compromise.

A PASS from `custody.py` is a *local audit result*, not certification of the
custodian or its future survival. See [CUSTODY.md](CUSTODY.md).

## 2026-11-12 — GitHub-native evidence mirror

- [x] Code: mirror an independently pinned, timestamp-verified multi-version
  custody snapshot to a second GitHub repository's immutable Release; verify
  via anonymous HTTPS, SHA-256 pins and RFC 3161, with no Drive runtime.
- [ ] Operations: an owner with authenticated GitHub CLI actually publishes
  a mirror, and an independently managed observer verifies the public bytes.
- [ ] Durability: separate account custody and verified offline export/restore
  are evidenced; GitHub-wide failure remains a common-mode risk.

See [GitHub preservation](GITHUB_PRESERVATION.md). Do not call the code's
unit tests evidence of a real third-party archive or completed v1.0.
