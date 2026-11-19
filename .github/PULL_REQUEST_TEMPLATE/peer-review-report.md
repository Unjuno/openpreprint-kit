## Public peer-review report

- Round issue: <!-- canonical https://github.com/OWNER/REPO/issues/123 -->
- Exact release URL:
- Version:
- Paper PDF SHA-256 (64 lowercase hex):
- Reviewer GitHub account (must match this PR author):
- Conflict declaration: <!-- state none, or that a conflict was discussed privately with the editor; do not disclose private details here -->
- Consent to publish this report: <!-- yes/no; no means do not merge/publish this report -->
- Review scope:

## Report

Add a UTF-8 `.md` or `.txt` file under `reviews/evidence/`. Keep the report evidence based and version specific. Do not include confidential, personal, clinical, or unlicensed material.

## Record event

Append one `kind: "review"` event to `reviews/record.json` with the exact version, PDF SHA-256, round issue URL, reviewer account, conflict declaration, UTC claimed time, summary, and report SHA-256. Never edit or remove existing events.

## Checklist

- [ ] I reviewed the exact PDF bytes pinned above.
- [ ] The report is public and I consent to its publication.
- [ ] I checked the target version and SHA-256 in the round issue.
- [ ] This PR contains only the report and its append-only record event.
- [ ] No confidential or restricted information is included.

GitHub PR approval is a code review action. It does not itself count as a scholarly review report or editorial decision.
