#!/usr/bin/env python3
"""Portable evidence backup/restore, never an automatic trust-store importer.

Default: require timestamp validation under --policy supplied independently.
--integrity-only is an explicit reduced check, never reported as time verification.
No originals, secret HMAC keys or workspace files are accepted. Standard-library
integrity operations; timestamp verification additionally uses existing requirements.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile
import zipfile
from verify_release import EXPECTED_FILES, RESEARCH_FILES, EVIDENCE_FILES, unique_object, verify

MAX_ARCHIVE = 160 * 1024 * 1024
MAX_MEMBER = 128 * 1024 * 1024
BUNDLE_NAMES = EXPECTED_FILES | RESEARCH_FILES | EVIDENCE_FILES
TRUST_NAMES = {'trust/policy-snapshot.json', 'trust/ca.pem', 'trust/crl.pem'}
ALLOWED_NAMES = {'preservation.json'} | {'bundle/' + n for n in BUNDLE_NAMES} | TRUST_NAMES
HEX = re.compile(r'[0-9a-f]{64}\Z', re.ASCII)


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest() if hasattr(hashlib, 'file_digest') else _hash(stream)


def _hash(stream) -> str:
    h = hashlib.sha256()
    while block := stream.read(1024 * 1024): h.update(block)
    return h.hexdigest()


def regular(path: Path, limit: int) -> None:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError('expected bounded regular non-symlink file: ' + path.name)


def validate_bundle(bundle: Path, policy_path: Path | None, integrity_only: bool) -> dict:
    errors = verify(bundle, None)
    if errors: raise ValueError('; '.join(errors))
    if integrity_only:
        if policy_path is not None: raise ValueError('choose --policy OR --integrity-only')
        return {'timestamp': 'NOT_VERIFIED'}
    if policy_path is None: raise ValueError('an independently selected --policy is required; reduced mode requires --integrity-only')
    from timestamp import load_policy, read_regular, verify_proof
    report = verify_proof(bundle, read_regular(bundle/'timestamp.tsq'), read_regular(bundle/'timestamp.tsr'), load_policy(policy_path))
    return {'timestamp': 'VERIFIED', 'time_evidence': report}


def pack(bundle: Path, output: Path, policy_path: Path | None = None, integrity_only: bool = False) -> dict:
    if output.exists() or output.is_symlink(): raise ValueError('refusing to overwrite an existing preservation archive')
    if output.resolve().is_relative_to(bundle.resolve()): raise ValueError('archive must be outside the source bundle')
    if bundle.is_symlink() or not bundle.is_dir(): raise ValueError('bundle must be a real directory')
    names = {p.name for p in bundle.iterdir()}
    if not names <= BUNDLE_NAMES: raise ValueError('unexpected file in bundle; never archive a workspace or secret')
    for name in names: regular(bundle/name, MAX_MEMBER)
    if sum((bundle/n).stat().st_size for n in names) > MAX_ARCHIVE - 1024*1024:
        raise ValueError('bundle exceeds preservation limit')
    with tempfile.TemporaryDirectory(prefix='.opk-pack-', dir=output.absolute().parent) as temp:
        stage = Path(temp); copied = stage/'bundle'; copied.mkdir()
        for name in sorted(names): shutil.copyfile(bundle/name,copied/name)
        report = validate_bundle(copied,policy_path,integrity_only)
        if policy_path is not None:
            from timestamp import load_policy, POLICY_KEYS
            policy=load_policy(policy_path)
            for field, label in (('_ca_file','CERTIFICATE'),('_crl_file','X509 CRL')):
                data=policy[field]
                pattern=rb'(?:\s*-----BEGIN '+label.encode()+rb'-----[A-Za-z0-9+/=\r\n]+-----END '+label.encode()+rb'-----\s*)+'
                if re.fullmatch(pattern,data) is None: raise ValueError('trust snapshot must contain only public certificate/CRL PEM blocks')
            trust=stage/'trust'; trust.mkdir()
            (trust/'ca.pem').write_bytes(policy['_ca_file']); (trust/'crl.pem').write_bytes(policy['_crl_file'])
            snapshot={k:policy[k] for k in POLICY_KEYS}
            snapshot.update(ca_file='ca.pem',crl_file='crl.pem')
            (trust/'policy-snapshot.json').write_text(json.dumps(snapshot,sort_keys=True,indent=2)+'\n',encoding='utf-8')
        inventory={}
        for file in sorted(stage.rglob('*')):
            if file.is_file():
                regular(file,MAX_MEMBER)
                inventory[file.relative_to(stage).as_posix()]={'sha256':digest(file),'size_bytes':file.stat().st_size}
        info={'schema_version':1,'format':'opk-preservation-1','files':inventory,
              'manifest_sha256':digest(copied/'manifest.json'),
              'trust_rule':'bundled certificates are evidence copies, not automatically trusted',
              'private_originals_and_keys':'NOT_INCLUDED'}
        (stage/'preservation.json').write_text(json.dumps(info,sort_keys=True,indent=2)+'\n',encoding='utf-8')
        temporary=stage/'archive.zip'
        with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_STORED) as z:
            for name in sorted([*inventory,'preservation.json']):
                zi=zipfile.ZipInfo(name, date_time=(1980,1,1,0,0,0)); zi.create_system=3; zi.external_attr=(0o100644<<16)
                with (stage/name).open('rb') as src, z.open(zi,'w') as dest: shutil.copyfileobj(src,dest,1024*1024)
        regular(temporary,MAX_ARCHIVE)
        fingerprint=digest(temporary)
        # Same-filesystem hard link is an exclusive, atomic installation of the file.
        os.link(temporary,output)
    return {'status':'PASS','archive_sha256':fingerprint,'manifest_sha256':info['manifest_sha256'],
            'offsite_storage':'NOT_ASSERTED','authorship':'NOT_PROVEN',**report}


def restore(archive: Path, output: Path, expected_sha256: str, policy_path: Path | None = None, integrity_only: bool = False) -> dict:
    if not HEX.fullmatch(expected_sha256): raise ValueError('independently retained 64-digit lowercase archive SHA-256 required')
    if output.exists() or output.is_symlink(): raise ValueError('restore destination must not exist')
    regular(archive,MAX_ARCHIVE)
    # Hash and parse the same descriptor; do not reopen an untrusted path after hashing.
    with archive.open('rb') as stream:
        if _hash(stream) != expected_sha256: raise ValueError('archive does not match the independently retained SHA-256')
        stream.seek(0)
        with zipfile.ZipFile(stream) as z:
            members=z.infolist(); names=[m.filename for m in members]
            if len(members)>len(ALLOWED_NAMES) or len(set(names))!=len(names) or not set(names)<=ALLOWED_NAMES:
                raise ValueError('unexpected, duplicate, or unsafe archive member')
            if 'preservation.json' not in names: raise ValueError('preservation manifest missing')
            total=0
            for member in members:
                mode=member.external_attr>>16
                if (member.is_dir() or member.compress_type!=zipfile.ZIP_STORED or member.flag_bits&1
                        or stat.S_IFMT(mode) not in (0,stat.S_IFREG)
                        or not 0<=member.file_size<=MAX_MEMBER or member.compress_size!=member.file_size):
                    raise ValueError('compressed, encrypted, linked, or oversized archive member')
                total+=member.file_size
            if total>MAX_ARCHIVE: raise ValueError('archive exceeds aggregate size limit')
            if z.getinfo('preservation.json').file_size>65536: raise ValueError('oversized preservation manifest')
            info=json.loads(z.read('preservation.json'),object_pairs_hook=unique_object)
            if (not isinstance(info,dict) or type(info.get('schema_version')) is not int or info['schema_version']!=1
                    or info.get('format')!='opk-preservation-1' or not isinstance(info.get('files'),dict)
                    or set(info['files'])!=set(names)-{'preservation.json'}):
                raise ValueError('invalid preservation manifest')
            for name, entry in info['files'].items():
                if (not isinstance(entry,dict) or set(entry)!={'sha256','size_bytes'}
                        or not isinstance(entry['sha256'],str) or not HEX.fullmatch(entry['sha256'])
                        or type(entry['size_bytes']) is not int or entry['size_bytes']!=z.getinfo(name).file_size):
                    raise ValueError('invalid preservation file entry')
            with tempfile.TemporaryDirectory(prefix='.opk-restore-',dir=output.absolute().parent) as temp:
                target=Path(temp)/'result'; target.mkdir()
                for member in members:
                    file=target/member.filename; file.parent.mkdir(parents=True,exist_ok=True)
                    with z.open(member) as src, file.open('xb') as dest: shutil.copyfileobj(src,dest,1024*1024)
                    if member.filename!='preservation.json' and digest(file)!=info['files'][member.filename]['sha256']:
                        raise ValueError('preserved member checksum mismatch')
                if digest(target/'bundle'/'manifest.json')!=info.get('manifest_sha256'):
                    raise ValueError('preserved bundle identity mismatch')
                trust_names=set(names)&TRUST_NAMES
                if trust_names and trust_names!=TRUST_NAMES: raise ValueError('incomplete public trust snapshot')
                report=validate_bundle(target/'bundle',policy_path,integrity_only)
                if output.exists() or output.is_symlink(): raise ValueError('restore destination appeared during validation')
                os.rename(target,output)
    return {'status':'PASS','archive_sha256':expected_sha256,'manifest_sha256':info['manifest_sha256'],
            'bundled_trust':'NOT_AUTOMATICALLY_TRUSTED','authorship':'NOT_PROVEN',**report}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['pack','restore']); parser.add_argument('input',type=Path)
    parser.add_argument('--out',type=Path,required=True); parser.add_argument('--policy',type=Path)
    parser.add_argument('--expected-sha256'); parser.add_argument('--integrity-only',action='store_true')
    a=parser.parse_args()
    try:
        if a.operation=='pack': result=pack(a.input,a.out,a.policy,a.integrity_only)
        else:
            if a.expected_sha256 is None: raise ValueError('restore requires --expected-sha256 obtained separately')
            result=restore(a.input,a.out,a.expected_sha256,a.policy,a.integrity_only)
        print(json.dumps(result,sort_keys=True,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,zipfile.BadZipFile,RuntimeError) as exc:
        print('FAIL: '+str(exc),file=sys.stderr); return 1

if __name__=='__main__': raise SystemExit(main())
