#!/usr/bin/env bash
# Owner-operated first publication. No token is printed or supplied by chat.
set -euo pipefail
if [[ $# -eq 0 || ( $# -eq 1 && $1 == '--plan' ) ]]; then
  printf '%s\n' 'PLAN_ONLY: no network, output, or publication.' \
    'Target: NEW Unjuno/openpreprint-kit-paper; author Unjuno; CC BY 4.0; v1.' \
    'Run with --publish only from an owner-authenticated GitHub CLI environment.'
  exit 0
fi
if [[ $# -ne 1 || $1 != '--publish' ]]; then
  printf '%s\n' 'Usage: bash scripts/publish_first_paper.sh [--plan|--publish]' >&2
  exit 2
fi
for tool in python3 gh curl openssl sha256sum mktemp; do
  command -v "$tool" >/dev/null || { printf 'Required tool missing: %s\n' "$tool" >&2; exit 1; }
done
openssl version | grep -q '^OpenSSL 3\.' || { echo 'OpenSSL 3 is required.' >&2; exit 1; }
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
# Version-controlled, previously approved PDF; do not depend on expiring run 43279522755 artifacts.
PDF="$ROOT/manuscripts/openpreprint-kit/approved-v1/paper.pdf"
PDF_SHA=0860b735379fb1b9b223f5d535442dae8421f456d7ae1c6bf6ce8d3141a1b07c
[[ -f "$PDF" && ! -L "$PDF" ]] || { echo 'Approved versioned PDF is missing or linked; refusing substitution.' >&2; exit 1; }
printf '%s  %s\n' "$PDF_SHA" "$PDF" | sha256sum -c -
gh auth status --hostname github.com
[[ $(gh api repos/Unjuno/openpreprint-kit --jq '.is_template') == true ]] || { echo 'Owner must enable the toolkit Template repository setting before publication.' >&2; exit 1; }
WORK=$(mktemp -d "${TMPDIR:-/tmp}/opk-first-paper-publication.XXXXXXXX")
export WORK
trap 'rc=$?; printf "Stopped (%s). Evidence remains at %s. Inspect GitHub; no rollback is claimed.\n" "$rc" "$WORK" >&2; exit "$rc"' ERR
printf 'Owner-run evidence directory: %s\n' "$WORK"
python3 -m venv "$WORK/venv"
PY="$WORK/venv/bin/python"
"$PY" -m pip install --require-hashes -r "$ROOT/requirements-build.lock"
"$PY" -m pip install --require-hashes --no-build-isolation -r "$ROOT/requirements.lock"
mkdir -p "$WORK/trust"
# Trust root is selected here independently of the paper archive. Never change
# a failed pin just to make verification succeed; stop for owner review instead.
curl --proto '=https' --tlsv1.2 --fail --max-time 45 \
  https://freetsa.org/files/cacert.pem -o "$WORK/trust/ca.pem"
printf '%s  %s\n' 2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438 \
  "$WORK/trust/ca.pem" | sha256sum -c -
curl --proto '=https' --tlsv1.2 --fail --max-time 45 \
  https://www.freetsa.org/crl/root_ca.crl -o "$WORK/trust/crl.pem"
openssl crl -in "$WORK/trust/crl.pem" -noout -verify -CAfile "$WORK/trust/ca.pem"
"$PY" - <<'PY'
import json, os
from pathlib import Path
p=Path(os.environ['WORK'])/'trust'/'policy.json'
p.write_text(json.dumps({
 'schema_version':1,'tsa_url':'https://freetsa.org/tsr','ca_file':'ca.pem',
 'ca_sha256':'2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438',
 'crl_file':'crl.pem','policy_oid':'1.2.3.4.1','timeout_seconds':45
},sort_keys=True,indent=2)+'\n',encoding='utf-8')
PY
# The verifier checks CRL validity and signature chains, not merely this download.
"$PY" "$ROOT/scripts/first_paper_publish.py" \
  --repository Unjuno/openpreprint-kit-paper \
  --paper-pdf "$PDF" --paper-sha256 "$PDF_SHA" \
  --policy "$WORK/trust/policy.json" --out "$WORK/publication" --publish
printf 'Publication checks completed. Preserve the report and evidence from: %s\n' "$WORK/publication"
printf '%s\n' 'This is not an independent witness, human peer review, or production v1.0 certification.'
