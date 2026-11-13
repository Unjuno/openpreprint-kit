# First approved paper publication plan

Goal: a bounded owner-authenticated path from the approved Unjuno/CC-BY-4.0 v1 manuscript to a new dedicated GitHub repository and verified immutable Release. No new approval request, no test data substituted for the real manuscript.

Architecture: reuse current selftest, strict metadata, pilot GitHub adapter, preflight, RFC3161, anonymous observation downloader and preservation verifier. The default command is read-only PLAN_ONLY. --publish explicitly creates the new public paper repository and enables immutability; existing repos/output are refused. No secrets are copied, printed or embedded in archives. Actual owner authority must be supplied through native gh authentication, not bypassed via connector permissions.

Tests first: read-only plan; forbidden existing destination/invalid names; PDF fingerprint mismatch before API writes; positive actual byte/crypto path using mocked GitHub only; immutability readback failure; corrupted draft prevents promotion; source binding; post-publish attestation failure remains public-pending and never reported rolled back.

Completion: focused tests + full supported-version CI, source readback and a scoped PR. Real public release remains unverified until an owner-authorized run succeeds; unit mocks do not close production gates. Do not repeat author/licence approval questions.
