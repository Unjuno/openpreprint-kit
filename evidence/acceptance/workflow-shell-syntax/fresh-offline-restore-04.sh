set -euo pipefail
received="$RUNNER_TEMP/received"
result="$RUNNER_TEMP/fresh-offline"
mkdir -p "$result"
while IFS=' ' read -r label paper_sha; do
  echo "=== fresh runner: $label ==="
  (cd "$received" && sha256sum -c "$label.opk.zip.sha256")
  expected=$(cut -d ' ' -f1 "$received/$label.opk.zip.sha256")
  python scripts/preserve.py restore "$received/$label.opk.zip" --out "$result/$label" --expected-sha256 "$expected" --policy "$received/trust/policy.json" > "$result/$label-restore.json"
  python scripts/verify_release.py "$result/$label/bundle" --expected-paper-sha256 "$paper_sha"
  python scripts/citation_validation.py "$result/$label/bundle"
  python scripts/timestamp.py verify "$result/$label/bundle" --policy "$received/trust/policy.json" > "$result/$label-timestamp.json"
  find "$received/releases/$label" -maxdepth 1 -type f -print0 | while IFS= read -r -d '' file; do cmp "$file" "$result/$label/bundle/$(basename "$file")"; done
  echo "PASS: fresh-runner offline restore and byte comparison for $label"
done <<'EOF'
paper-v1 0860b735379fb1b9b223f5d535442dae8421f456d7ae1c6bf6ce8d3141a1b07c
paper-v2 18e13ff3ccf37632cc86ede322687a32d2f959494672df52d78901cabe745805
robustness-v1.0.0 92774a6552f0aaf9315baea6e9672677903a1bdb64288dfddf449cffb3de53a4
robustness-v2.0.0 d63876e1f83c2b6bd39c48ef7b7779c88679f3b95faaedbc29d31dc6194d5676
robustness-v2.0.1 d63876e1f83c2b6bd39c48ef7b7779c88679f3b95faaedbc29d31dc6194d5676
EOF
python - <<'PY'
import json, os, platform
from pathlib import Path
root=Path(os.environ['RUNNER_TEMP'])/'fresh-offline'
reports=[]
for path in sorted(root.glob('*-restore.json')):
    r=json.loads(path.read_text('utf-8'))
    label=path.name.removesuffix('-restore.json')
    bundle=root/label/'bundle'
    assert r['status']=='PASS' and r['timestamp']=='VERIFIED'
    assert len(list(bundle.iterdir()))==11
    reports.append({'label':label,'status':r['status'],'restored_assets':11,'archive_sha256':r['archive_sha256']})
assert len(reports)==5
summary={'schema_version':1,'runner_os':os.environ.get('RUNNER_OS'),'runner_name':os.environ.get('RUNNER_NAME'),'platform':platform.platform(),'restore_network_proxy':'unreachable loopback','results':reports,'all_five_pass':True}
(root/'fresh-offline-summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print('PASS: five immutable release preservation archives restored and reverified on a fresh GitHub-hosted runner')
PY
