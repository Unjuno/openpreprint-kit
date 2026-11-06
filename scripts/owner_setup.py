#!/usr/bin/env python3
"""Configure GitHub safeguards with an owner's already authenticated gh CLI.

Default is read-only. --apply enables immutable releases; --template additionally
marks this repo as a reusable template. Never changes visibility, permissions,
branch protection, secrets, or publishes any release. No credential is printed.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from typing import Callable
from preflight import validate_repository

API = Callable[[str, str, dict | None], object]


def gh_api(method: str, path: str, payload: dict | None = None) -> object:
    args=['gh','api','--hostname','github.com','--method',method,path,
          '-H','Accept: application/vnd.github+json','-H','X-GitHub-Api-Version: 2026-03-10']
    if payload is not None: args+=['--input','-']
    result=subprocess.run(args,input=json.dumps(payload) if payload is not None else None,
                          capture_output=True,text=True,timeout=45,check=False)
    if result.returncode:
        # Do not log a potentially secret-bearing response or ambient credentials.
        raise ValueError('GitHub '+method+' failed; check gh authentication and repository Administration permissions')
    if len(result.stdout)>1024*1024: raise ValueError('GitHub response exceeds size bound')
    if not result.stdout.strip(): return None
    return json.loads(result.stdout)


def configure(repository: str, apply: bool, template: bool, api: API = gh_api) -> dict:
    validate_repository(repository)
    path='repos/'+repository
    repo=api('GET',path,None)
    if not isinstance(repo,dict) or str(repo.get('full_name','')).lower()!=repository.lower():
        raise ValueError('could not verify the canonical repository')
    if repo.get('private') is not False:
        raise ValueError('repository is not public; this tool will NEVER change visibility')
    if not isinstance(repo.get('permissions'),dict) or repo['permissions'].get('admin') is not True:
        raise ValueError('repository administration authority must be confirmed before configuration')
    if apply:
        api('PUT',path+'/immutable-releases',None)
        if template: api('PATCH',path,{'is_template':True})
    current=api('GET',path+'/immutable-releases',None)
    checked=api('GET',path,None)
    if not isinstance(current,dict) or type(current.get('enabled')) is not bool or not isinstance(checked,dict):
        raise ValueError('cannot confirm configuration after API calls')
    ready=current['enabled'] is True and (not template or checked.get('is_template') is True)
    if apply and not ready: raise ValueError('read-back did not confirm the requested settings; inspect partial changes')
    return {'status':'PASS' if ready else 'ACTION_REQUIRED','mode':'APPLY' if apply else 'READ_ONLY',
            'repository':repository,'immutable':current['enabled'],'template':checked.get('is_template'),
            'release_created':False,'secrets_configured':False}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repository',required=True); p.add_argument('--apply',action='store_true')
    p.add_argument('--template',action='store_true'); a=p.parse_args()
    try:
        result=configure(a.repository,a.apply,a.template)
        print(json.dumps(result,sort_keys=True,indent=2)); return 0 if result['status']=='PASS' else 2
    except (OSError,ValueError,TypeError,subprocess.TimeoutExpired) as exc:
        print('FAIL: '+str(exc),file=sys.stderr); return 1

if __name__=='__main__': raise SystemExit(main())
