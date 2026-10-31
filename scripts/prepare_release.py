#!/usr/bin/env python3
"""Create a deterministic Release bundle from a validated OpenPreprint repository.

Requirements: Python >= 3.10, PyYAML >= 6.0.2. This tool NEVER publishes a release.
The manifest contains ordinary hashes, NOT a signed timestamp or publication proof.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

import yaml

from validate import ROOT, validate

REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
COMMIT_RE = re.compile(r"^[a-fA-F0-9]{40}$")
PAYLOAD_FILES = (
    "CITATION.cff",
    "RELEASE_NOTES.md",
    "citation.bib",
    "paper.pdf",
    "preprint-metadata.json",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def escaped_bibtex(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}", "{": r"\{", "}": r"\}",
        "%": r"\%", "&": r"\&", "_": r"\_", "#": r"\#",
        "$": r"\$", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, " " if char in "\r\n\t" else char) for char in value)


def cff_author(author: dict) -> dict:
    if "name" in author:
        result = {"name": author["name"]}  # Research group / entity
    else:
        result = {"family-names": author["family_names"], "given-names": author["given_names"]}
    if author.get("orcid"):
        orcid = author["orcid"]
        result["orcid"] = orcid if orcid.startswith("https://orcid.org/") else f"https://orcid.org/{orcid}"
    return result


def bibtex_author(author: dict) -> str:
    if "name" in author:
        return "{" + escaped_bibtex(author["name"]) + "}"
    return escaped_bibtex(author["family_names"] + ", " + author["given_names"])


def create_bundle(output: Path, repository: str | None, commit: str | None) -> None:
    if repository is not None and not REPOSITORY_RE.fullmatch(repository):
        raise ValueError("--repository must be OWNER/REPO")
    if commit is not None and not COMMIT_RE.fullmatch(commit):
        raise ValueError("--commit must be a 40-digit Git commit SHA")
    if (repository is None) != (commit is None):
        raise ValueError("--repository and --commit must be supplied together")
    if validate(strict=True) != 0:
        raise ValueError("strict validation failed; release bundle not built")

    with (ROOT / "preprint.yaml").open(encoding="utf-8") as source:
        metadata = yaml.safe_load(source)
    paper_path = (ROOT / metadata["paper"]).resolve()
    output = output.resolve()
    if output == ROOT or output == paper_path or output == ROOT / "paper":
        raise ValueError("output cannot overwrite the repository or paper")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("output directory must be empty (never overwrite a previous release bundle)")
    output.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(paper_path, output / "paper.pdf")
    paper_sha = sha256_file(output / "paper.pdf")
    source = {"repository": repository, "commit": commit} if repository else None
    record = {
        "schema_version": 1,
        "title": metadata["title"],
        "authors": metadata["authors"],
        "abstract": metadata["abstract"],
        "keywords": metadata["keywords"],
        "version": metadata["version"],
        "license": metadata["license"],
        "paper_source_path": metadata["paper"],
        "paper_asset": "paper.pdf",
        "paper_sha256": paper_sha,
        "paper_size_bytes": (output / "paper.pdf").stat().st_size,
        "source_claim": source,
        "time_attestation": None,
    }
    (output / "preprint-metadata.json").write_text(
        json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )

    cff = {
        "cff-version": "1.2.0",
        "message": "Please cite this preprint using these metadata and its version-specific release URL.",
        "title": metadata["title"],
        "authors": [cff_author(author) for author in metadata["authors"]],
        "abstract": metadata["abstract"],
        "version": metadata["version"],
        "license": metadata["license"],
    }
    if metadata["keywords"]:
        cff["keywords"] = metadata["keywords"]
    if repository:
        cff["repository-code"] = f"https://github.com/{repository}"
        cff["commit"] = commit
    (output / "CITATION.cff").write_text(
        yaml.safe_dump(cff, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8"
    )

    author_text = " and ".join(bibtex_author(author) for author in metadata["authors"])
    citation_key = (repository.split("/")[-1] if repository else "preprint").replace("-", "_")
    citation_key += "_" + metadata["version"].replace(".", "_")
    bib_fields = {
        "title": escaped_bibtex(metadata["title"]),
        "author": author_text,
        "note": f"Preprint, version {escaped_bibtex(metadata['version'])}; release date not independently attested",
    }
    if repository:
        bib_fields["url"] = f"https://github.com/{repository}/releases/tag/{metadata['version']}"
    lines = [f"@misc{{{citation_key},"]
    lines.extend(f"  {key} = {{{value}}}," for key, value in bib_fields.items())
    lines.append("}")
    (output / "citation.bib").write_text("\n".join(lines) + "\n", encoding="utf-8")

    normalized_title = " ".join(metadata["title"].split())
    release_url = f"https://github.com/{repository}/releases/tag/{metadata['version']}" if repository else "(local bundle)"
    notes = (
        f"# {normalized_title} — {metadata['version']}\n\n"
        f"Version-specific release: {release_url}\n\n"
        f"Paper license: {metadata['license']}\n\n"
        f"Paper SHA-256: {paper_sha}\n\n"
        "This release includes machine-readable citation metadata and a checksum manifest.\n"
        "**Checksums alone are not time evidence. Verify any timestamp.tsq/timestamp.tsr sidecars with an independently selected trust policy. Public access time is not proven.**\n"
    )
    (output / "RELEASE_NOTES.md").write_text(notes, encoding="utf-8")

    files = {
        filename: {
            "sha256": sha256_file(output / filename),
            "size_bytes": (output / filename).stat().st_size,
        }
        for filename in PAYLOAD_FILES
    }
    manifest = {"schema_version": 1, "algorithm": "sha256", "files": files}
    (output / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    sums = {name: info["sha256"] for name, info in files.items()}
    sums["manifest.json"] = sha256_file(output / "manifest.json")
    (output / "SHA256SUMS").write_text(
        "".join(f"{sums[name]}  {name}\n" for name in sorted(sums)), encoding="ascii"
    )
    print(f"PASS: created {len(PAYLOAD_FILES) + 2} release assets in {output}")
    print("WARNING: these files are not a cryptographic timestamp or publication proof")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="dist", type=Path)
    parser.add_argument("--repository", help="GitHub OWNER/REPO (source claim, not attestation)")
    parser.add_argument("--commit", help="40-digit source commit SHA (source claim, not attestation)")
    arguments = parser.parse_args()
    try:
        create_bundle(arguments.output, arguments.repository, arguments.commit)
    except (OSError, ValueError, yaml.YAMLError, KeyError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
