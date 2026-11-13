# OpenPreprint Kit

## First paper: v1 immutable GitHub Release published (2026-11-14)

The [first OpenPreprint Kit manuscript](manuscripts/openpreprint-kit/README.md) is publicly available as [the immutable paper v1 Release](https://github.com/Unjuno/openpreprint-kit-paper/releases/tag/v1) (Release ID 444659219; GitHub API: `draft=false`, `immutable=true`, 11 assets). The published `paper.pdf` has the exact approved SHA-256 `0860b735379fb1b9b223f5d535442dae8421f456d7ae1c6bf6ce8d3141a1b07c`. The [owner's publication evidence](https://github.com/Unjuno/openpreprint-kit/issues/5#issuecomment-6863092530) records a **separate approved continuation** after the initial Windows citation-validator subprocess failed; it reports fresh RFC 3161 validation, Release and asset attestations, anonymous retrieval and offline restore. Both the original failure and continuation reports are retained outside the repository. The publication was owner-controlled, **not independent human verification**; the paper is unreviewed, and first-publication time, author identity, scientific correctness, independent custody and toolkit v1.0 acceptance remain unproven. The reusable template root remains v0/UNSPECIFIED. **Do not re-run the one-time `--publish` launcher against this existing paper repository.**

## GitHub-only publication and preservation (2026-11-12)

**Online publication and replicated preservation are GitHub-native.** Each paper
has versioned immutable GitHub Releases; separate GitHub evidence repositories
store verified research-object ZIPs and pinned custody catalogs as immutable
Releases. `scripts/github_mirror.py` (optionally use `verify --require-source-release` to verify that original immutable Releases and their bytes remain publicly available) provides offline `plan`, explicit
owner-authenticated `publish --apply`, and credential-free anonymous `verify`
with independently supplied SHA-256 pins and a separately trusted RFC 3161
policy. See [GitHub-only preservation](docs/GITHUB_PRESERVATION.md). **No Google
Drive runtime integration is necessary.** The prior one-off Drive test is only
historical evidence, not the supported architecture.

A second GitHub repository is still dependent on GitHub's platform and does
not by itself prove independent custody or full-site disaster recovery. Such
claims require an operator-controlled offline export, independently held hashes
and an actual restore test. The v1.0 acceptance gates remain strict.

**v1.0 release decision:** [objective acceptance gates](docs/V1_ACCEPTANCE.md) · [current readiness](docs/RELEASE_READINESS.md). First **paper** Release v1 is public, but toolkit **software** v1.0.0 is still NO-GO: the remaining multi-version tests, independent public witness, separate custodian, human review and security/privacy audit are not accepted.

**GitHubを論文公開の本体にする、再利用可能なプレプリント公開キット。**

現行ソフトウェアは受入試験中の開発版です。**一般利用向けv1.0の運用受入は未完了**です。
[完成判定表](docs/RELEASE_READINESS.md)と[ロードマップ](docs/ROADMAP.md)に未達条件を示します。
論文の版番号（v1、v2）とキットのソフトウェア版番号は別です。

## One-command offline verification (two explicit evidence scopes)

`verify_evidence.py` composes SHA-256 content verification, a separately trusted
RFC 3161 timestamp, and (optionally) an Ed25519-signed **and RFC 3161-timestamped**
independent-witness record. The verifier never fetches URLs; download and
separately pin the evidence and trust policy before running it.

```bash
# Content and existence-time evidence only — NOT evidence of public access.
python scripts/verify_evidence.py --scope existence \
  --bundle downloaded-release --policy /trusted/timestamp-policy.json \
  --repository OWNER/PAPER --version v1

# Signed public-retrieval ASSERTION, matched to all the same Release bytes.
python scripts/verify_evidence.py --scope public-observation \
  --bundle downloaded-release --policy /trusted/timestamp-policy.json \
  --repository OWNER/PAPER --version v1 \
  --witness /trusted/witness-v1 \
  --observer-public-key /trusted/witness-public.pem \
  --observer-public-key-sha256 INDEPENDENTLY_PINNED_SHA256
```

Both commands return structured JSON. `verdict: PASS` applies only to the
requested `scope`; first-publication time, author identity, scientific validity
and genuine witness independence remain `NOT_PROVEN`/`NOT_VERIFIED`. For the
health-record original, verification still requires the private HMAC key and
separate authorized disclosure via `private_seal.py`: this command never reads
or uploads a patient's original record. See [operational detail](docs/PRESERVATION_AND_WITNESS.md).

## Operational pilot — next owner action

A reviewed owner-authenticated execution of [the synthetic publication pilot](docs/OPERATIONAL_PILOT.md)
creates two **new** `opk-demo-*` template repositories, publishes v1/v2 with
immutable Release + asset attestations, anonymously re-downloads and verifies
every byte, and restores all four evidence archives. `scripts/pilot.py` defaults
to a **no-I/O plan**; only `--publish-synthetic` authorizes public changes.
It never reads a user's real paper or patient records and never claims that its
own retrieval is an independent witness. Existing destinations are refused.

[2026-11-12 evidence and remaining boundaries](docs/STATUS_2026-11-12.md).

## Public research objects and private-record verification (research extension)

A Release can now bind the paper to explicit **public data**, **analysis code**,
**supplementary protocols** and **anonymous private-record commitments**.
Declare public files and their licenses in `research-assets.yaml` and run:

```bash
python scripts/research_package.py --check
```

When declared research objects exist, the Release adds `research-assets.json`
and deterministic `research-assets.tar`; both are hashed in the same main
manifest that is subsequently timestamped. `verify_release.py` checks every
inner file without unpacking the archive to disk. Readers see the declared
data/code relationships and verification digests in the static page.

**Health/medical records must NEVER be pushed to public GitHub.** Locally
create a *per-record* HMAC-SHA256 receipt with `scripts/private_seal.py`,
store the 256-bit secret key and original outside the repository, and include
only its anonymous JSON receipt. A third-party verifier requires the original
and corresponding key, plus independently verified Release and timestamp
proofs. This is **tamper-evidence, not literal tamper-prevention**, not
patient identification, and not a medical-content certification.

Full usage and threat model: [Research objects and privacy](docs/RESEARCH_OBJECTS.md).


## Verified delivery, recovery and independent observation (completion work)

The opt-in `scripts/preserve.py` makes a deterministic, allowlisted ZIP of
release assets and publicly available verification snapshots. Extraction is
verified against an independently retained SHA-256 and **separately selected
TSA trust policy**; no secret key or medical original may enter a public ZIP.
`--integrity-only` clearly disclaims the authenticity of time evidence.

The opt-in `scripts/observation.py` permits an external organization to
anonymously retrieve and sign the exact public Release assets, under its own
Ed25519 witness key. The optional `--timestamp-observation` additionally
obtains an external RFC 3161 token covering **both the signed observation and
its Ed25519 signature**. A verifier can require that token and must specify
the expected repository/tag when using the CLI. Only an out-of-band pinned public key authenticates that
claim; the witness's clock is self-reported and **first publication is not
proven**. `scripts/acceptance.py` generates two synthetic research versions,
obtains real RFC 3161 evidence and tests restore and tamper rejection without
publishing research or patient originals.

Published dependencies for CI are SHA-256-locked in `requirements.lock` and
`requirements-build.lock` (Python 3.10/3.12 hosted runner compatibility must
be verified in CI). Owners can use `scripts/owner_setup.py` to inspect and
**explicitly** enable public repo template / immutable release settings.
Detailed commands and limitations: [Preservation & witness](docs/PRESERVATION_AND_WITNESS.md).

**This is not a v1.0 production readiness certification.** Real author-approved
publications, independent reviewer/witness custody, long-term escrow and
clinical privacy/legal acceptance remain distinct operational gates.

## Independent archive custody and read-only audits (development feature)

An independent archivist can use `scripts/custody.py` to deposit multiple
versioned `.opk.zip` archives, requiring an **out-of-band digest for every ZIP**,
a separately selected RFC 3161 trust policy, and exact repository/version
identity. `deposit` never overwrites existing custody; `audit` requires an
**out-of-band SHA-256 of the custody catalog** and re-verifies every version
without calling GitHub. It refuses missing versions, changed archives,
symlinks, modified catalog, and stale CRL evidence.

This tool does not establish the operator's independence, long-term retention,
confidential health-data storage, or third-party auditing. For operator commands,
trust boundaries and recovery see [Custody runbook](docs/CUSTODY.md).

## 機能と限界

| 機能 | 状態 |
|---|---|
| メタデータ、ORCID、PDF構造検査 | 開発中。公開時は25 MiB以下・500ページ以下、非暗号化、対話型機能なしのPDFを要求。PDF/A認証やマルウェア検査ではない |
| CFF/BibTeX、metadata、manifest、SHA-256 | 決定的生成・ハッシュ照合。発行前に外部CFFスキーマとBibTeXパーサーも実行 |
| RFC 3161 | 要求、HTTPS送信、署名/連鎖/nonce/OID/現在のCRLの検証 |
| GitHub公開 | 手動起動。公開前APIガードとdraft再ダウンロード検証 |
| レビュー/応答/訂正/懸念/撤回 | 版とPDF/報告書ハッシュに結合。CIで既存記録の変更を拒否 |
| 読者ページ | 静的HTML生成。撤回・懸念を明示。自動デプロイなし |
| 実TSA・実論文での運用、独立レビュー | 第1論文v1の実GitHub Immutable Release公開済み（P1）。別利用者による4版運用受入と独立人間レビューは未達 |
| 公開観測・保管、DOI、長期保存 | 観測/保管CLIは実装済み。独立運用・DOI・長期保証は未達 |

## Forward timestamp renewal (experimental)

`scripts/renewal.py` can re-timestamp a verified public preservation ZIP and the complete preceding RFC 3161 renewal evidence, keeping original immutable Releases byte-for-byte. A separately pinned deterministic renewal ZIP can be published in a **new** immutable GitHub Release. **This is not RFC 4998 ERS or historical long-term signature validation**. See [forward renewal procedure](docs/FORWARD_RENEWAL.md).

## 利用開始

配布元のSettings → General → Template repositoryを有効にし、論文ごとに
Use this templateからPublic Repositoryを作ります。`preprint.yaml`と`paper/paper.pdf`を設定します。
初期状態は仮データとv0であり、そのまま公開できません。

```bash
python -m pip install -r requirements.txt -r requirements-publication-checks.txt
python scripts/validate.py --strict
python scripts/research_record.py
python scripts/prepare_release.py --output dist
python scripts/verify_release.py dist
python scripts/citation_validation.py dist
```

Python 3.10以上、OpenSSL 3、PyYAML 6.0.3、asn1crypto 1.5.1、pypdf 6.21.4を使用します。
公開前の引用書式検査にはcffconvert 2.0.0、bibtexparser 1.4.3も使用します。
ハッシュ整合検査と研究記録/読者ページの処理はPython標準ライブラリで動作します。

## 時刻証明と公開

[時刻証明手順](docs/TIMESTAMPS.md)に従い、独立に確認したCA/CRLとTSA方針から
`timestamp-policy.json`を設定します。同梱されていたという理由だけでCAを信頼しないでください。

```bash
python scripts/timestamp.py stamp dist --policy timestamp-policy.json
python scripts/timestamp.py verify dist --policy timestamp-policy.json
```

論文リポジトリでImmutable Releasesを有効にし、対象リポジトリの**Administration:read**を持つ
短命なtokenをActions secret **OPK_ADMIN_READ_TOKEN**へ設定します。ソースやチャットには貼りません。
完成原稿だけを対象にActions → Publish preprint releaseを手動起動します。

PDF構造/メタデータ検査 → bundle → CFF/BibTeXスキーマ検査 → APIで公開前条件確認 → TSA → draft → 全公開資産を再取得・検証 →
immutability再確認 → 公開 → 公開後確認。権限不足・API障害・証明不成立では停止します。
確認と公開は原子的ではありません。公開後の失敗で公開を巻き戻せたとは主張しません。
[運用手順](docs/OPERATIONS.md)に復旧方法と必要権限を記載しています。

9資産はPDF、metadata JSON、CITATION.cff、BibTeX、manifest、SHA256SUMS、Release説明、
RFC 3161要求と応答です。研究データ等を含む場合はJSONカタログとTARを加えた11資産です。旧7資産も整合検査できます。添付CFFだけではリポジトリの引用ウィジェットは設定されません。
`time_attestation: null`は時刻証拠をJSON内に埋め込まない意味で、外部sidecarを検証して判断します。

## レビューと訂正

[査読・訂正方針](docs/REVIEW_POLICY.md)に従い、公開許諾を得た報告を`reviews/evidence/`へ置き、
`reviews/record.json`へ追記します。名前と日時は申告情報であり、CI成功やAI評価を「査読済み」とは表示しません。
原版を消して修正せず、新版と理由を残します。機密査読は公開リポジトリで行いません。

```bash
python scripts/build_site.py downloaded-release --repository OWNER/PAPER --output site
```

ActionsのBuild reader siteでも生成できます。ページには撤回・懸念を表示し、原本を保持します。
ページ単独でタイムスタンプを検証したとは表示しません。研究記録は元の時刻証明とは別の未署名スナップショットです。

## テスト・問題修正

```bash
python -m unittest discover -s tests -v
```

試験は一時CA/TSAと合成データを使用し、GitHub APIの異常系は模擬応答で検査します。
実サービスの運用実証ではありません。CIはPython 3.10/3.12で検査し、試験済みソースとログを14日保存します。
[貢献手順](CONTRIBUTING.md)の再現テスト→修正→全件試験→人間のレビューを運用に組み込みます。
秘密情報は公開Issueへ出さず、[SECURITY.md](SECURITY.md)を確認してください。

## 保証とライセンス

存在時刻、一般公開時刻、著作者資格、科学的正しさは別です。[脅威モデル](docs/THREAT_MODEL.md)を参照してください。
学術出版（版・引用）、暗号学/PKI（署名・信頼）、保存・分散システム（独立観測）を分離しています。
ツールはMIT。論文・図表・データの利用条件は研究者が別に指定してください。
