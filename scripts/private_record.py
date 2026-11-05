#!/usr/bin/env python3
"""Local-only private record commitments. Never upload original files or receipts.

This is not encryption, a medical-record system or proof of the clinical event time.
The expected commitment must come from an independently authenticated bundle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys

SCHEME = 'opk-private-sha256-v1'
DOMAIN = b'OpenPreprint-Kit/private-record/v1\x00'
MAX_PRIVATE_BYTES = 100 * 1024 * 1024
ROOT = Path(__file__).resolve().parents[1]
HEX = re.compile(r'[0-9a-f]{64}')


def outside_git(path: Path) -> Path:
    path = path.absolute()
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError('private path must not contain symlinks')
    resolved = path.resolve()
    if resolved.is_relative_to(ROOT):
        raise ValueError('private originals and receipts must be outside the toolkit')
    if any((parent / '.git').exists() or (parent / '.git').is_symlink() for parent in resolved.parents):
        raise ValueError('private originals and receipts must be outside Git working trees')
    return resolved


def file_digest(path: Path) -> bytes:
    path = outside_git(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= MAX_PRIVATE_BYTES:
        raise ValueError('private input must be a nonempty regular file of at most 100 MiB')
    digest, total = hashlib.sha256(), 0
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    with os.fdopen(os.open(path, flags), 'rb') as stream:
        opened = os.fstat(stream.fileno())
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise ValueError('private input changed before reading')
        for block in iter(lambda: stream.read(1024*1024), b''):
            total += len(block)
            if total > MAX_PRIVATE_BYTES:
                raise ValueError('private input exceeds size limit')
            digest.update(block)
        after = os.fstat(stream.fileno())
    if total != before.st_size or (after.st_size, after.st_mtime_ns) != (before.st_size, before.st_mtime_ns):
        raise ValueError('private input changed during reading')
    return digest.digest()


def commitment(digest: bytes, nonce: bytes, identifier: str) -> str:
    return hashlib.sha256(DOMAIN + identifier.encode('ascii') + b'\x00' + nonce + digest).hexdigest()


def commit_record(source: Path, receipt: Path) -> dict:
    target = outside_git(receipt)
    if target.exists():
        raise ValueError('private receipt already exists; never overwrite it')
    digest = file_digest(source)
    nonce = secrets.token_bytes(32)
    identifier = 'pr-' + secrets.token_hex(16)
    value = commitment(digest, nonce, identifier)
    opening = dict(schema_version=1, scheme=SCHEME, id=identifier, nonce=nonce.hex(), commitment=value)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(target, flags, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(opening, stream, sort_keys=True); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return dict(id=identifier, kind='record', visibility='private',
                commitment=dict(scheme=SCHEME, digest=value))


def unique_object(pairs):
    result = {}
    for k, v in pairs:
        if k in result: raise ValueError('duplicate private receipt key')
        result[k] = v
    return result


def verify_record(source: Path, receipt: Path, expected_commitment: str) -> None:
    if not isinstance(expected_commitment, str) or HEX.fullmatch(expected_commitment) is None:
        raise ValueError('an independently authenticated 64-digit commitment is required')
    path = outside_git(receipt)
    if not path.is_file() or path.stat().st_size > 4096:
        raise ValueError('invalid private receipt')
    data = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique_object)
    if (not isinstance(data, dict) or set(data) != {'schema_version', 'scheme', 'id', 'nonce', 'commitment'}
            or type(data['schema_version']) is not int or data['schema_version'] != 1
            or data['scheme'] != SCHEME or not isinstance(data['id'], str)
            or re.fullmatch(r'pr-[0-9a-f]{32}', data['id']) is None
            or not isinstance(data['nonce'], str) or HEX.fullmatch(data['nonce']) is None
            or not isinstance(data['commitment'], str) or HEX.fullmatch(data['commitment']) is None):
        raise ValueError('invalid private opening schema')
    actual = commitment(file_digest(source), bytes.fromhex(data['nonce']), data['id'])
    if not secrets.compare_digest(actual, expected_commitment) or not secrets.compare_digest(actual, data['commitment']):
        raise ValueError('private record does not match the independently supplied commitment')


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation', choices=('commit', 'verify'))
    p.add_argument('source', type=Path)
    p.add_argument('--receipt', required=True, type=Path)
    p.add_argument('--commitment', help='digest obtained from separately authenticated evidence')
    args = p.parse_args()
    try:
        if args.operation == 'commit':
            result = commit_record(args.source, args.receipt)
        else:
            verify_record(args.source, args.receipt, args.commitment)
            result = dict(status='MATCH', basis='caller_supplied_commitment',
                          clinical_event_time='NOT_PROVEN', authorship='NOT_PROVEN')
        print(json.dumps(result, sort_keys=True, indent=2)); return 0
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        # Do not emit sensitive path names or file contents in logs.
        print('FAIL: private operation refused; check local paths, receipt and trusted commitment. No private data logged.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
