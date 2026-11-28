# G6 human editorial and privacy handoff — 2026-11-29

**Status: REQUEST PACKAGE ONLY.** No real-person review, rights/consent/COI decision, correction exercise, or withdrawal exercise is recorded by this package. G6 remains BLOCKED until the actual actions are completed and their evidence is returned. AI and GitHub accounts controlled by the same owner cannot supply or impersonate those human decisions.

## Fixed review inputs

- Kit source: `Unjuno/openpreprint-kit`, main SHA `39346736ce91371b957ddbfa9b045cbe9409494f`.
- Complete tracked manuscript input inventory: [`G6-review-inputs-2026-11-29.json`](../../evidence/acceptance/G6-review-inputs-2026-11-29.json), SHA-256 `B300E4E0BF969E6506194FAE4544663407ED425833E282F99FB6E84AA89948F8`.
- The inventory contains 42 source files and the GitHub API metadata plus SHA-256 digests for every asset in all five public immutable paper Releases. Its status is explicitly `HANDOFF_INPUT_INVENTORY_ONLY_NOT_REVIEW_EVIDENCE`.
- Formal target releases: first paper v1/v2 and robustness paper v1.0.0/v2.0.1. Robustness v2.0.0 is an additional immutable intermediate release; it remains part of the inventory/history. A failed draft with ID `461075262` is recorded as historical and excluded from the review target.
- Public release routes: [paper v1](https://github.com/Unjuno/openpreprint-kit-paper/releases/tag/v1), [paper v2](https://github.com/Unjuno/openpreprint-kit-paper/releases/tag/v2), [robustness v1.0.0](https://github.com/Unjuno/openpreprint-kit-robustness-eval/releases/tag/v1.0.0), [robustness v2.0.1](https://github.com/Unjuno/openpreprint-kit-robustness-eval/releases/tag/v2.0.1), and retained [robustness v2.0.0](https://github.com/Unjuno/openpreprint-kit-robustness-eval/releases/tag/v2.0.0).

The releases are already public and immutable. The reviewer is evaluating existing published material and editorial/privacy decisions; this request does not authorize changing or removing any release.

## Request to the actual reviewer

> Please personally review the fixed manuscript and release inputs identified in the attached SHA-256 inventory. Confirm each copy against the manifest before reading it. Assess the scientific/editorial content within the scope you accept, copyright and third-party material, license statements, data and code provenance/licensing, publication consent, author display, conflicts of interest, privacy/re-identification risk, and absence of patient originals or secret keys. Record questions, answers, findings, and a final accept/reject/defer decision with reasons. State whether you are independent of the repository owner/authors and disclose any relationship or conflict. The owner manages both GitHub accounts `Unjuno` and `TAKAYASHIKIJUNYA`; those accounts must not be represented as two people. You may decline. Do not change or delete any existing immutable Release.

Please also complete two clearly labelled exercises on a disposable synthetic repository or test fixture only:

1. **Correction exercise:** make a synthetic correction as a new version while preserving the prior immutable version, then verify that the old version remains retrievable and verifiable.
2. **Withdrawal exercise:** mark a synthetic version as withdrawn/retracted in a new mutable notice or follow-on record while retaining the immutable release and checking that its existing assets remain retrievable and verifiable.

Do not perform either exercise against the actual paper repositories or releases. Label all artifacts and notices `EXERCISE — NOT AN ACTUAL WITHDRAWAL`.

## Return record — reviewer fills this in

- Reviewer name and verifiable identifier/contact: `UNFILLED`
- Date/time and review environment: `UNFILLED`
- Inventory SHA-256 checked: `UNFILLED`
- Scope read and scope not covered: `UNFILLED`
- Relationship to owner/authors; conflict disclosure; independence basis: `UNFILLED`
- Rights/copyright/third-party-material decision and rationale: `UNFILLED`
- License and data/code provenance decision and rationale: `UNFILLED`
- Publication consent and author-display decision and rationale: `UNFILLED`
- Privacy/re-identification and sensitive-material decision and rationale: `UNFILLED`
- Findings, owner responses, unresolved matters: `UNFILLED`
- Final decision (accept / reject / defer) and reasons: `UNFILLED`
- Correction exercise artifact/commit and old-version retrieval/verification result: `UNFILLED`
- Withdrawal exercise artifact/commit and old-version retrieval/verification result: `UNFILLED`
- Reviewer signature or equivalent verifiable confirmation and evidence URI/hash: `UNFILLED`

Store personal or sensitive review material in an appropriately restricted location. Publicly record only an approved summary and evidence fingerprints. Do not publish private contact details, sensitive COI details, or any credential, private key, or patient original.

## Stop conditions

Stop and return `REJECT` or `DEFER` with reasons if ownership or consent is unresolved, an inventory digest differs, sensitive material is found, a correction/withdrawal exercise would mutate an actual immutable Release, or the requested scope cannot be completed. Keep G6 BLOCKED until a real human has returned the completed record and both synthetic exercises have been verified.
