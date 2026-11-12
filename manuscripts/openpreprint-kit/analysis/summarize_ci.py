#!/usr/bin/env python3
"""Recompute paper results from a pinned, gzip-compressed GitHub CI log.

Only Python's standard library is needed. This checks a retained log, not
GitHub attestation, scholarly validity, author identity, or publication time.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys

TEST=re.compile(r'^test_[^\s]+ \((test_[^.\s]+)\.([^\)]+)\) \.\.\. ',re.M)
SUMMARY=re.compile(r'^Ran ([0-9]+) tests? in ([0-9.]+)s$',re.M)
MAX_LOG=4*1024*1024

def summarize(text: str) -> dict:
    if len(text.encode('utf-8'))>MAX_LOG:
        raise ValueError('log exceeds size limit')
    totals=SUMMARY.findall(text)
    if len(totals)!=1 or text.rstrip().splitlines()[-1]!='OK':
        raise ValueError('exactly one successful unskipped suite is required')
    if re.search(r'^FAILED\b|^FAIL:|^ERROR:|\.\.\. (?:FAIL|ERROR|skipped)',text,re.M):
        raise ValueError('failed or skipped test is present')
    matches=TEST.findall(text)
    if len(set(matches))!=len(matches):raise ValueError('duplicate test identity')
    total=int(totals[0][0])
    if total<=0 or total!=len(matches):raise ValueError('reported count differs from distinct test lines')
    python=re.search(r'^Python ([^\r\n]+)',text,re.M)
    openssl=re.search(r'^OpenSSL ([^\r\n]+)',text,re.M)
    return {'tests':total,'modules':dict(sorted(Counter(m for m,_ in matches).items())),
            'suite_status':'PASS','skipped':0,
            'python':python.group(1) if python else 'not recorded',
            'openssl':openssl.group(1) if openssl else 'not recorded',
            'runtime_is_benchmark':False}

def inspect_archive(data: Path) -> dict:
    meta=json.loads((data/'provenance.json').read_text('utf-8'))
    source=data/'baseline-ci.txt.gz'
    if source.is_symlink() or not source.is_file() or source.stat().st_size>MAX_LOG:
        raise ValueError('invalid evidence archive')
    raw=source.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=meta['compressed_log_sha256']:
        raise ValueError('compressed log hash mismatch')
    with gzip.open(source,'rb') as f:
        content=f.read(MAX_LOG+1)
    if len(content)>MAX_LOG or hashlib.sha256(content).hexdigest()!=meta['raw_log_sha256']:
        raise ValueError('raw log hash or size mismatch')
    result=summarize(content.decode('utf-8'))
    result['evaluated_commit']=meta['evaluated_commit']
    result['source_log_sha256']=meta['raw_log_sha256']
    result['source_log_url']=meta['ci_run_url']
    return result

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',type=Path,default=Path(__file__).resolve().parents[1]/'data')
    p.add_argument('--csv',type=Path,help='optional new CSV path; refuses overwrite')
    a=p.parse_args()
    try:
        result=inspect_archive(a.data)
        if a.csv:
            with a.csv.open('x',newline='',encoding='utf-8') as f:
                w=csv.writer(f,lineterminator='\n');w.writerow(['module','test_count']);w.writerows(result['modules'].items())
        print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2))
        return 0
    except (OSError,ValueError,KeyError,UnicodeError) as exc:
        print('FAIL: '+str(exc),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
