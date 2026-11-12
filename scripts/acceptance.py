#!/usr/bin/env python3
"""Synthetic end-to-end acceptance. Never reads a user's paper or patient record.

fixture: offline paper + data + analysis + private commitment; no secret export.
live: explicitly contact the TSA in --policy for two synthetic versions, validate,
      preserve/restore, and verify tamper rejection. Does NOT create a GitHub Release.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]


def run(script: Path, *args: object, expected: int = 0) -> str:
    result=subprocess.run([sys.executable,str(script),*map(str,args)],capture_output=True,text=True,timeout=120)
    if result.returncode!=expected:
        raise ValueError(script.name+' failed: '+result.stderr[-2000:])
    return result.stdout


def fixture(output: Path, version: str, *, export_source: bool = False) -> dict:
    if version not in ('v1','v2'): raise ValueError('synthetic acceptance supports only v1 and v2')
    if output.exists() or output.is_symlink(): raise ValueError('fixture output must not exist')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='opk-synthetic-') as tmp:
        work=Path(tmp); repo=work/'synthetic-repository'; repo.mkdir()
        shutil.copytree(ROOT/'scripts',repo/'scripts',ignore=shutil.ignore_patterns('__pycache__'))
        for area in ('paper','data','analysis','reviews'): (repo/area).mkdir()
        from pypdf import PdfWriter
        from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
        writer=PdfWriter(); page=writer.add_blank_page(width=595,height=842)
        font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
        content=DecodedStreamObject()
        lines=['OPENPREPRINT KIT - SYNTHETIC ACCEPTANCE '+version,
               'TEST FIXTURE ONLY. NOT A SCIENTIFIC PAPER.',
               'Dataset: data/synthetic.csv. Code: analysis/reproduce.py.',
               'No real participants, patients, clinical observations or claims.',
               'Private fixture originals and keys never leave temporary storage.']
        commands=['BT /F1 12 Tf 45 770 Td']
        for i,line in enumerate(lines):
            if i: commands.append('0 -25 Td')
            commands.append('('+line+') Tj')
        commands.append('ET'); content.set_data(('\n'.join(commands)).encode('ascii'))
        page[NameObject('/Contents')]=writer._add_object(content)
        writer.add_metadata({'/Title':'SYNTHETIC - NOT RESEARCH','/Author':'OpenPreprint Kit test fixture'})
        with (repo/'paper'/'paper.pdf').open('wb') as f: writer.write(f)
        import yaml
        metadata={'schema_version':1,'title':'SYNTHETIC acceptance fixture '+version+' - not research',
                  'authors':[{'name':'OpenPreprint Kit synthetic test fixture'}],
                  'abstract':'Synthetic test bytes only. No human research or clinical data.',
                  'keywords':['synthetic','acceptance-test'],'version':version,'paper':'paper/paper.pdf','license':'CC0-1.0'}
        (repo/'preprint.yaml').write_text(yaml.safe_dump(metadata),encoding='utf-8')
        (repo/'data'/'synthetic.csv').write_text('x,y\n1,2\n2,4\n' + ('3,6\n' if version=='v2' else ''),encoding='utf-8')
        (repo/'analysis'/'reproduce.py').write_text('"""Synthetic demonstration only."""\nimport csv\nfrom pathlib import Path\np = Path(__file__).resolve().parents[1] / "data/synthetic.csv"\nwith p.open() as f:\n    assert all(int(r["y"]) == 2 * int(r["x"]) for r in csv.DictReader(f))\nprint("SYNTHETIC CHECK PASS")\n',encoding='utf-8')
        research={'schema_version':1,'public_assets':[
            {'path':'data/synthetic.csv','role':'dataset','description':'Synthetic integer pairs; no health data','license':'CC0-1.0','public_confirmed':True},
            {'path':'analysis/reproduce.py','role':'analysis_code','description':'Checks synthetic y=2x pairs','license':'MIT','public_confirmed':True}],
            'relations':[{'source':'analysis/reproduce.py','target':'data/synthetic.csv','kind':'analyzes'}]}
        (repo/'research-assets.yaml').write_text(yaml.safe_dump(research),encoding='utf-8')
        (repo/'reviews'/'record.json').write_text('{"schema_version":1,"events":[]}\n',encoding='utf-8')
        private=work/'private'; private.mkdir(mode=0o700)
        original=private/'synthetic-record.json'; original.write_bytes(b'{"type":"NO_PATIENT_PRIVATE_FIXTURE","value":123}\n')
        key=private/'per-record.key'
        run(repo/'scripts'/'private_seal.py','seal',original,'--key-output',key)
        receipt=next((repo/'evidence'/'commitments').glob('*.json'))
        run(repo/'scripts'/'private_seal.py','verify',original,'--key',key,'--receipt',receipt)
        original.write_bytes(b'changed synthetic record')
        run(repo/'scripts'/'private_seal.py','verify',original,'--key',key,'--receipt',receipt,expected=1)
        bundle=work/'bundle'
        run(repo/'scripts'/'prepare_release.py','--output',bundle)
        run(ROOT/'scripts'/'verify_release.py',bundle)
        tar=(bundle/'research-assets.tar').read_bytes()
        if b'NO_PATIENT_PRIVATE_FIXTURE' in tar or key.read_bytes() in tar: raise ValueError('private fixture leaked into public archive')
        run(repo/'analysis'/'reproduce.py')
        from build_site import build_site
        site=work/'site'; build_site(bundle,repo,site,'example/synthetic-acceptance')
        report={'schema_version':1,'version':version,'synthetic_only':True,
                'private_match':'PASS','private_tamper_rejected':'PASS','private_export':'NONE',
                'analysis_reproduction':'PASS','manifest_sha256':hashlib.sha256((bundle/'manifest.json').read_bytes()).hexdigest(),
                'timestamp':'NOT_YET_REQUESTED','github_release':'NOT_CREATED'}
        # All exports are allowlisted; temporary source/private directories are destroyed.
        output.mkdir()
        shutil.copytree(bundle,output/'bundle'); shutil.copytree(site,output/'site')
        if export_source:
            public_paths = ['preprint.yaml', 'research-assets.yaml', 'paper/paper.pdf',
                            'data/synthetic.csv', 'analysis/reproduce.py', str(receipt.relative_to(repo))]
            for relative in public_paths:
                destination = output / 'source' / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(repo / relative, destination)
            report['source_export'] = 'ALLOWLISTED_SYNTHETIC_ONLY'
            report['source_files'] = sorted(public_paths)
        (output/'fixture-report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    return report


def live(output: Path, policy_path: Path) -> dict:
    if output.exists() or output.is_symlink(): raise ValueError('live output must not exist')
    from timestamp import load_policy
    policy=load_policy(policy_path)
    output.mkdir(parents=True)
    # Public material ONLY. This is a snapshot; a verifier must choose trust separately.
    trust=output/'trust'; trust.mkdir()
    (trust/'ca.pem').write_bytes(policy['_ca_file']); (trust/'crl.pem').write_bytes(policy['_crl_file'])
    from timestamp import POLICY_KEYS
    snapshot={k:policy[k] for k in POLICY_KEYS}; snapshot.update(ca_file='ca.pem',crl_file='crl.pem')
    (trust/'policy-snapshot.json').write_text(json.dumps(snapshot,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    reports=[]; v1_before=None
    for version in ('v1','v2'):
        fixture(output/version,version)
        bundle=output/version/'bundle'
        run(ROOT/'scripts'/'citation_validation.py',bundle)
        stamped=json.loads(run(ROOT/'scripts'/'timestamp.py','stamp',bundle,'--policy',policy_path))
        verified=json.loads(run(ROOT/'scripts'/'timestamp.py','verify',bundle,'--policy',policy_path))
        if stamped['manifest_sha256']!=verified['manifest_sha256']: raise ValueError('stamp/verify identity changed')
        archive=output/(version+'.opk.zip')
        packed=json.loads(run(ROOT/'scripts'/'preserve.py','pack',bundle,'--out',archive,'--policy',policy_path))
        restored=json.loads(run(ROOT/'scripts'/'preserve.py','restore',archive,'--out',output/(version+'-restored'),
                                '--expected-sha256',packed['archive_sha256'],'--policy',policy_path))
        if restored['timestamp']!='VERIFIED': raise ValueError('restored timestamp not verified')
        original={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in bundle.iterdir()}
        recovered={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (output/(version+'-restored')/'bundle').iterdir()}
        if original!=recovered: raise ValueError('restored bytes differ')
        with tempfile.TemporaryDirectory(prefix='opk-tamper-') as bad:
            target=Path(bad)/'bundle'; shutil.copytree(bundle,target)
            with (target/'paper.pdf').open('ab') as f: f.write(b'TAMPERED')
            run(ROOT/'scripts'/'timestamp.py','verify',target,'--policy',policy_path,expected=1)
        reports.append({'version':version,'timestamp':verified,'archive_sha256':packed['archive_sha256'],
                        'restore_byte_equality':'PASS','tamper_rejected':'PASS'})
        if version=='v1': v1_before=original; time.sleep(1.1)
    v1_after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (output/'v1'/'bundle').iterdir()}
    if v1_before!=v1_after: raise ValueError('v2 preparation changed v1')
    report={'schema_version':1,'status':'PASS','synthetic_only':True,'source_commit':os.environ.get('GITHUB_SHA'),
            'python':sys.version.split()[0],'versions':reports,'v1_preserved_after_v2':'PASS',
            'tsa_trust':'explicit CA PEM pin; not an independent audit of TSA operations',
            'github_release':'NOT_CREATED','public_availability':'NOT_PROVEN','human_review':'NOT_PERFORMED'}
    (output/'acceptance-report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    return report


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation',choices=['fixture','live']); p.add_argument('--out',required=True,type=Path)
    p.add_argument('--version',default='v1',choices=['v1','v2']); p.add_argument('--policy',type=Path)
    p.add_argument('--export-source', action='store_true', help='fixture only: export allowlisted synthetic source; never original/private key')
    a=p.parse_args()
    try:
        if a.operation=='fixture': report=fixture(a.out,a.version,export_source=a.export_source)
        else:
            if a.export_source: raise ValueError('--export-source is only valid with fixture')
            if a.policy is None: raise ValueError('live acceptance requires --policy')
            report=live(a.out,a.policy)
        print(json.dumps(report,sort_keys=True,indent=2)); return 0
    except (OSError,ValueError,TypeError,subprocess.TimeoutExpired) as exc:
        print('FAIL: '+str(exc),file=sys.stderr); return 1

if __name__=='__main__': raise SystemExit(main())
