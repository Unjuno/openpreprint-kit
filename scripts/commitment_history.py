#!/usr/bin/env python3
"""CI guard: existing anonymous record receipts must not be edited or deleted.

This compares Git commits only; enforce branch protection to prevent bypass.
Every commit in base_sha..HEAD that touches evidence/commitments is checked,
not just the net endpoint diff, so tamper-then-restore cannot hide a change.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys

RECEIPT_PATH = 'evidence/commitments'


def _run(repo: Path, *args: str) -> bytes:
    return subprocess.run(['git', *args], cwd=repo, check=True,
                          capture_output=True, timeout=10).stdout


def protect_history(repo: Path, base_sha: str) -> list[str]:
    if not re.fullmatch(r'[a-fA-F0-9]{40}', base_sha):
        return ['invalid or missing baseline commit SHA']
    # An all-zero sentinel never identifies a real commit. Callers that have a
    # genuine first commit must handle it explicitly and must NOT ask this
    # guard to report PASS: doing so silently disables the append-only check.
    if base_sha == '0' * 40:
        return ['invalid or missing baseline commit SHA (all-zero sentinel)']
    try:
        subprocess.run(['git', 'cat-file', '-e', base_sha + '^{commit}'], cwd=repo,
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        log = _run(repo, 'log', '--format=%H', base_sha + '..HEAD', '--', RECEIPT_PATH)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return ['unable to compare receipt history against trusted base commit']

    commits = [line.strip() for line in log.decode('utf-8', errors='replace').splitlines()
               if line.strip()]
    errors: list[str] = []
    for commit in commits:
        try:
            raw = _run(repo, 'diff-tree', '--no-commit-id', '--name-status', '-r', '-z',
                       '--no-renames', '--root', commit, '--', RECEIPT_PATH)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return ['unable to compare receipt history against trusted base commit']
        items = [x.decode('utf-8', errors='replace') for x in raw.split(b'\x00') if x]
        if len(items) % 2:
            return ['invalid Git receipt diff output']
        for status, path in zip(items[::2], items[1::2]):
            if not path.endswith('.json'):
                continue
            if status != 'A':
                errors.append('existing commitment changed or deleted in commit '
                              + commit[:12] + ': ' + path)
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
