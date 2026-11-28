"""Validate public release tags."""
import argparse
import json
import re
from pathlib import Path

PUBLIC_TAG = re.compile(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")

def validate_public_tag(value):
    if not isinstance(value, str) or not PUBLIC_TAG.fullmatch(value):
        raise ValueError("public Release version must be stable SemVer vMAJOR.MINOR.PATCH")
    return value

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metadata", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.metadata.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("metadata must be a JSON object")
        tag = validate_public_tag(data.get("version"))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    print(f"tag={tag}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
