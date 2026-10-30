#!/usr/bin/env python3
"""Validate OpenPreprint Kit metadata, or a complete release with --strict.

Runtime: Python >= 3.10 and PyYAML >= 6.0.2.
This script does not issue or verify cryptographic timestamps.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

import yaml

ROOT = Path(__file__).resolve().parent.parent
METADATA = ROOT / "preprint.yaml"
VERSION_RE = re.compile(r"^v(?:0|[1-9]\d*)(?:\.(?:0|[1-9]\d*)){0,2}$")
PLACEHOLDERS = {
    "Untitled Preprint",
    "Replace with author name",
    "Replace with a given name",
    "Replace with a family name",
    "Replace with an abstract.",
    "UNSPECIFIED",
}


def is_nonblank(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def valid_orcid(value: str) -> bool:
    match = re.fullmatch(r"(?:https://orcid\.org/)?(\d{4}-\d{4}-\d{4}-[\dX]{4})", value)
    if match is None:
        return False
    digits = match.group(1).replace("-", "")
    total = 0
    for digit in digits[:15]:
        total = (total + int(digit)) * 2
    check = (12 - total % 11) % 11
    return digits[-1] == ("X" if check == 10 else str(check))


def validate(strict: bool) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        with METADATA.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError, UnicodeError) as exc:
        print(f"ERROR: cannot read preprint.yaml: {exc}", file=sys.stderr)
        return 1

    if not isinstance(data, dict):
        errors.append("preprint.yaml must contain a YAML mapping")
        data = {}

    if data.get("schema_version") != 1:
        errors.append("schema_version must equal 1")

    for field in ("title", "abstract", "version", "paper", "license"):
        if not is_nonblank(data.get(field)):
            errors.append(f"{field} must be a non-empty string")

    for field in ("title", "abstract", "license"):
        if isinstance(data.get(field), str) and data[field] in PLACEHOLDERS:
            (errors if strict else warnings).append(f"{field} is still a placeholder")

    authors = data.get("authors")
    if not isinstance(authors, list) or not authors:
        errors.append("authors must be a non-empty list")
    else:
        for index, author in enumerate(authors):
            if not isinstance(author, dict):
                errors.append(f"authors[{index}] must be a mapping")
                continue
            name = author.get("name")
            family = author.get("family_names")
            given = author.get("given_names")
            if name is not None:
                if not is_nonblank(name) or family is not None or given is not None:
                    errors.append(f"authors[{index}] must have either name OR family_names/given_names")
                elif name in PLACEHOLDERS:
                    (errors if strict else warnings).append(f"authors[{index}].name is a placeholder")
            else:
                if not is_nonblank(family) or not is_nonblank(given):
                    errors.append(f"authors[{index}] requires family_names and given_names")
                for field, value in (("family_names", family), ("given_names", given)):
                    if isinstance(value, str) and value in PLACEHOLDERS:
                        (errors if strict else warnings).append(f"authors[{index}].{field} is a placeholder")
            orcid = author.get("orcid")
            if orcid is not None and not is_nonblank(orcid):
                errors.append(f"authors[{index}].orcid must be null or a non-empty string")
            elif isinstance(orcid, str) and not valid_orcid(orcid):
                errors.append(f"authors[{index}].orcid must be a valid ORCID (checksum included)")

    keywords = data.get("keywords")
    if not isinstance(keywords, list) or not all(is_nonblank(x) for x in keywords):
        errors.append("keywords must be a list of non-empty strings")

    version = data.get("version")
    if is_nonblank(version) and not VERSION_RE.fullmatch(version):
        errors.append("version must look like v1 or v1.2.3 (without leading zeros)")
    if strict and version == "v0":
        errors.append("v0 is a draft version; set a public release version")

    filename = data.get("paper")
    if is_nonblank(filename):
        filename_path = Path(filename)
        resolved = (ROOT / filename_path).resolve()
        if filename_path.is_absolute() or not resolved.is_relative_to(ROOT):
            errors.append("paper path must stay inside the repository")
        elif resolved.suffix.lower() != ".pdf":
            errors.append("paper must point to a PDF file")
        elif not resolved.is_file():
            (errors if strict else warnings).append(f"paper file not found: {filename}")
        else:
            try:
                with resolved.open("rb") as handle:
                    signature = handle.read(5)
                if signature != b"%PDF-":
                    errors.append(f"paper does not start with the PDF signature: {filename}")
                if resolved.stat().st_size < 10:
                    errors.append(f"paper PDF is too short: {filename}")
            except OSError as exc:
                errors.append(f"cannot inspect paper PDF: {exc}")

    for issue in warnings:
        print(f"WARNING: {issue}")
    for issue in errors:
        print(f"ERROR: {issue}", file=sys.stderr)
    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 1
    print(f"PASS: metadata checked ({len(warnings)} warning(s)); strict={strict}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="Require completed metadata and PDF")
    return validate(strict=parser.parse_args().strict)


if __name__ == "__main__":
    raise SystemExit(main())
