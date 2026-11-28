#!/usr/bin/env python3
"""Verify a human-review inventory against immutable Git blob bytes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath


def verify_inventory(repo: Path, inventory_path: Path) -> tuple[str, int, list[str], str]:
    raw = inventory_path.read_bytes()
    inventory = json.loads(raw)
    fixed_sha = inventory.get("fixed_main_sha")
    if not isinstance(fixed_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", fixed_sha):
        raise ValueError("fixed_main_sha must be a full 40-character Git commit SHA")

    entries = inventory.get("manuscript_sources")
    if not isinstance(entries, list) or not entries:
        raise ValueError("manuscript_sources must be a non-empty list")

    failures: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        path = entry.get("path")
        if not isinstance(path, str):
            failures.append("entry has no string path")
            continue
        git_path = PurePosixPath(path)
        if git_path.is_absolute() or ".." in git_path.parts or path in seen:
            failures.append(f"unsafe or duplicate path: {path}")
            continue
        seen.add(path)
        result = subprocess.run(
            ["git", "-C", str(repo), "show", f"{fixed_sha}:{path}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode:
            failures.append(f"{path}: cannot read blob at {fixed_sha}: {result.stderr.decode(errors='replace').strip()}")
            continue
        blob = result.stdout
        actual_size = len(blob)
        actual_hash = hashlib.sha256(blob).hexdigest()
        if entry.get("bytes") != actual_size or entry.get("sha256") != actual_hash:
            failures.append(
                f"{path}: declared {entry.get('bytes')} bytes/{entry.get('sha256')}; "
                f"Git blob has {actual_size} bytes/{actual_hash}"
            )

    return fixed_sha, len(entries), failures, hashlib.sha256(raw).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Git repository containing fixed_main_sha")
    parser.add_argument("--inventory", type=Path, required=True, help="Review-input inventory JSON")
    parser.add_argument(
        "--reference", type=Path, action="append", default=[],
        help="Markdown document that must contain the inventory's current SHA-256 (repeatable)",
    )
    args = parser.parse_args()

    try:
        fixed_sha, count, failures, inventory_sha = verify_inventory(args.repo, args.inventory)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    for reference in args.reference:
        try:
            text = reference.read_text(encoding="utf-8")
        except OSError as exc:
            failures.append(f"{reference}: cannot read fingerprint reference: {exc}")
            continue
        if inventory_sha.lower() not in text.lower():
            failures.append(f"{reference}: missing inventory SHA-256 {inventory_sha}")

    if failures:
        print(f"FAIL: {len(failures)} issue(s) in {count} manuscript entries at {fixed_sha}")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"PASS: {count} manuscript entries match Git blob bytes at {fixed_sha}")
    print(f"Inventory SHA-256: {inventory_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
