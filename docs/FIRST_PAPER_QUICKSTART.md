# 第1論文の最終発行 / First-paper final publication

## Single owner command

On Linux, after `gh auth login --hostname github.com`, from a trusted checkout run:

```bash
bash scripts/publish_first_paper.sh --publish
```

This installs the hash-locked dependencies into a new isolated temporary environment, retrieves the already-approved PDF from run 43279522755, checks its fixed SHA-256, fetches the independently pinned FreeTSA CA and current signed CRL, and invokes the publisher below. The output directory is printed and retained even on failure. With no argument or `--plan`, it prints a plan only and performs no network or file operations. It requires Python with venv, GitHub CLI, curl, OpenSSL 3 and sha256sum.

**Real public side effects:** the target is one NEW `Unjuno/openpreprint-kit-paper`. Its immutability setting is enabled; public inputs and one v1 Release are created. Existing repositories are never reused. The original artifact expires after its GitHub retention period; if download fails, stop and use the pinned PDF plus explicit advanced command below rather than substitute another version. There is no embedded token, no automatic trust of certificates in the evidence archive, and no change to the user's global git authentication configuration.


Advanced options, failure handling and evidence limits: [FIRST_PAPER_PUBLICATION.md](FIRST_PAPER_PUBLICATION.md).

Author Unjuno / manuscript CC BY 4.0 / version v1 are already approved. This command does not claim independent review, independent observer operation or full-kit production acceptance. No actual public Release has been executed by the chat connection.
