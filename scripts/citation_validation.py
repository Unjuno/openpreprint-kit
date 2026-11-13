#!/usr/bin/env python3
"""Independently validate generated CFF 1.2.0 and BibTeX publication assets.

Require cffconvert==2.0.0 (CLI) and bibtexparser==1.4.3. Metadata truth,
authorship, and peer review are outside this syntax/schema validation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

import yaml
from yaml_strict import safe_load_unique

MAX_CITATION_BYTES = 1024 * 1024


def read_text(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"citation asset must be a regular non-symlink file: {path.name}")
    if not (0 < path.stat().st_size <= MAX_CITATION_BYTES):
        raise ValueError(f"citation asset must not be empty or oversized: {path.name}")
    return path.read_text(encoding="utf-8")


def expected_authors(metadata_authors: object) -> list[dict]:
    if not isinstance(metadata_authors, list) or not metadata_authors:
        raise ValueError("publication authors must be a non-empty list")
    output = []
    for author in metadata_authors:
        if not isinstance(author, dict):
            raise ValueError("publication authors must be structured objects")
        if "name" in author:
            parsed = {"name": author["name"]}
        else:
            parsed = {"family-names": author.get("family_names"),
                      "given-names": author.get("given_names")}
        if author.get("orcid"):
            value = author["orcid"]
            parsed["orcid"] = value if value.startswith("https://orcid.org/") else "https://orcid.org/" + value
        output.append(parsed)
    return output


def cffconvert_binary() -> str:
    """Prefer the executable installed for this Python, even without venv activation.

    On Windows, a venv's console-script shim lives in Scripts/ while callers
    may invoke the absolute python.exe without adding Scripts/ to PATH.
    """
    python_bin = Path(sys.executable).parent
    names = ("cffconvert.exe", "cffconvert")
    for directory in (python_bin, python_bin / "Scripts"):
        for name in names:
            candidate = directory / name
            if candidate.is_file():
                return str(candidate)
    # Keep established global-PATH behavior for non-venv consumers.
    return shutil.which("cffconvert") or "cffconvert"


def validate_citations(folder: Path) -> None:
    folder = folder.resolve()
    cff_path = folder / "CITATION.cff"
    bib_path = folder / "citation.bib"
    metadata_path = folder / "preprint-metadata.json"
    cff = safe_load_unique(read_text(cff_path))
    bib_text = read_text(bib_path)
    metadata = json.loads(read_text(metadata_path))
    if not isinstance(cff, dict) or cff.get("cff-version") != "1.2.0":
        raise ValueError("CFF must contain valid version 1.2.0 metadata")
    if not isinstance(metadata, dict):
        raise ValueError("publication metadata must be a JSON object")
    for field in ("title", "version", "abstract", "license"):
        if (field in metadata or field in cff) and cff.get(field) != metadata.get(field):
            raise ValueError(f"citation {field} does not match the fixed publication metadata")
    if "keywords" in metadata and cff.get("keywords", []) != metadata["keywords"]:
        raise ValueError("citation keywords do not match the publication metadata")
    if cff.get("authors") != expected_authors(metadata.get("authors")):
        raise ValueError("citation authors do not match the fixed publication metadata")
    try:
        result = subprocess.run(
            [cffconvert_binary(), "--validate", "-i", str(cff_path)],
            capture_output=True, text=True, timeout=20, check=False, cwd=folder,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise ValueError("CFF schema validator unavailable or exceeded its timeout") from exc
    if result.returncode:
        raise ValueError("CFF 1.2.0 schema validation failed: " + result.stderr[-1000:])
    try:
        import bibtexparser
    except ImportError as exc:
        raise ValueError("BibTeX independent parser is not installed") from exc
    try:
        entries = bibtexparser.loads(bib_text).entries
    except Exception as exc:
        raise ValueError("BibTeX parsing failed") from exc
    if len(entries) != 1 or entries[0].get("ENTRYTYPE", "").lower() != "misc":
        raise ValueError("BibTeX must contain exactly one @misc citation entry")
    if any(not isinstance(entries[0].get(key), str) or not entries[0][key].strip()
           for key in ("title", "author", "note")):
        raise ValueError("BibTeX must include title, author and note")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        validate_citations(args.directory)
    except (OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: CFF schema validated and BibTeX parsed (citation truth NOT certified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
