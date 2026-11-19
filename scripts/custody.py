#!/usr/bin/env python3
"""Offline, externally pinned custody of versioned OpenPreprint evidence ZIPs.

This command is not a storage provider, signing authority, historical LTV
service, witness, or an attestation of the archive operator's independence.
A PASS means the specified local files passed integrity and currently trusted
RFC 3161 checks at this run's verification time.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import zipfile

from observation import VERSION_RE, assert_source_identity
from preflight import validate_repository
from preserve import MAX_ARCHIVE, restore
from verify_release import sha256_file, unique_object

CATALOG_NAME = 'custody.json'
FORMAT = 'opk-custody-1'
MAX_ITEMS = 32
MAX_CATALOG = 65536
HEX = re.compile(r'[0-9a-f]{64}\Z', re.ASCII)


def valid_version(version: str) -> None:
    if (not isinstance(version, str) or not VERSION_RE.fullmatch(version)
            or not any(int(component) for component in version[1:].split('.'))):
        raise ValueError('version must be a non-draft published tag, e.g. v1 or v1.2')


def check_archive_file(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError('archive must be an existing non-symlink file')
    length = path.stat().st_size
    if not 0 < length <= MAX_ARCHIVE:
        raise ValueError('archive size must be positive and bounded')


def source_details(restored: Path, repository: str, version: str) -> dict:
    bundle = restored / 'bundle'
    assert_source_identity(bundle, repository, version)
    metadata = json.loads((bundle / 'preprint-metadata.json').read_text(encoding='utf-8'),
                          object_pairs_hook=unique_object)
    if not isinstance(metadata, dict) or not isinstance(metadata.get('source_claim'), dict):
        raise ValueError('source identity mismatch: missing source claim')
    source_commit = metadata['source_claim'].get('commit')
    if (not isinstance(source_commit, str) or
            re.fullmatch(r'[0-9a-fA-F]{40}\Z', source_commit, re.ASCII) is None):
        raise ValueError('source identity mismatch: Git commit ID missing')
    manifest_sha256 = sha256_file(bundle / 'manifest.json')
    paper_sha256 = sha256_file(bundle / 'paper.pdf')
    return {'version': version, 'filename': version + '.opk.zip',
            'manifest_sha256': manifest_sha256, 'paper_sha256': paper_sha256,
            'source_commit': source_commit.lower()}


def deposit(repository: str, entries: list[tuple[str, Path, str]],
            output: Path, policy: Path) -> dict:
    """Copy only explicit pinned ZIPs, validate and install an atomic store."""
    validate_repository(repository)
    if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_ITEMS:
        raise ValueError('deposit requires between 1 and 32 versioned archives')
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise ValueError('custody destination already exists; never overwrite')
    if output.parent.is_symlink() or not output.parent.is_dir():
        raise ValueError('custody destination parent must be an existing regular directory')
    versions: set[str] = set()
    for version, source, expected_sha in entries:
        valid_version(version)
        if version in versions:
            raise ValueError('duplicate version in custody deposit')
        versions.add(version)
        if not isinstance(expected_sha, str) or HEX.fullmatch(expected_sha) is None:
            raise ValueError('an out-of-band lowercase archive SHA-256 is required')
        check_archive_file(source)

    # Never let an input file live inside the output location. Later auditing
    # likewise takes its policy and catalog digest from the operator, not here.
    for _, source, _ in entries:
        if source.resolve().is_relative_to(output):
            raise ValueError('custody input and destination must be independent')

    with tempfile.TemporaryDirectory(prefix='.opk-custody-stage-', dir=output.parent) as temp:
        stage = Path(temp) / 'store'
        stage.mkdir()
        catalog_entries = []
        for version, source, expected_sha in sorted(entries, key=lambda row: row[0]):
            destination = stage / (version + '.opk.zip')
            with source.open('rb') as infile, destination.open('xb') as outfile:
                shutil.copyfileobj(infile, outfile, 1024 * 1024)
            check_archive_file(destination)
            if sha256_file(destination) != expected_sha:
                raise ValueError('archive SHA-256 mismatch with out-of-band pin: ' + version)
            with tempfile.TemporaryDirectory(prefix='.opk-custody-check-', dir=output.parent) as check:
                restored = Path(check) / 'restored'
                report = restore(destination, restored, expected_sha, policy)
                if report.get('timestamp') != 'VERIFIED':
                    raise ValueError('trusted RFC 3161 timestamp verification required')
                details = source_details(restored, repository, version)
                details.update(archive_sha256=expected_sha, size_bytes=destination.stat().st_size)
                catalog_entries.append(details)

        catalog = {
            'schema_version': 1,
            'format': FORMAT,
            'repository': repository,
            'entries': catalog_entries,
            'trust_rule': 'CATALOG_SHA256_AND_TSA_POLICY_MUST_BE_PINNED_OUT_OF_BAND',
            'offsite_custody': 'NOT_ATTESTED',
        }
        catalog_bytes = (json.dumps(catalog, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
        if len(catalog_bytes) > MAX_CATALOG:
            raise ValueError('custody catalog exceeds size bound')
        (stage / CATALOG_NAME).write_bytes(catalog_bytes)
        if output.exists() or output.is_symlink():
            raise ValueError('custody destination appeared during verification')
        os.rename(stage, output)
    return {'status': 'PASS', 'repository': repository, 'archive_count': len(catalog_entries),
            'catalog_sha256': hashlib.sha256(catalog_bytes).hexdigest(),
            'timestamp': 'VERIFIED_USING_CURRENT_POLICY',
            'offsite_custody': 'NOT_ATTESTED', 'durability': 'NOT_PROVEN',
            'first_publication': 'NOT_PROVEN', 'authorship': 'NOT_PROVEN'}


def audit(repository: str, storage: Path, catalog_hash: str, policy: Path) -> dict:
    """Read-only verification; never trust the catalog's own digest or CA."""
    validate_repository(repository)
    if not isinstance(catalog_hash, str) or HEX.fullmatch(catalog_hash) is None:
        raise ValueError('independently pinned catalog SHA-256 is mandatory')
    if storage.is_symlink() or not storage.is_dir():
        raise ValueError('custody store must be a real non-symlink directory')
    catalog_file = storage / CATALOG_NAME
    if catalog_file.is_symlink() or not catalog_file.is_file() or catalog_file.stat().st_size > MAX_CATALOG:
        raise ValueError('missing, unsafe or oversized custody catalog')
    # Hash and parse the SAME bytes. Reopening a writable catalog after the
    # digest check would allow an attacker to switch versions in between.
    raw_catalog = catalog_file.read_bytes()
    actual_catalog_hash = hashlib.sha256(raw_catalog).hexdigest()
    if actual_catalog_hash != catalog_hash:
        raise ValueError('catalog SHA-256 mismatch with independent pin')
    catalog = json.loads(raw_catalog.decode('utf-8'), object_pairs_hook=unique_object)
    if (not isinstance(catalog, dict) or set(catalog) !=
            {'schema_version', 'format', 'repository', 'entries', 'trust_rule', 'offsite_custody'}
            or type(catalog['schema_version']) is not int or catalog['schema_version'] != 1
            or catalog['format'] != FORMAT
            or not isinstance(catalog['repository'], str)
            or catalog['repository'].lower() != repository.lower()
            or catalog['trust_rule'] != 'CATALOG_SHA256_AND_TSA_POLICY_MUST_BE_PINNED_OUT_OF_BAND'
            or catalog['offsite_custody'] != 'NOT_ATTESTED'):
        raise ValueError('unsupported custody catalog or repository identity mismatch')
    entries = catalog['entries']
    if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_ITEMS:
        raise ValueError('custody catalog entries are invalid')
    versions: set[str] = set()
    expected_files = {CATALOG_NAME}
    for item in entries:
        if (not isinstance(item, dict) or set(item) != {'version', 'filename', 'archive_sha256',
                                                       'size_bytes', 'manifest_sha256',
                                                       'paper_sha256', 'source_commit'}):
            raise ValueError('custody catalog contains an invalid entry')
        version = item['version']
        valid_version(version)
        if version in versions:
            raise ValueError('custody catalog has duplicate version')
        versions.add(version)
        if item['filename'] != version + '.opk.zip':
            raise ValueError('custody archive name and version mismatch')
        for key in ('archive_sha256', 'manifest_sha256', 'paper_sha256'):
            if not isinstance(item[key], str) or HEX.fullmatch(item[key]) is None:
                raise ValueError('invalid custody digest: ' + key)
        if (type(item['size_bytes']) is not int or not 0 < item['size_bytes'] <= MAX_ARCHIVE
                or not isinstance(item['source_commit'], str)
                or re.fullmatch(r'[0-9a-f]{40}\Z', item['source_commit'], re.ASCII) is None):
            raise ValueError('invalid archive length or source commit')
        expected_files.add(item['filename'])
    actual_files = {entry.name for entry in storage.iterdir()}
    if actual_files != expected_files:
        raise ValueError('custody store contents mismatch (missing or unexpected archive)')
    for name in expected_files:
        file = storage / name
        if file.is_symlink() or not file.is_file():
            raise ValueError('custody store contains a symlink or non-regular file: ' + name)

    results = []
    for item in entries:
        archive = storage / item['filename']
        check_archive_file(archive)
        if archive.stat().st_size != item['size_bytes'] or sha256_file(archive) != item['archive_sha256']:
            raise ValueError('archive SHA-256 mismatch or length mismatch: ' + item['version'])
        with tempfile.TemporaryDirectory(prefix='.opk-custody-audit-') as temp:
            restore_dir = Path(temp) / 'restored'
            report = restore(archive, restore_dir, item['archive_sha256'], policy)
            if report.get('timestamp') != 'VERIFIED':
                raise ValueError('custody requires current trusted timestamp verification')
            verified = source_details(restore_dir, repository, item['version'])
            if any(verified[key] != item[key] for key in
                   ('filename', 'source_commit', 'manifest_sha256', 'paper_sha256')):
                raise ValueError('archive source or evidence identity mismatch: ' + item['version'])
            results.append({'version': item['version'], 'archive_sha256': item['archive_sha256'],
                            'manifest_sha256': item['manifest_sha256'], 'timestamp': 'VERIFIED'})
    return {'status': 'PASS', 'repository': repository, 'archive_count': len(entries),
            'catalog_sha256': catalog_hash, 'timestamp': 'VERIFIED_USING_CURRENT_POLICY',
            'records': results, 'durability': 'NOT_PROVEN',
            'offsite_custody': 'NOT_ATTESTED', 'first_publication': 'NOT_PROVEN',
            'authorship': 'NOT_PROVEN'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['deposit', 'audit'])
    parser.add_argument('--repository', required=True, help='trusted expected GitHub OWNER/REPO')
    parser.add_argument('--policy', required=True, type=Path,
                        help='CA/CRL trust policy acquired independently of custody artifacts')
    parser.add_argument('--entry', nargs=3, action='append', metavar=('VERSION', 'ZIP', 'SHA256'),
                        help='repeat for each version: published tag, evidence ZIP, externally pinned SHA-256')
    parser.add_argument('--out', type=Path, help='new directory for deposited evidence archives')
    parser.add_argument('--store', type=Path, help='existing directory to audit read-only')
    parser.add_argument('--catalog-sha256', help='externally retained catalog fingerprint')
    arguments = parser.parse_args()
    try:
        if arguments.operation == 'deposit':
            if arguments.out is None or not arguments.entry or arguments.store or arguments.catalog_sha256:
                raise ValueError('deposit requires --entry and --out; audit arguments are not permitted')
            rows = [(v, Path(a), sha) for v, a, sha in arguments.entry]
            result = deposit(arguments.repository, rows, arguments.out, arguments.policy)
        else:
            if arguments.store is None or arguments.catalog_sha256 is None or arguments.entry or arguments.out:
                raise ValueError('audit requires --store and independently retained --catalog-sha256')
            result = audit(arguments.repository, arguments.store, arguments.catalog_sha256, arguments.policy)
        print(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError, OverflowError,
            json.JSONDecodeError, zipfile.BadZipFile, RuntimeError) as exc:
        print(json.dumps({'status': 'FAIL', 'error': str(exc)[:1000],
                          'offsite_custody': 'NOT_ATTESTED', 'durability': 'NOT_PROVEN'},
                         sort_keys=True), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
