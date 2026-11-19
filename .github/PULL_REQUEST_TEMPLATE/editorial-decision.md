## Public editor decision for a collaborative review round

- Round issue:
- Exact version:
- Paper PDF SHA-256:
- Distinct public reviewer accounts and report event IDs:
- Author response event ID:
- Editor GitHub account (must differ from the reviewers and author responders):
- Conflict declaration and handling:
- Decision: `accept`, `revise`, `decline`, or `pause`

## Rationale

Summarize how the public reports and author response were considered. The editor owns the decision. AI may help organize comments but may not decide or create a human identity.

## Record event

Append one `kind: "editorial_decision"` event to `reviews/record.json`. Include `round_issue` and the `decision` field. The validator requires at least two distinct review actors, an author response, and an editor distinct from reviewers and responders for the exact version/PDF hash/round.

## Checklist

- [ ] At least two distinct reviewer accounts submitted public reports for this exact version and hash.
- [ ] The author response is recorded.
- [ ] The editor is distinct from the reviewers and responders.
- [ ] Conflicts were handled and the decision rationale is public.
- [ ] No prior report, response or event was edited or deleted.
- [ ] A `revise` outcome starts a new version and new round; earlier records remain attached to the old version.
