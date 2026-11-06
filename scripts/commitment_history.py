#!/usr/bin/env python3
"""CI guard: existing anonymous record receipts must not be edited or deleted.

This compares Git commits only; enforce branch protection to prevent bypass.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys


def protect_history(repo: Path, base_sha: str) -> list[str]:
    if not re.fullmatch(r'[a-fA-F0-9]{40}', base_sha):
        return ['invalid or missing baseline commit SHA']
    if base_sha == '0' * 40:
        return []  # First commit has no predecessor; configured separately in CI.
    try:
        subprocess.run(['git', 'cat-file', '-e', base_sha + '^{commit}'], cwd=repo,
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        proc = subprocess.run(['git', 'diff', '--name-status', '--no-renames', '-z',
                               base_sha, 'HEAD', '--', 'evidence/commitments'], cwd=repo,
                              check=True, capture_output=True, timeout=10)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return ['unable to compare receipt history against trusted base commit']
    raw = proc.stdout.split(b'\x00')
    items = [x.decode('utf-8', errors='replace') for x in raw if x]
    if len(items) % 2:
        return ['invalid Git receipt diff output']
    errors = []
    for status, path in zip(items[::2], items[1::2]):
        if not path.endswith('.json'):
            continue
        if status != 'A':
            errors.append('existing commitment changed or deleted: ' + path)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--base-sha', required=True)
    args = parser.parse_args()
    errors = protect_history(args.root, args.base_sha)
    if errors:
        for error in errors:
            print('FAIL: ' + error, file=sys.stderr)
        return 1
    print('PASS: no previously committed private receipt was changed or deleted')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
