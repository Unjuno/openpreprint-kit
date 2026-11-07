#!/usr/bin/env python3
"""Optional *independent* public-access witness, signed by an external operator.

Use on a machine managed separately from GitHub and the preprint author.
An Ed25519 signature authenticates the witness's assertion under an externally pinned
public key. It does NOT prove the first publication time, author identity, or honesty
of a compromised/malicious witness. RFC 3161 evidence is verified separately.

OpenSSL 3 is required. Never store the witness signing key in the repository.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

from preflight import validate_repository
from verify_release import EXPECTED_FILES, EVIDENCE_FILES, RESEARCH_FILES, sha256_file, unique_object, verify
from timestamp import (load_policy, make_query_for_digest, post_query, read_regular,
                       verify_digest, verify_proof)

VERSION_RE = re.compile(r'v(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*)){0,2}\Z', re.ASCII)
SHA_RE = re.compile(r'[0-9a-f]{64}\Z', re.ASCII)
BUNDLE_ALLOWED = EXPECTED_FILES | RESEARCH_FILES | EVIDENCE_FILES
LIMIT = 128 * 1024 * 1024
HOSTS = {'github.com', 'release-assets.githubusercontent.com', 'objects.githubusercontent.com'}
OBSERVATION_STAMP_FILES = {'observation.tsq', 'observation.tsr'}
OBSERVATION_FIELDS = {
    'schema_version', 'signature_algorithm', 'repository', 'version',
    'anonymous_https', 'observed_interval_start_utc', 'observed_interval_end_utc',
    'timestamp_verified', 'manifest_sha256', 'paper_sha256', 'files',
    'public_availability', 'first_publication', 'authorship', 'witness_clock',
}


def receipt_digest(data: bytes, signature: bytes) -> bytes:
    """Domain-separated SHA-256 of BOTH the signed observation and its Ed25519 signature.

    The RFC 3161 response is not included, avoiding circular evidence. Without
    the signature in this digest, a witness could sign the statement after it
    was time-stamped and misrepresent when the signature existed.
    """
    if (type(data) is not bytes or type(signature) is not bytes
            or not 0 < len(data) <= 65536 or not 0 < len(signature) <= 65536):
        raise ValueError('invalid bound observation or signature')
    envelope = (b'OpenPreprintKit-ObservationReceipt-v1\0' +
                len(data).to_bytes(8, 'big') + data +
                len(signature).to_bytes(8, 'big') + signature)
    return hashlib.sha256(envelope).digest()


def assert_source_identity(bundle: Path, repository: str, version: str) -> None:
    """The fetched paper must declare the GitHub repository and tag being observed."""
    metadata = json.loads(read_regular(bundle / 'preprint-metadata.json'),
                          object_pairs_hook=unique_object)
    if not isinstance(metadata, dict):
        raise ValueError('source identity mismatch: invalid paper metadata')
    source = metadata.get('source_claim')
    if (not isinstance(source, dict) or
            not isinstance(source.get('repository'), str) or
            source['repository'].lower() != repository.lower() or
            metadata.get('version') != version):
        raise ValueError('source identity mismatch: release does not declare requested repository/version')




def safe_https(url: str) -> bool:
    try:
        parts = urllib.parse.urlsplit(url)
        return (parts.scheme == 'https' and parts.hostname in HOSTS and parts.username is None
                and parts.password is None and not parts.fragment and parts.port in (None, 443))
    except ValueError:
        return False


class ControlledRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not safe_https(newurl):
            raise ValueError('a Release download attempted an untrusted redirect')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_asset(repository: str, version: str, name: str) -> bytes:
    if name not in BUNDLE_ALLOWED:
        raise ValueError('unknown release asset')
    path = f'https://github.com/{repository}/releases/download/{version}/{name}'
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), ControlledRedirect())
    req = urllib.request.Request(path, method='GET', headers={'User-Agent': 'OpenPreprint-Kit/independent-observer'})
    with opener.open(req, timeout=30) as response:
        if response.status != 200 or not safe_https(response.url):
            raise ValueError('asset not publicly retrievable over anonymous HTTPS')
        contents = response.read(LIMIT + 1)
    if len(contents) == 0 or len(contents) > LIMIT:
        raise ValueError('empty or oversized publicly downloaded asset')
    return contents


def sign(private_key: Path, source: Path, dest: Path) -> None:
    if private_key.is_symlink() or not private_key.is_file():
        raise ValueError('witness signing key is unavailable or a symlink')
    cmd=['openssl', 'pkeyutl', '-sign', '-inkey', str(private_key), '-rawin', '-in', str(source), '-out', str(dest)]
    result = subprocess.run(cmd, capture_output=True, timeout=30, check=False)
    if result.returncode:
        raise ValueError('external-witness signing failed; no observation published')


def verify_signature(public_key: Path, source: Path, signature: Path) -> None:
    if any(p.is_symlink() or not p.is_file() for p in (public_key, source, signature)):
        raise ValueError('signing evidence is unavailable or unsafe')
    cmd=['openssl', 'pkeyutl', '-verify', '-pubin', '-inkey', str(public_key),
         '-sigfile', str(signature), '-rawin', '-in', str(source)]
    result=subprocess.run(cmd, capture_output=True, timeout=30, check=False)
    if result.returncode: raise ValueError('external-witness Ed25519 signature does not verify')


def download_bundle(repository: str, version: str, root: Path, fetcher=None) -> dict:
    fetcher = fetcher or (lambda name: fetch_asset(repository,version,name))
    manifest_bytes = fetcher('manifest.json')
    if not isinstance(manifest_bytes, bytes) or len(manifest_bytes) > 1024*1024:
        raise ValueError('invalid or oversized Release manifest')
    manifest = json.loads(manifest_bytes, object_pairs_hook=unique_object)
    declared = manifest.get('files') if isinstance(manifest, dict) else None
    if not isinstance(declared, dict) or not declared:
        raise ValueError('manifest files not declared')
    names = set(declared)|{'manifest.json','SHA256SUMS'}|EVIDENCE_FILES
    if not names <= BUNDLE_ALLOWED:
        raise ValueError('Release declares unsafe or unknown files')
    root.mkdir()
    for name in sorted(names):
        try:
            data = manifest_bytes if name=='manifest.json' else fetcher(name)
        except (KeyError, FileNotFoundError) as exc:
            raise ValueError('required public release asset is missing: ' + name) from exc
        if not isinstance(data, bytes) or not 0 < len(data) <= LIMIT:
            raise ValueError('invalid file response: ' + name)
        (root/name).write_bytes(data)
    failures=verify(root,None)
    if failures: raise ValueError('publicly downloaded release is inconsistent: '+'; '.join(failures))
    return manifest


def record_public(repository: str, version: str, output: Path, policy_path: Path,
                  private_key: Path, fetcher=None, *, stamp_observation: bool = False,
                  tsa_exchange=None) -> dict:
    validate_repository(repository)
    if not VERSION_RE.fullmatch(version) or not any(int(n) for n in version[1:].split('.')):
        raise ValueError('invalid release version for witness')
    if output.exists() or output.is_symlink():
        raise ValueError('witness evidence destination already exists')
    if private_key.resolve().is_relative_to(output.resolve()):
        raise ValueError('private witness key must remain outside witness artifacts')
    policy=load_policy(policy_path)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.opk-witness-',dir=output.parent) as temporary:
        base=Path(temporary); stage=base/'observation'; stage.mkdir()
        started=datetime.now(timezone.utc)
        bundle=stage/'bundle'
        download_bundle(repository,version,bundle,fetcher)
        assert_source_identity(bundle, repository, version)
        timestamp=verify_proof(bundle,read_regular(bundle/'timestamp.tsq'),read_regular(bundle/'timestamp.tsr'),policy)
        completed=datetime.now(timezone.utc)
        files={p.name:{'sha256':sha256_file(p),'size_bytes':p.stat().st_size} for p in sorted(bundle.iterdir())}
        evidence={'schema_version':1,'signature_algorithm':'Ed25519',
                  'repository':repository,'version':version,'anonymous_https':True,
                  'observed_interval_start_utc':started.isoformat(),
                  'observed_interval_end_utc':completed.isoformat(),
                  'timestamp_verified':True,'manifest_sha256':files['manifest.json']['sha256'],
                  'paper_sha256':files['paper.pdf']['sha256'],'files':files,
                  'public_availability':'WITNESS_ASSERTS_ANONYMOUS_RETRIEVAL',
                  'first_publication':'NOT_PROVEN','authorship':'NOT_PROVEN',
                  'witness_clock':'SELF_REPORTED_NOT_A_TRUSTED_TIMESTAMP'}
        (stage/'observation.json').write_text(json.dumps(evidence,sort_keys=True,indent=2)+'\n',encoding='utf-8')
        sign(private_key,stage/'observation.json',stage/'observation.sig')
        witness_timestamp = None
        if stamp_observation:
            bound_digest = receipt_digest(read_regular(stage/'observation.json', 65536),
                                          read_regular(stage/'observation.sig', 65536))
            query = make_query_for_digest(bound_digest, policy)
            response = (tsa_exchange(query) if tsa_exchange is not None else
                        post_query(policy['tsa_url'], query, policy['timeout_seconds']))
            if not isinstance(response, bytes):
                raise ValueError('TSA response must be bytes')
            witness_timestamp = verify_digest(bound_digest, query, response, policy)
            (stage/'observation.tsq').write_bytes(query)
            (stage/'observation.tsr').write_bytes(response)
        os.rename(stage,output)
    return {'status':'PASS','timestamp_verified':True,'repository':repository,'version':version,
            'signature':'SIGNED_BY_WITNESS','public_observation':'WITNESS_CLAIM_NOT_FIRST_PUBLICATION_PROOF',
            'observation_timestamp': 'VERIFIED' if witness_timestamp else 'NOT_PRESENT',
            'observation_tsa_time_utc': witness_timestamp['tsa_time_utc'] if witness_timestamp else None}


def verify_public(root: Path, public_key: Path, expected_pubkey_sha256: str,
                  policy_path: Path, *, require_observation_timestamp: bool = False,
                  expected_repository: str | None = None,
                  expected_version: str | None = None) -> dict:
    if root.is_symlink() or not root.is_dir(): raise ValueError('witness evidence must be a directory')
    if not isinstance(expected_pubkey_sha256,str) or not SHA_RE.fullmatch(expected_pubkey_sha256):
        raise ValueError('externally pinned observer public-key SHA-256 is mandatory')
    if public_key.is_symlink() or not public_key.is_file(): raise ValueError('invalid external observer key')
    if sha256_file(public_key) != expected_pubkey_sha256: raise ValueError('observer public-key pin mismatch')
    actual_members = {p.name for p in root.iterdir()}
    plain_members = {'bundle', 'observation.json', 'observation.sig'}
    stamped = actual_members == (plain_members | OBSERVATION_STAMP_FILES)
    if actual_members != plain_members and not stamped:
        raise ValueError('unexpected or partial external-witness timestamp evidence')
    if require_observation_timestamp and not stamped:
        raise ValueError('observation timestamp is required by verification policy')
    for name in ('observation.json','observation.sig'):
        path=root/name
        if path.is_symlink() or not path.is_file() or path.stat().st_size>65536:
            raise ValueError('invalid external-witness evidence member')
    signed = json.loads((root/'observation.json').read_text(encoding='utf-8'),object_pairs_hook=unique_object)
    if (not isinstance(signed, dict) or set(signed) != OBSERVATION_FIELDS or
            type(signed.get('schema_version')) is not int or signed['schema_version'] != 1 or
            signed.get('signature_algorithm') != 'Ed25519'):
        raise ValueError('unsupported external-witness observation schema')
    verify_signature(public_key,root/'observation.json',root/'observation.sig')
    repository=signed.get('repository'); version=signed.get('version')
    validate_repository(repository)
    if not isinstance(version,str) or not VERSION_RE.fullmatch(version): raise ValueError('invalid signed release version')
    if (expected_repository is not None and (not isinstance(expected_repository, str) or
            repository.lower() != expected_repository.lower())):
        raise ValueError('witness observation identity mismatch: repository')
    if expected_version is not None and version != expected_version:
        raise ValueError('witness observation identity mismatch: release version')
    # Verify the semantics of the signed claim, not merely its Ed25519
    # signature. A signer must not silently upgrade retrieval into a
    # trusted-clock, first-publication or independent availability proof.
    expected_claims = {
        'anonymous_https': True,
        'timestamp_verified': True,
        'public_availability': 'WITNESS_ASSERTS_ANONYMOUS_RETRIEVAL',
        'first_publication': 'NOT_PROVEN',
        'authorship': 'NOT_PROVEN',
        'witness_clock': 'SELF_REPORTED_NOT_A_TRUSTED_TIMESTAMP',
    }
    if any(type(signed.get(key)) is not type(value) or signed.get(key) != value
           for key, value in expected_claims.items()):
        raise ValueError('witness statement overstates proof')
    times=[]
    for name in ('observed_interval_start_utc','observed_interval_end_utc'):
        val=signed.get(name)
        if not isinstance(val,str): raise ValueError('signed observed time is absent')
        when=datetime.fromisoformat(val)
        if when.tzinfo is None or when.utcoffset()!=timedelta(0):
            raise ValueError('witness time must be timezone-aware UTC')
        times.append(when)
    if times[0]>times[1] or times[1]>datetime.now(timezone.utc)+timedelta(minutes=5):
        raise ValueError('nonsensical witness retrieval interval')
    bundle=root/'bundle'
    failures=verify(bundle,None)
    if failures: raise ValueError('witness bundle integrity failed: '+'; '.join(failures))
    assert_source_identity(bundle, repository, version)
    actual={p.name:{'sha256':sha256_file(p),'size_bytes':p.stat().st_size} for p in bundle.iterdir()}
    if actual != signed.get('files') or signed.get('manifest_sha256')!=actual['manifest.json']['sha256'] or signed.get('paper_sha256')!=actual['paper.pdf']['sha256']:
        raise ValueError('witness assertion does not match fetched content')
    policy=load_policy(policy_path)
    timestamp=verify_proof(bundle,read_regular(bundle/'timestamp.tsq'),read_regular(bundle/'timestamp.tsr'),policy)
    if timestamp['manifest_sha256']!=signed['manifest_sha256']:
        raise ValueError('timestamp of another version was substituted')
    witness_time = None
    if stamped:
        bound_digest = receipt_digest(read_regular(root/'observation.json', 65536),
                                      read_regular(root/'observation.sig', 65536))
        witness_time = verify_digest(bound_digest,
                                     read_regular(root/'observation.tsq'),
                                     read_regular(root/'observation.tsr'), policy)
    return {'status':'PASS','signature':'VERIFIED','timestamp':'VERIFIED',
            'repository':repository,'version':version,
            'public_observation':'WITNESS_CLAIM_NOT_FIRST_PUBLICATION_PROOF',
            'observed_interval_start_utc':times[0].isoformat(),
            'observed_interval_end_utc':times[1].isoformat(),
            'observer_key_sha256':expected_pubkey_sha256,
            'observation_timestamp': 'VERIFIED' if witness_time else 'NOT_PRESENT',
            'observation_tsa_time_utc': witness_time['tsa_time_utc'] if witness_time else None,
            'observation_accuracy_microseconds': witness_time['accuracy_microseconds'] if witness_time else None}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation',choices=('record','verify'))
    p.add_argument('--repository'); p.add_argument('--version'); p.add_argument('--out',type=Path)
    p.add_argument('--observation',type=Path); p.add_argument('--signing-key',type=Path)
    p.add_argument('--public-key',type=Path); p.add_argument('--expected-public-key-sha256')
    p.add_argument('--expected-repository', help='expected GitHub OWNER/REPO (required for verify CLI)')
    p.add_argument('--expected-version', help='expected GitHub release tag (required for verify CLI)')
    p.add_argument('--timestamp-observation',action='store_true',help='also timestamp signed witness statement using selected TSA')
    p.add_argument('--require-observation-timestamp',action='store_true',help='reject legacy untimestamped witness statements')
    p.add_argument('--policy',type=Path,required=True)
    a=p.parse_args()
    try:
        if a.operation=='record':
            if not a.repository or not a.version or not a.out or not a.signing_key:
                raise ValueError('record requires --repository, --version, --out and --signing-key')
            result=record_public(a.repository,a.version,a.out,a.policy,a.signing_key,
                                 stamp_observation=a.timestamp_observation)
        else:
            if not a.observation or not a.public_key or not a.expected_public_key_sha256:
                raise ValueError('verify requires --observation, --public-key and --expected-public-key-sha256')
            if not a.expected_repository or not a.expected_version:
                raise ValueError('verify requires --expected-repository and --expected-version to prevent evidence substitution')
            result=verify_public(a.observation,a.public_key,a.expected_public_key_sha256,a.policy,
                                 require_observation_timestamp=a.require_observation_timestamp,
                                 expected_repository=a.expected_repository,
                                 expected_version=a.expected_version)
        print(json.dumps(result,sort_keys=True,indent=2)); return 0
    except (OSError,ValueError,KeyError,TypeError,subprocess.TimeoutExpired,urllib.error.URLError) as exc:
        print('FAIL: '+str(exc),file=sys.stderr); return 1

if __name__=='__main__': raise SystemExit(main())
