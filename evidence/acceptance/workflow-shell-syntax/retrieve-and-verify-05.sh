set -euo pipefail
root="$RUNNER_TEMP/opk"
while IFS=' ' read -r label repo tag paper_sha; do
  echo "=== $repo $tag ==="
  gh release verify "$tag" --repo "$repo" | tee "$root/$label-attestation.txt"
  python scripts/verify_release.py "$root/releases/$label" --expected-paper-sha256 "$paper_sha"
  python scripts/citation_validation.py "$root/releases/$label"
  python scripts/timestamp.py verify "$root/releases/$label" --policy "$root/trust/policy.json" > "$root/$label-timestamp.json"
  python - "$root/$label-timestamp.json" <<'PY'
import json,sys
report=json.load(open(sys.argv[1],encoding='utf-8'))
assert report['status']=='VERIFIED'
assert report['revocation']=='checked_current_crls_full_chain'
print('PASS: RFC 3161 signature, policy, source-pinned CA, certificate chain and current CRL')
PY
  python scripts/preserve.py pack "$root/releases/$label" --out "$root/$label.opk.zip" --policy "$root/trust/policy.json" > "$root/$label-preservation.json"
  (cd "$root" && sha256sum "$label.opk.zip" > "$label.opk.zip.sha256")
done <<'EOF'
paper-v1 Unjuno/openpreprint-kit-paper v1 0860b735379fb1b9b223f5d535442dae8421f456d7ae1c6bf6ce8d3141a1b07c
paper-v2 Unjuno/openpreprint-kit-paper v2 18e13ff3ccf37632cc86ede322687a32d2f959494672df52d78901cabe745805
robustness-v1.0.0 Unjuno/openpreprint-kit-robustness-eval v1.0.0 92774a6552f0aaf9315baea6e9672677903a1bdb64288dfddf449cffb3de53a4
robustness-v2.0.0 Unjuno/openpreprint-kit-robustness-eval v2.0.0 d63876e1f83c2b6bd39c48ef7b7779c88679f3b95faaedbc29d31dc6194d5676
robustness-v2.0.1 Unjuno/openpreprint-kit-robustness-eval v2.0.1 d63876e1f83c2b6bd39c48ef7b7779c88679f3b95faaedbc29d31dc6194d5676
EOF
