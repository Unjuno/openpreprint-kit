#!/usr/bin/env python3
"""Verify bundle integrity offline; does not prove authorship or publication time.

For authenticity, compare against a separately trusted digest or release attestation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

# Standard library only: verification must not depend on YAML parsing or CI tooling.
PAYLOAD_FILES = (
    "CITATION.cff", "RELEASE_NOTES.md", "citation.bib",
    "paper.pdf", "preprint-metadata.json",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


EXPECTED_FILES = set(PAYLOAD_FILES) | {"manifest.json", "SHA256SUMS"}
RESEARCH_FILES = {"research-manifest.json", "research-data.zip"}
EVIDENCE_FILES = {"timestamp.tsq", "timestamp.tsr"}
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def unique_object(pairs: list[tuple]) -> dict:
    """Reject ambiguous JSON rather than silently using the last duplicate key."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def verify(folder: Path, expected_paper_sha256: str | None, expected_manifest_sha256: str | None = None) -> list[str]:
    errors: list[str] = []
    if not folder.is_dir() or folder.is_symlink():
        return ["bundle must be a real directory"]
    actual_files = {item.name for item in folder.iterdir()}
    if actual_files not in (EXPECTED_FILES, EXPECTED_FILES | EVIDENCE_FILES,
                            EXPECTED_FILES | RESEARCH_FILES, EXPECTED_FILES | RESEARCH_FILES | EVIDENCE_FILES):
        errors.append(f"unexpected bundle contents; missing={sorted(EXPECTED_FILES - actual_files)}, extra={sorted(actual_files - EXPECTED_FILES)}")
        return errors
    for name in actual_files:
        item = folder / name
        if item.is_symlink() or not item.is_file():
            errors.append(f"asset {name} must be a regular, non-symlink file")
    if errors:
        return errors
    if any((folder / name).stat().st_size > 1024*1024 for name in
           ("manifest.json", "preprint-metadata.json", "SHA256SUMS")):
        return ["metadata or manifest exceeds 1 MiB"]
    if RESEARCH_FILES.issubset(actual_files):
        from research_bundle import MAX_JSON, MAX_TOTAL, MAX_ITEMS
        if ((folder / "research-manifest.json").stat().st_size > MAX_JSON or
                (folder / "research-data.zip").stat().st_size > MAX_TOTAL + MAX_ITEMS*2048 + 65536):
            return ["research package exceeds size limit"]
    try:
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        metadata = json.loads((folder / "preprint-metadata.json").read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except (OSError, ValueError, UnicodeError) as exc:
        return [f"invalid JSON: {exc}"]
    if not isinstance(manifest, dict) or type(manifest.get("schema_version")) is not int or manifest["schema_version"] not in (1, 2) or manifest.get("algorithm") != "sha256":
        return ["unsupported manifest schema or algorithm"]
    payload_files = set(PAYLOAD_FILES) | (RESEARCH_FILES if manifest["schema_version"] == 2 else set())
    required = payload_files | {"manifest.json", "SHA256SUMS"}
    if actual_files not in (required, required | EVIDENCE_FILES):
        return ["manifest schema does not match the exact asset set"]
    contents = manifest.get("files")
    if not isinstance(contents, dict) or set(contents) != payload_files:
        return ["manifest must list exactly the required payload assets"]

    digest_values = {}
    for name in sorted(payload_files):
        item = contents[name]
        if not isinstance(item, dict) or set(item) != {"sha256", "size_bytes"}:
            errors.append(f"invalid manifest entry: {name}")
            continue
        digest = item["sha256"]
        size = item["size_bytes"]
        if not isinstance(digest, str) or not HEX_SHA256.fullmatch(digest) or type(size) is not int or size < 0:
            errors.append(f"invalid digest or size in manifest: {name}")
            continue
        actual_digest = sha256_file(folder / name)
        actual_size = (folder / name).stat().st_size
        if actual_digest != digest or actual_size != size:
            errors.append(f"checksum/size mismatch: {name}")
        digest_values[name] = actual_digest

    digest_values["manifest.json"] = sha256_file(folder / "manifest.json")
    expected_sums = "".join(f"{digest_values[name]}  {name}\n" for name in sorted(digest_values)) if len(digest_values) == len(payload_files) + 1 else None
    if expected_sums is None or (folder / "SHA256SUMS").read_text(encoding="utf-8") != expected_sums:
        errors.append("SHA256SUMS does not match the manifest and assets")

    if not isinstance(metadata, dict):
        errors.append("preprint-metadata.json must contain an object")
    elif metadata.get("paper_sha256") != digest_values.get("paper.pdf"):
        errors.append("metadata paper_sha256 is inconsistent with paper.pdf")
    if expected_paper_sha256 is not None:
        if not HEX_SHA256.fullmatch(expected_paper_sha256):
            errors.append("expected hash must be 64 lowercase hex digits")
        elif expected_paper_sha256 != digest_values.get("paper.pdf"):
            errors.append("paper does not match the separately supplied expected SHA-256")
    if expected_manifest_sha256 is not None:
        if (not isinstance(expected_manifest_sha256, str) or not HEX_SHA256.fullmatch(expected_manifest_sha256)
                or expected_manifest_sha256 != digest_values["manifest.json"]):
            errors.append("manifest does not match the separately supplied expected SHA-256")
    if manifest["schema_version"] == 2 and not errors:
        try:
            from research_bundle import verify_research
            verify_research(folder, metadata)
        except (OSError, ValueError, TypeError, KeyError, RecursionError, zipfile.BadZipFile, RuntimeError) as exc:
            errors.append(f"invalid research package: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="directory containing downloaded Release assets")
    parser.add_argument("--expected-paper-sha256", help="separately trusted fingerprint for paper.pdf")
    parser.add_argument("--expected-manifest-sha256", help="independently trusted fingerprint binding ALL release assets")
    arguments = parser.parse_args()
    try:
        errors = verify(arguments.directory, arguments.expected_paper_sha256, arguments.expected_manifest_sha256)
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError) as exc:
        errors = [str(exc)]
    for error in errors:
        print(f"FAIL: {error}", file=sys.stderr)
    if errors:
        return 1
    print("PASS: release assets and SHA256SUMS are internally consistent")
    if arguments.expected_manifest_sha256:
        print("PASS: complete manifest matches separately supplied SHA-256 fingerprint")
    if arguments.expected_paper_sha256:
        print("PASS: paper.pdf matches separately supplied SHA-256 fingerprint")
        if (arguments.directory / "research-manifest.json").exists() and not arguments.expected_manifest_sha256:
            print("NOTE: a paper fingerprint alone does NOT authenticate research data; pin the manifest or verify its timestamp")
    elif not arguments.expected_manifest_sha256:
        print("WARNING: no independent trusted fingerprint supplied; authenticity NOT established")
    if (arguments.directory / "timestamp.tsr").exists():
        print("NOTE: timestamp files present but NOT verified; use timestamp.py verify with an independent trust policy")
    print("NOTE: existence time, public availability and authorship are NOT verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
