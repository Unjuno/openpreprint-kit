#!/usr/bin/env python3
"""Create/verify local HMAC commitments for confidential records.

NEVER place originals or secret keys inside a public GitHub repository.
The receipt alone is only a commitment; it is NOT a timestamp, clinical validation,
consent proof, identity proof, or protection from deletion. A verifier who receives
an original and its per-record secret can establish a match to an anchored receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import sys

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = b'OpenPreprint-Kit private record commitment v1\x00'
MAX_BYTES = 100 * 1024 * 1024
ID_RE = re.compile(r'[0-9a-f]{32}\Z', re.ASCII)
HEX_RE = re.compile(r'[0-9a-f]{64}\Z', re.ASCII)


def commit_file(path: Path, key: bytes) -> str:
    if len(key) != 32 or path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError('invalid private source/key or record size exceeded')
    digester = hmac.new(key, DOMAIN, hashlib.sha256)
    total = 0
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            total += len(block)
            if total > MAX_BYTES:
                raise ValueError('private record exceeded 100 MiB')
            digester.update(block)
    return digester.hexdigest()


def ensure_outside_root(path: Path) -> None:
    if path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('confidential original and secret key MUST remain outside the public repository')


def receipt_data(receipt: Path) -> dict:
    from json import loads
    def no_duplicates(items):
        obj = {}
        for k, v in items:
            if k in obj:
                raise ValueError('duplicate JSON keys in private receipt')
            obj[k] = v
        return obj
    if receipt.is_symlink() or not receipt.is_file() or receipt.stat().st_size > 4096:
        raise ValueError('invalid receipt')
    data = loads(receipt.read_text('utf-8'), object_pairs_hook=no_duplicates)
    if (not isinstance(data, dict) or set(data) != {'schema_version', 'record_id', 'algorithm', 'commitment'}
            or type(data['schema_version']) is not int or data['schema_version'] != 1
            or data['algorithm'] != 'HMAC-SHA256'
            or not isinstance(data['record_id'], str) or not ID_RE.fullmatch(data['record_id'])
            or not isinstance(data['commitment'], str) or not HEX_RE.fullmatch(data['commitment'])
            or receipt.name != data['record_id'] + '.json'):
        raise ValueError('malformed or misnamed receipt')
    return data


def seal(source: Path, key_path: Path) -> Path:
    ensure_outside_root(source)
    ensure_outside_root(key_path)
    if key_path.parent.is_symlink() or not key_path.parent.is_dir():
        raise ValueError('secret directory must already exist and must not be a symlink')
    key = secrets.token_bytes(32)
    commitment = commit_file(source, key)
    rid = secrets.token_hex(16)
    receipt_dir = ROOT / 'evidence' / 'commitments'
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = receipt_dir / (rid + '.json')
    if receipt_path.exists() or key_path.exists() or key_path.is_symlink():
        raise ValueError('receipt or private key already exists; refuse overwrite')
    receipt = {'schema_version': 1, 'record_id': rid,
               'algorithm': 'HMAC-SHA256', 'commitment': commitment}
    fd = None
    try:
        fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        with os.fdopen(fd, 'wb') as handle:
            fd = None
            handle.write(key)
        with receipt_path.open('x', encoding='utf-8') as handle:
            json.dump(receipt, handle, sort_keys=True, separators=(',', ':'))
            handle.write('\n')
    except BaseException:
        if fd is not None:
            os.close(fd)
        key_path.unlink(missing_ok=True)
        receipt_path.unlink(missing_ok=True)
        raise
    return receipt_path


def verify(source: Path, key_path: Path, receipt_path: Path) -> bool:
    ensure_outside_root(source)
    ensure_outside_root(key_path)
    data = receipt_data(receipt_path)
    if key_path.is_symlink() or not key_path.is_file():
        raise ValueError('private key missing or unsafe')
    key = key_path.read_bytes()
    return hmac.compare_digest(commit_file(source, key), data['commitment'])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('seal')
    p.add_argument('original', type=Path)
    p.add_argument('--key-output', type=Path, required=True)
    p = sub.add_parser('verify')
    p.add_argument('original', type=Path)
    p.add_argument('--key', type=Path, required=True)
    p.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.cmd == 'seal':
            receipt = seal(args.original, args.key_output)
            print('PASS: created public, non-identifying commitment receipt ' + receipt.relative_to(ROOT).as_posix())
            print('Keep the 256-bit per-record key outside GitHub; never upload your confidential original.')
        else:
            if not verify(args.original, args.key, args.receipt):
                print('FAIL: original record does not match sealed commitment', file=sys.stderr)
                return 1
            print('PASS: confidential record matches independently provided key and public receipt')
            print('NOTE: no timestamp was checked; verify the release manifest and RFC 3161 evidence separately.')
        return 0
    except (ValueError, OSError, UnicodeError, TypeError) as exc:
        print('FAIL: confidential record seal/verification rejected: ' + type(exc).__name__, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
