#!/usr/bin/env bash
set -euo pipefail

VENV=/tmp/opk-r139-venv
REPO=/mnt/c/Users/junny/Documents/Codex/2026-11-15/files-mentioned-by-the-user-opk/work/current-acceptance-handoff-r139
BASE=/mnt/c/Users/junny/Documents/Codex/2026-11-15/files-mentioned-by-the-user-opk/outputs/Gold-Candidate-2026-11-29-r138-kit-codeql-policy-review
OUT="$REPO/evidence/acceptance/wsl-g3-verification"
POLICY="$REPO/evidence/acceptance/trust-r139/timestamp-policy.json"
mkdir -p "$OUT"

verify_one() {
  local label="$1"
  local bundle="$2"
  "$VENV/bin/python" "$REPO/scripts/timestamp.py" verify "$bundle" --policy "$POLICY" \
    > "$OUT/$label.json" 2> "$OUT/$label.stderr"
  "$VENV/bin/python" -c 'import json,sys; d=json.load(open(sys.argv[1])); print(sys.argv[2], d.get("status"), d.get("tsa_time_utc"), d.get("openssl"))' \
    "$OUT/$label.json" "$label"
}

verify_one paper-v1 "$BASE/evidence/r117-four-release-recheck-2026-11-28/paper-v1/preservation/restored-offline/bundle"
verify_one paper-v2 "$BASE/evidence/r117-four-release-recheck-2026-11-28/paper-v2/preservation/restored-offline/bundle"
verify_one robustness-v1.0.0 "$BASE/evidence/r117-four-release-recheck-2026-11-28/robust-v1.0.0/preservation/restored-offline/bundle"
verify_one robustness-v2.0.1 "$BASE/evidence/r117-four-release-recheck-2026-11-28/robust-v2.0.1/preservation/restored-offline/bundle"
verify_one robustness-v2.0.0 "$BASE/evidence/R136-published-second-paper-releases-2026-11-29/published-release-audit/offline-restored/v2.0.0"
