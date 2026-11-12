# v1.0 完成判定 / リリースを止める条件

**現在は実装済み機能の統合候補。一般利用向けv1.0完成とは宣言しない。**
完成判定は「コードが存在する」ではなく、独立した人・環境が操作と検証を再現できること。

| ゲート | 判定 | 必要な証拠 / 担当 |
|---|---|---|
| G1 単体・暗号・統合ガード試験 | 実行結果で判定 | 同一コミットのCIログ、テスト対象・件数 / 開発担当 |
| G2 実TSAの正常/異常系 | 未確認・BLOCK | 独立に承認したCA/CRL、公開TSAでの要求/応答/別環境検証 / 運用責任者 |
| G3 実論文を2つの複製リポジトリで公開 | 未確認・BLOCK | v1/v2、9資産、immutable=true、旧版保持、第三者再検証 / 著者と運用責任者 |
| G4 査読/訂正の実運用 | 未確認・BLOCK | 実担当者の同意、COI、版指定、応答、訂正/撤回通知の処理記録 / 人間の編集責任者 |
| G5 独立したセキュリティレビュー | 未実施・BLOCK | 開発者とは独立したレビュー、重大指摘の解決 / 外部エンジニア |
| G6 書式・依存・長期検証 | 未完了・BLOCK | pypdf構造・対話型チェックと外部CFF/BibTeX検査のCI成功、残るPDF/A網羅検査、依存hash lock、鍵/失効情報更新と保存試験 / 開発・運用 |
| G7 独立公開観測・外部保存 | 未実装/未確認 | 管理主体の別な観測と保存。一般公開時刻や永続保存を保証する場合に必須 |

独立レビューを実行するサブエージェントは今回の環境では起動できなかった。
テストと自己点検を独立レビューと呼ばない。起動可能な開発環境または人間の
ソフトウェアエンジニアに、以下のレビュー項目を渡す。

## 独立レビューへの引継ぎ
対象: PR #2の時刻証明コードと、operational-readinessブランチの追加分。
最低限: 信頼ストア分離、CRL/期限判定、malformed ASN.1、API例外、設定変更競合、
未信頼PRでの秘密情報露出、版とレビューの結合、履歴の破壊、HTML注入、復旧手順。
`python -m unittest discover -s tests -v` を実行し、テストで覆われていない攻撃入力を探す。
発見事項は再現テスト、影響、修正条件を添えてIssue/PRに残す。

## 完成表示の禁止事項
未実施の公開を「E2E成功」、自己署名試験を「公共認証局で実証」、レビューの存在を
「査読済み」、ハッシュ一致を「論文が正しい」、HTTP到達時刻を「初公開時刻」と表示しない。
実装できない権限操作や外部手続は、担当者・必要な操作・完了証拠を明記して残す。


## 2026-11-06: Verified public TSA and portable recovery acceptance

- **G2 synthetic external TSA:** An actual FreeTSA issuance for synthetic v1/v2
  was observed with pinned CA PEM SHA-256
  `2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438`
  and explicit OID `1.2.3.4.1`. Validity and current full-chain CRLs were
  verified. Accuracy absent -> no exact signed time-error bound.
- **G3 still NOT MET:** no real author-approved GitHub immutable Release, no
  two independent template-derived repositories with real versioned assets.
- **G4/G5 still NOT MET:** no genuine human peer review or independent software
  security/privacy audit. Generated review records are not certifications.
- **G6 partial:** sha256-hash locked build/runtime dependencies, PDF and citation
  validation, archive restoration tests. CI Python 3.10/3.12 is the final check.
  Full historic LTV and signature renewal not implemented.
- **G7 partial:** separate-key Ed25519 public witness CLI and portable retention
  archive implemented; **not** yet exercised against a truly public immutable
  Release by a separately managed observer, no external durable escrow.
- A synthetic data exercise established v1 and v2 time-anchored research-object
  bundles, tamper rejection and byte-identical recovery on an alternate machine.
  Source: the test-run audit report and separately verified ZIP digests.
- A 14-day GitHub Actions artifact is NOT an external permanent repository.
- `is_template` and `has_pages` require administrator action; do not equate
  availability of a CLI with actual setting activation.
- Production v1.0 remains BLOCKED until remaining G3/G4/G5/G7 conditions have
  dated evidence from responsible external parties.

The standalone helper details and safe CLI are in
[PRESERVATION_AND_WITNESS.md](PRESERVATION_AND_WITNESS.md).

## 2026-11-08 — witness evidence verification enhancement

Witness tooling can now request a second RFC 3161 timestamp **for the signed
witness statement itself**, not just the original paper manifest. This adds a
verifiable TSA upper bound on the signed witness statement's existence, even
when the witness's local clock is untrusted. It does not authenticate the
observation's truth, first public availability, or witness independence.

This work is an implementation and test milestone for G7; it does **not** clear
G3/G4/G5/G7 operational acceptance. An independent witness and long-term
archive custodian have still not executed the required tests. CLI verification
requires out-of-band `--expected-repository` and `--expected-version`.

## 2026-11-08 — One-command offline verification

The unified `scripts/verify_evidence.py` CLI composes integrity, release time,
expected source identity and—only when explicitly requested—signed and
RFC 3161-timestamped witness evidence. Tests use an ephemeral real OpenSSL
TSA and Ed25519 keys and must pass in both supported GitHub Python runners.
This removes a usability gap; it does **not** close G3, G4, G5 or G7 without
external operational evidence. A verified witness assertion is not proof of
its operator's genuine independence or of first public availability.

## 2026-11-08 — Custodial audit code, not a custody service

The `custody.py` CLI now supports external-pin-controlled, multi-version
archive deposit and read-only integrity/RFC 3161 audits. The cryptographic
checks include all archived assets and re-check the independently selected
TSA certificate chain and CRLs. An absent or modified version fails.

**G7 REMAINS BLOCKED**: no independent off-GitHub custodian has contracted
for retention, published externally verified restored evidence, performed
ongoing audits or established service/incident obligations. CLI installation
is not an operational attestation, and this milestone does not clear human
peer review, clinical privacy approval or certified long-term validation.

## 2026-11-12 — GitHub-only archival backend

**Canonical online storage:** source immutable paper Releases and a second GitHub
repository's immutable evidence mirror Releases (scripts/github_mirror.py).
No Google Drive integration or second cloud provider is required. The verifier
uses anonymous HTTPS and out-of-band SHA-256 catalog and receipt pins.
Mirror publication preflights the **actual published source** and its GitHub
release/asset attestations, then audits every replica with real RFC 3161 checks.

A mirror under the same GitHub service does **not** establish resilience to a
GitHub-wide outage. G5 requires genuine tested offline export and recovery;
independently managed operators and historical certificate/CRL renewal still
require evidence. The current test suite mocks GitHub writes and cannot
certify an actual public mirror. See [GITHUB_PRESERVATION.md](GITHUB_PRESERVATION.md).

## 2026-11-12: Forward existence-time evidence renewal

The new `renewal.py` provides independently pinned linked RFC 3161 re-attestation of the **exact** original preservation archive and prior tokens, with a verified ZIP for separate GitHub Releases. Both source and renewal CA/CRL chains must verify **currently**; expired or revoked older proofs remain blockers. RFC 4998 evidence records, historical LTV validation, key compromise tolerance and real independently managed operations remain **NOT ESTABLISHED**.
