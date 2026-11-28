set -euo pipefail
mkdir -p "$RUNNER_TEMP/opk/trust"
curl --proto '=https' --tlsv1.2 --fail --max-time 45 https://freetsa.org/files/cacert.pem -o "$RUNNER_TEMP/opk/trust/ca.pem"
echo '2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438' "$RUNNER_TEMP/opk/trust/ca.pem" | sha256sum -c -
curl --proto '=https' --tlsv1.2 --fail --max-time 45 https://www.freetsa.org/crl/root_ca.crl -o "$RUNNER_TEMP/opk/trust/crl.pem"
openssl crl -in "$RUNNER_TEMP/opk/trust/crl.pem" -noout -verify -CAfile "$RUNNER_TEMP/opk/trust/ca.pem"
openssl crl -in "$RUNNER_TEMP/opk/trust/crl.pem" -noout -lastupdate -nextupdate | tee "$RUNNER_TEMP/opk/trust/crl-validity.txt"
python - <<'PY'
import json, os
from pathlib import Path
root=Path(os.environ['RUNNER_TEMP'])/'opk'/'trust'
policy={'schema_version':1,'tsa_url':'https://freetsa.org/tsr',
  'ca_file':'ca.pem','ca_sha256':'2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438',
  'crl_file':'crl.pem','policy_oid':'1.2.3.4.1','timeout_seconds':45}
(root/'policy.json').write_text(json.dumps(policy,sort_keys=True)+'\n',encoding='utf-8')
PY
