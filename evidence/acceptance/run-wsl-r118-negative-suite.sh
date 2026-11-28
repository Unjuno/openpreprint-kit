#!/usr/bin/env bash
set -u
REPO=/mnt/c/Users/junny/Documents/Codex/2026-11-15/files-mentioned-by-the-user-opk/work/current-acceptance-handoff-r139
NEG=/mnt/c/Users/junny/Documents/Codex/2026-11-15/files-mentioned-by-the-user-opk/outputs/r139-wsl-negative-suite
BASE=/mnt/c/Users/junny/Documents/Codex/2026-11-15/files-mentioned-by-the-user-opk/outputs/Gold-Candidate-2026-11-29-r138-kit-codeql-policy-review/evidence/r117-four-release-recheck-2026-11-28/paper-v1/preservation/restored-offline/bundle
POLICY="$REPO/evidence/acceptance/wsl-negative-trust/timestamp-policy.json"
OPK_SOURCE_ROOT="$REPO" \
OPK_NEGATIVE_DIR="$NEG" \
OPK_BASE_BUNDLE="$BASE" \
OPK_POLICY_PATH="$POLICY" \
OPK_OPENSSL=openssl \
  /tmp/opk-r139-venv/bin/python "$NEG/negative-suite-runner-r117.py" > "$NEG/wsl-r118-negative-run.log" 2>&1
status=$?
tail -n 28 "$NEG/wsl-r118-negative-run.log"
exit "$status"
