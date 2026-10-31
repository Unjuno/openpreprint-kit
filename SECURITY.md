# Security reporting

Do not publish credentials, participant information, private manuscripts, or exploit
payloads containing real secrets in a public Issue. Use GitHub private vulnerability
reporting **only if the repository owner has enabled it**. Otherwise ask the owner
for a private reporting channel without posting sensitive details. No private channel
is automatically provisioned by this template.

Include affected commit, minimal reproduction with synthetic data, impact, and a
proposed regression test. Preserve evidence; revoke exposed credentials with their
provider. Do not assume deleting a Git commit erases copies already downloaded.

Current trust boundaries and unsupported guarantees are documented in
[THREAT_MODEL.md](docs/THREAT_MODEL.md) and [RELEASE_READINESS.md](docs/RELEASE_READINESS.md).
