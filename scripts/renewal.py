#!/usr/bin/env python3
"""Forward RFC 3161 timestamp renewal for an already verified preservation ZIP.

This creates a separately publishable, append-only chain of *new* timestamps
on a statement binding exact old evidence and the previous renewal step. This
is NOT historical LTV, protection after a CA compromise, proof of authorship,
first-publication time, or durability of any storage provider.

All trust policies and the original ZIP and latest chain SHA-256 fingerprints
come from outside the evidence. Certificates and CRLs must validate NOW.
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
import urllib.error
import zipfile

from custody import source_details, valid_version
from preflight import validate_repository
from preserve import restore
from timestamp import LIMIT, load_policy, make_query_for_digest, post_query, verify_digest
from verify_release import sha256_file, unique_object

FORMAT = 'opk-forward-renewal-1'
PURPOSE = 'FORWARD_EXISTENCE_OF_ORIGINAL_ARCHIVE_AND_PREVIOUS_RENEWAL'
STEP_FILES = ('statement.json', 'timestamp.tsq', 'timestamp.tsr')
MAX_STEPS = 16
MAX_STATEMENT = 16384
MAX_PACKAGE = 64 * 1024 * 1024
HEX = re.compile(r'[0-9a-f]{64}\Z', re.ASCII)
STATEMENT_KEYS = {'schema_version', 'format', 'purpose', 'source_repository',
                  'source_version', 'source_archive_sha256', 'source_manifest_sha256',
                  'step_number', 'previous_step_sha256', 'renewal_ca_sha256',
                  'renewal_policy_oid', 'historical_ltv', 'public_availability'}


def _canonical(data: dict) -> bytes:
    return (json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def _regular_bytes(path: Path, maximum: int) -> bytes:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ValueError('missing, unsafe or oversized renewal member: ' + path.name)
    with path.open('rb') as f:
        data = f.read(maximum + 1)
    if not 0 < len(data) <= maximum:
        raise ValueError('missing, unsafe or oversized renewal member: ' + path.name)
    return data


def _step_bytes(step: Path) -> list[bytes]:
    if step.is_symlink() or not step.is_dir() or {p.name for p in step.iterdir()} != set(STEP_FILES):
        raise ValueError('unexpected or missing renewal step files')
    return [_regular_bytes(step / name, MAX_STATEMENT if name == 'statement.json' else LIMIT)
            for name in STEP_FILES]


def _hash_step_parts(items: list[bytes]) -> str:
    digest = hashlib.sha256(b'OPK-FORWARD-RENEWAL-STEP-v1\0')
    for item in items:
        digest.update(len(item).to_bytes(8, 'big'))
        digest.update(item)
    return digest.hexdigest()


def step_digest(step: Path) -> str:
    """Domain-separated hash over the three exact public renewal files."""
    return _hash_step_parts(_step_bytes(step))


def _steps(chain: Path) -> list[Path]:
    if chain.is_symlink() or not chain.is_dir():
        raise ValueError('renewal evidence must be a real directory')
    children = list(chain.iterdir())
    if not 1 <= len(children) <= MAX_STEPS:
        raise ValueError('renewal step count out of bounds')
    expected = {f'step-{i:04d}' for i in range(1, len(children) + 1)}
    if {p.name for p in children} != expected:
        raise ValueError('missing, unknown, or reordered renewal step')
    return [chain / f'step-{i:04d}' for i in range(1, len(children) + 1)]


def _source(archive: Path, archive_pin: str, policy: Path,
            repository: str, version: str) -> dict:
    validate_repository(repository)
    valid_version(version)
    if not isinstance(archive_pin, str) or not HEX.fullmatch(archive_pin):
        raise ValueError('independently pinned original archive SHA-256 is required')
    if archive.is_symlink() or not archive.is_file():
        raise ValueError('original preservation ZIP must be a regular file')
    with tempfile.TemporaryDirectory(prefix='opk-renew-source-') as tmp:
        restored = Path(tmp) / 'restored'
        try:
            report = restore(archive, restored, archive_pin, policy)
        except (zipfile.BadZipFile, EOFError) as exc:
            raise ValueError('source preservation ZIP is malformed') from None
        if report['timestamp'] != 'VERIFIED':
            raise ValueError('original source timestamp must verify under current trusted CRLs')
        details = source_details(restored, repository, version)
    return details


def verify_chain(archive: Path, archive_pin: str, source_policy: Path,
                 chain: Path, expected_chain_sha256: str, renewal_policies: list[Path],
                 repository: str, version: str) -> dict:
    """Verify the *entire* linked chain under separately supplied live trust policies."""
    if not isinstance(expected_chain_sha256, str) or not HEX.fullmatch(expected_chain_sha256):
        raise ValueError('out-of-band final renewal SHA-256 is mandatory')
    paths = _steps(chain)
    if not isinstance(renewal_policies, list) or len(renewal_policies) != len(paths):
        raise ValueError('one externally trusted policy per renewal step is mandatory')
    origin = _source(archive, archive_pin, source_policy, repository, version)
    previous = None
    policies = []
    signed_times = []
    for number, (step, path) in enumerate(zip(paths, renewal_policies), 1):
        statement_bytes, query, response = _step_bytes(step)
        statement = json.loads(statement_bytes.decode('utf-8'), object_pairs_hook=unique_object)
        policy = load_policy(path)
        if (not isinstance(statement, dict) or set(statement) != STATEMENT_KEYS
                or type(statement.get('schema_version')) is not int or statement['schema_version'] != 1
                or statement.get('format') != FORMAT or statement.get('purpose') != PURPOSE
                or statement.get('source_repository') != repository
                or statement.get('source_version') != version
                or statement.get('source_archive_sha256') != archive_pin
                or statement.get('source_manifest_sha256') != origin['manifest_sha256']
                or type(statement.get('step_number')) is not int or statement['step_number'] != number
                or statement.get('previous_step_sha256') != previous
                or statement.get('renewal_ca_sha256') != policy['ca_sha256']
                or statement.get('renewal_policy_oid') != policy['policy_oid']
                or statement.get('historical_ltv') != 'NOT_ESTABLISHED'
                or statement.get('public_availability') != 'NOT_PROVEN'
                or _canonical(statement) != statement_bytes):
            raise ValueError('renewal statement, identity, chain link or trust policy mismatch')
        signature_report = verify_digest(hashlib.sha256(statement_bytes).digest(), query, response, policy)
        if signature_report['status'] != 'VERIFIED':
            raise ValueError('renewal timestamp signature did not verify')
        signed_times.append(signature_report['tsa_time_utc'])
        policies.append(signature_report['policy_oid'])
        previous = _hash_step_parts([statement_bytes, query, response])
    if previous != expected_chain_sha256:
        raise ValueError('renewal chain does not match independently pinned terminal digest')
    return {'status': 'PASS', 'source_archive_sha256': archive_pin,
            'source_repository': repository, 'source_version': version,
            'chain_sha256': previous, 'steps': len(paths), 'tsa_policies': policies,
            'tsa_signed_times_utc': signed_times,
            'revocation': 'CURRENT_CRLS_REQUIRED_FOR_ORIGINAL_AND_ALL_RENEWALS',
            'historical_ltv': 'NOT_ESTABLISHED', 'independent_custody': 'NOT_PROVEN',
            'first_publication': 'NOT_PROVEN'}


def issue_chain(archive: Path, archive_pin: str, source_policy: Path,
                renewal_policy: Path, repository: str, version: str, output: Path,
                *, prior_chain: Path | None = None, prior_sha256: str | None = None,
                prior_policies: list[Path] | None = None, post=post_query) -> dict:
    """Atomically issue one more genuine timestamp; the source archive is never modified."""
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise ValueError('renewal destination already exists; never overwrite evidence')
    if output.parent.is_symlink() or not output.parent.is_dir():
        raise ValueError('renewal destination parent must exist and not be a symlink')
    if prior_chain is None and (prior_sha256 is not None or prior_policies):
        raise ValueError('prior SHA/policy supplied without prior chain')
    if prior_chain is not None and (
            not isinstance(prior_sha256, str) or not HEX.fullmatch(prior_sha256)
            or not isinstance(prior_policies, list) or not prior_policies):
        raise ValueError('prior renewal needs external terminal digest and explicit policies')
    origin = _source(archive, archive_pin, source_policy, repository, version)
    policy = load_policy(renewal_policy)
    with tempfile.TemporaryDirectory(prefix='.opk-forward-renew-', dir=output.parent) as tmp:
        stage = Path(tmp) / 'chain'
        stage.mkdir()
        previous = None
        number = 1
        if prior_chain is not None:
            old_steps = _steps(prior_chain)
            if len(old_steps) >= MAX_STEPS:
                raise ValueError('renewal chain step limit reached')
            for old in old_steps:
                copied = stage / old.name
                copied.mkdir()
                for name, data in zip(STEP_FILES, _step_bytes(old)):
                    (copied / name).write_bytes(data)
            prior = verify_chain(archive, archive_pin, source_policy, stage,
                                 prior_sha256, prior_policies, repository, version)
            previous = prior['chain_sha256']
            number = prior['steps'] + 1
        statement = {'schema_version': 1, 'format': FORMAT, 'purpose': PURPOSE,
                     'source_repository': repository, 'source_version': version,
                     'source_archive_sha256': archive_pin,
                     'source_manifest_sha256': origin['manifest_sha256'],
                     'step_number': number, 'previous_step_sha256': previous,
                     'renewal_ca_sha256': policy['ca_sha256'],
                     'renewal_policy_oid': policy['policy_oid'],
                     'historical_ltv': 'NOT_ESTABLISHED',
                     'public_availability': 'NOT_PROVEN'}
        data = _canonical(statement)
        if len(data) > MAX_STATEMENT:
            raise ValueError('renewal statement exceeds size bound')
        query = make_query_for_digest(hashlib.sha256(data).digest(), policy)
        response = post(policy['tsa_url'], query, policy['timeout_seconds'])
        if type(response) is not bytes or not 0 < len(response) <= LIMIT:
            raise ValueError('invalid or oversized TSA response')
        verify_digest(hashlib.sha256(data).digest(), query, response, policy)
        step = stage / f'step-{number:04d}'
        step.mkdir()
        for name, value in zip(STEP_FILES, (data, query, response)):
            (step / name).write_bytes(value)
        terminal = step_digest(step)
        # Never mark a half-written or cryptographically invalid sidecar as issued.
        policies = list(prior_policies or []) + [renewal_policy]
        verified = verify_chain(archive, archive_pin, source_policy,
                                stage, terminal, policies, repository, version)
        if output.exists() or output.is_symlink():
            raise ValueError('renewal destination appeared during timestamping')
        os.rename(stage, output)
    return {'status': 'PASS', 'archive_sha256': archive_pin,
            'chain_sha256': verified['chain_sha256'], 'steps': verified['steps'],
            'historical_ltv': 'NOT_ESTABLISHED',
            'independent_custody': 'NOT_PROVEN', 'first_publication': 'NOT_PROVEN'}



def pack_chain(archive: Path, archive_pin: str, source_policy: Path,
               chain: Path, chain_pin: str, renewal_policies: list[Path],
               repository: str, version: str, output: Path) -> dict:
    """Make a deterministic public-only ZIP suitable for a new GitHub Release."""
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise ValueError('renewal package already exists; never overwrite')
    if not output.parent.is_dir() or output.parent.is_symlink():
        raise ValueError('renewal package output parent must be an existing regular directory')
    if output.resolve().is_relative_to(chain.resolve()):
        raise ValueError('renewal ZIP must not be created inside its own chain')
    verified = verify_chain(archive, archive_pin, source_policy, chain,
                            chain_pin, renewal_policies, repository, version)
    with tempfile.TemporaryDirectory(prefix='.opk-forward-package-', dir=output.parent) as tmp:
        zipped = Path(tmp) / 'evidence.zip'
        with zipfile.ZipFile(zipped, 'w', compression=zipfile.ZIP_STORED) as z:
            for step in _steps(chain):
                for name, raw in zip(STEP_FILES, _step_bytes(step)):
                    item = zipfile.ZipInfo(step.name + '/' + name, (1980, 1, 1, 0, 0, 0))
                    item.create_system = 3
                    item.external_attr = 0o100644 << 16
                    z.writestr(item, raw, compress_type=zipfile.ZIP_STORED)
        if zipped.stat().st_size > MAX_PACKAGE:
            raise ValueError('renewal evidence ZIP exceeds size bound')
        package_sha = sha256_file(zipped)
        os.link(zipped, output)   # exclusive installation; never replace an existing file
    return {'status': 'PASS', 'package_sha256': package_sha,
            'chain_sha256': verified['chain_sha256'], 'steps': verified['steps'],
            'historical_ltv': 'NOT_ESTABLISHED', 'github_release': 'NOT_CREATED'}


def restore_chain(archive: Path, archive_pin: str, source_policy: Path,
                  package: Path, expected_package_sha256: str, chain_pin: str,
                  renewal_policies: list[Path], repository: str, version: str,
                  output: Path) -> dict:
    """Restore only bounded/allowlisted public evidence and reverify all signatures."""
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise ValueError('renewal restore destination already exists')
    if not output.parent.is_dir() or output.parent.is_symlink():
        raise ValueError('renewal restore destination parent must be an existing regular directory')
    if not isinstance(expected_package_sha256, str) or not HEX.fullmatch(expected_package_sha256):
        raise ValueError('out-of-band package SHA-256 required')
    if package.is_symlink() or not package.is_file() or not 0 < package.stat().st_size <= MAX_PACKAGE:
        raise ValueError('missing, unsafe or oversized renewal package')
    with package.open('rb') as source:
        h = hashlib.sha256()
        for block in iter(lambda: source.read(1024 * 1024), b''):
            h.update(block)
        if h.hexdigest() != expected_package_sha256:
            raise ValueError('renewal package digest differs from out-of-band pin')
        source.seek(0)
        with zipfile.ZipFile(source) as z:
            members = z.infolist()
            filenames = [x.filename for x in members]
            if not 3 <= len(members) <= 3 * MAX_STEPS or len(members) % 3 or len(set(filenames)) != len(filenames):
                raise ValueError('invalid, missing or repeated renewal package members')
            count = len(members) // 3
            expected = {f'step-{i:04d}/{name}' for i in range(1, count + 1) for name in STEP_FILES}
            if set(filenames) != expected:
                raise ValueError('unknown, missing or traversing renewal package member')
            aggregate = 0
            for member in members:
                mode = member.external_attr >> 16
                if (member.is_dir() or member.compress_type != zipfile.ZIP_STORED
                        or member.flag_bits & 1 or stat.S_IFMT(mode) not in (0, stat.S_IFREG)
                        or not 0 < member.file_size <=
                        (MAX_STATEMENT if member.filename.endswith('/statement.json') else LIMIT)
                        or member.file_size != member.compress_size):
                    raise ValueError('unsafe, linked, encrypted or compressed renewal member')
                aggregate += member.file_size
            if aggregate > MAX_PACKAGE:
                raise ValueError('renewal package uncompressed size exceeds bound')
            with tempfile.TemporaryDirectory(prefix='.opk-forward-unpack-', dir=output.parent) as tmp:
                stage = Path(tmp) / 'chain'; stage.mkdir()
                for member in members:
                    parent = stage / member.filename.split('/')[0]
                    parent.mkdir(exist_ok=True)
                    with z.open(member) as incoming, (stage / member.filename).open('xb') as destination:
                        shutil.copyfileobj(incoming, destination, 1024 * 1024)
                checked = verify_chain(archive, archive_pin, source_policy, stage,
                                       chain_pin, renewal_policies, repository, version)
                if output.exists() or output.is_symlink():
                    raise ValueError('renewal restore destination appeared during verification')
                os.rename(stage, output)
    return {'status': 'PASS', 'package_sha256': expected_package_sha256,
            'chain_sha256': checked['chain_sha256'], 'steps': checked['steps'],
            'historical_ltv': 'NOT_ESTABLISHED', 'github_release': 'NOT_CHECKED'}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation', choices=('issue', 'verify', 'pack', 'restore'))
    p.add_argument('archive', type=Path)
    p.add_argument('--expected-archive-sha256', required=True)
    p.add_argument('--source-policy', required=True, type=Path)
    p.add_argument('--repository', required=True)
    p.add_argument('--version', required=True)
    p.add_argument('--renewal-policy', required=True, action='append', type=Path)
    p.add_argument('--chain', type=Path)
    p.add_argument('--expected-chain-sha256')
    p.add_argument('--prior', type=Path)
    p.add_argument('--expected-prior-sha256')
    p.add_argument('--prior-policy', action='append', type=Path)
    p.add_argument('--out', type=Path)
    p.add_argument('--package', type=Path)
    p.add_argument('--expected-package-sha256')
    p.add_argument('--apply', action='store_true', help='explicit opt-in to new external TSA request')
    a = p.parse_args()
    try:
        validate_repository(a.repository)
        valid_version(a.version)
        if not HEX.fullmatch(a.expected_archive_sha256):
            raise ValueError('independent original archive pin required')
        if a.operation == 'issue':
            if not a.out or len(a.renewal_policy) != 1 or a.chain or a.expected_chain_sha256:
                raise ValueError('issue requires --out and one --renewal-policy; not --chain')
            if not a.apply:
                report = {'status': 'PLAN_ONLY', 'network': False, 'archive_unchanged': True,
                          'release_created': False, 'historical_ltv': 'NOT_ESTABLISHED'}
            else:
                report = issue_chain(a.archive, a.expected_archive_sha256,
                     a.source_policy, a.renewal_policy[0], a.repository, a.version,
                     a.out, prior_chain=a.prior, prior_sha256=a.expected_prior_sha256,
                     prior_policies=a.prior_policy)
        elif a.operation == 'verify':
            if not a.chain or not a.expected_chain_sha256 or a.apply or a.prior or a.out or a.package:
                raise ValueError('verify requires --chain and independent --expected-chain-sha256')
            report = verify_chain(a.archive, a.expected_archive_sha256,
                a.source_policy, a.chain, a.expected_chain_sha256, a.renewal_policy,
                a.repository, a.version)
        elif a.operation == 'pack':
            if not a.chain or not a.expected_chain_sha256 or not a.out or a.apply or a.package:
                raise ValueError('pack requires --chain, --expected-chain-sha256 and --out')
            report = pack_chain(a.archive, a.expected_archive_sha256,
                a.source_policy, a.chain, a.expected_chain_sha256, a.renewal_policy,
                a.repository, a.version, a.out)
        else:
            if not a.package or not a.expected_package_sha256 or not a.expected_chain_sha256 or not a.out or a.apply or a.chain:
                raise ValueError('restore requires --package, --expected-package-sha256, --expected-chain-sha256 and --out')
            report = restore_chain(a.archive, a.expected_archive_sha256,
                a.source_policy, a.package, a.expected_package_sha256,
                a.expected_chain_sha256, a.renewal_policy, a.repository, a.version, a.out)
        print(json.dumps(report, sort_keys=True, indent=2))
        return 0
    except (ValueError, OSError, TypeError, KeyError, UnicodeError, RuntimeError,
            urllib.error.URLError, zipfile.BadZipFile) as exc:
        print('FAIL: ' + str(exc), file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
