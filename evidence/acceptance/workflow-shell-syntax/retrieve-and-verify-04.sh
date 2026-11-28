set -euo pipefail
mkdir -p "$RUNNER_TEMP/opk/releases"
python - <<'PY'
import hashlib, json, os
from pathlib import Path
from urllib.request import Request, urlopen

expected=[
  ('paper-v1','Unjuno/openpreprint-kit-paper','v1','804cb76a4cf5eea65349fc7a8f01e2ce00e1176d','0860b735379fb1b9b223f5d535442dae8421f456d7ae1c6bf6ce8d3141a1b07c'),
  ('paper-v2','Unjuno/openpreprint-kit-paper','v2','6ec47ec58e9dc733956615343aad16caca4bb8ee','18e13ff3ccf37632cc86ede322687a32d2f959494672df52d78901cabe745805'),
  ('robustness-v1.0.0','Unjuno/openpreprint-kit-robustness-eval','v1.0.0','dedadf3b2e95090439ec10aa4298db72f048caab','92774a6552f0aaf9315baea6e9672677903a1bdb64288dfddf449cffb3de53a4'),
  ('robustness-v2.0.0','Unjuno/openpreprint-kit-robustness-eval','v2.0.0','5b98226d9b7847f08edb8674a89a7f9ae9f1d8e0','d63876e1f83c2b6bd39c48ef7b7779c88679f3b95faaedbc29d31dc6194d5676'),
  ('robustness-v2.0.1','Unjuno/openpreprint-kit-robustness-eval','v2.0.1','256e4743963a3ffb955b017bb3ecb1d91316e602','d63876e1f83c2b6bd39c48ef7b7779c88679f3b95faaedbc29d31dc6194d5676'),
]
root=Path(os.environ['RUNNER_TEMP'])/'opk'
records=[]
def get_json(url):
    req=Request(url,headers={'Accept':'application/vnd.github+json','User-Agent':'OpenPreprint-Kit-readonly-verifier'})
    with urlopen(req,timeout=30) as response:
        return json.load(response)
for label,repo,tag,source_sha,paper_sha in expected:
    release=get_json(f'https://api.github.com/repos/{repo}/releases/tags/{tag}')
    assert release['draft'] is False and release.get('immutable') is True, (repo,tag,'release state')
    ref=get_json(f'https://api.github.com/repos/{repo}/git/ref/tags/{tag}')
    obj=ref['object']
    if obj['type']=='tag':
        obj=get_json(f'https://api.github.com/repos/{repo}/git/tags/{obj["sha"]}')['object']
    assert obj['type']=='commit' and obj['sha']==source_sha, (repo,tag,obj)
    out=root/'releases'/label
    out.mkdir(parents=True,exist_ok=False)
    asset_records=[]
    for asset in release['assets']:
        name=asset['name']
        assert Path(name).name==name and asset.get('digest','').startswith('sha256:'), (repo,tag,name)
        # No Authorization header or token is attached to this public-asset request.
        req=Request(asset['browser_download_url'],headers={'User-Agent':'OpenPreprint-Kit-anonymous-asset-check'})
        with urlopen(req,timeout=60) as response:
            data=response.read()
        actual=hashlib.sha256(data).hexdigest()
        assert actual==asset['digest'].split(':',1)[1], (repo,tag,name,'digest mismatch')
        (out/name).write_bytes(data)
        asset_records.append({'name':name,'bytes':len(data),'expected_sha256':asset['digest'],'actual_sha256':'sha256:'+actual,'anonymous_download':True})
    assert len(asset_records)==11, (repo,tag,'expected 11 release assets',len(asset_records))
    assert next(a for a in asset_records if a['name']=='paper.pdf')['actual_sha256']=='sha256:'+paper_sha
    records.append({'label':label,'repository':repo,'tag':tag,'release_id':release['id'],'source_sha':source_sha,'immutable':True,'asset_count':len(asset_records),'assets':asset_records})
report={'schema_version':1,'runner_os':os.environ.get('RUNNER_OS'),'runner_name':os.environ.get('RUNNER_NAME'),
  'source_sha':os.environ.get('GITHUB_SHA'),'anonymous_asset_downloads':True,'authorization_header_sent':False,
  'releases':records,'all_asset_digests_match':True}
(root/'anonymous-release-readback.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print('PASS: anonymously fetched and SHA-256 checked 55 assets across five immutable Releases')
PY
