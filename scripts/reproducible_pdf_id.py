"""Write a deterministic xdvipdfmx trailer ID for a source commit."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re


def trailer_id_tex(source_commit: str) -> str:
    """Return a pdf:trailerid special derived from a full Git commit SHA."""
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("source commit must be a full lowercase 40-character Git SHA")
    identifier = hashlib.sha256(source_commit.encode("ascii")).hexdigest()[:32]
    return f"\\special{{pdf:trailerid [<{identifier}><{identifier}>]}}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    content = trailer_id_tex(args.source_commit)
    args.output.write_text(content, encoding="ascii", newline="\n")
    print(f"Wrote deterministic PDF trailer ID for {args.source_commit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
