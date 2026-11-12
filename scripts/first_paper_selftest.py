#!/usr/bin/env python3
"""Run an author-metadata-confirmed manuscript through OPK; do not publish or timestamp.

User-confirmed display author/license are not signed legal identity attestations.
Requires the same hash-locked dependencies as OPK.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from pdf_validation import inspect_pdf
from verify_release import verify as verify_bundle
from yaml_strict import safe_load_unique
import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANUSCRIPT = ROOT / 'manuscripts' / 'openpreprint-kit'
PINNED_BASELINE = '940d0d06d957cd0708f644a595911bdbc3fffa64'
CONFIRMED_AUTHOR = 'Unjuno'
CONFIRMED_LICENSE = 'CC-BY-4.0'
CONFIRMED_VERSION = 'v1'
NEGATIVE_CASES = {
    'changed_pdf': ('paper.pdf', 'checksum/size mismatch'),
    'changed_research': ('research-assets.tar', 'checksum/size mismatch'),
    'changed_manifest': ('manifest.json', 'invalid JSON'),
    'missing_citation': ('citation.bib', 'unexpected bundle contents'),
}


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def run_script(root: Path, script: str, *args: str, success: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [sys.executable, str(root / 'scripts' / script), *args],
        cwd=root, text=True, capture_output=True, timeout=45, check=False,
        env={**os.environ, 'PATH': str(Path(sys.executable).parent) + os.pathsep + os.environ.get('PATH', '')},
    )
    if (result.returncode == 0) != success:
        raise ValueError(f'{script} unexpected return code {result.returncode}: '
                         + (result.stderr or result.stdout)[-800:])
    return result


def copy_regular(source: Path, destination: Path) -> None:
    if source.is_symlink() or not source.is_file():
        raise ValueError(f'unsafe or missing manuscript file: {source}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def validate_input_tree(root: Path) -> None:
    if root.is_symlink() or not root.is_dir():
        raise ValueError('manuscript must be a regular non-symlink directory')
    for area in ('data', 'analysis'):
        folder = root / area
        if folder.is_symlink() or not folder.is_dir():
            raise ValueError('invalid manuscript ' + area + ' directory')
        for path in folder.rglob('*'):
            if path.is_symlink() or not (path.is_file() or path.is_dir()):
                raise ValueError('unsafe manuscript input: ' + str(path))


def export_candidate(bundle: Path, destination: Path) -> None:
    """Export a verified publication candidate without overwriting evidence.

    This function creates NO GitHub Release, signature, or independent approval.
    The manuscript's author/license are declared, not independently authenticated.
    """
    bundle = bundle.absolute()
    destination = destination.absolute()
    if destination.is_relative_to(bundle):
        raise ValueError('draft candidate destination must be outside the source bundle')
    if destination.exists() or destination.is_symlink():
        raise ValueError('candidate destination already exists')
    if (not destination.parent.is_dir() or destination.parent.is_symlink()
            or bundle.is_symlink() or not bundle.is_dir()):
        raise ValueError('candidate source/destination directory is not safe')
    problems = verify_bundle(bundle, None)
    if problems:
        raise ValueError('candidate bundle integrity failed: ' + '; '.join(problems))
    with tempfile.TemporaryDirectory(prefix='.opk-candidate-', dir=destination.parent) as temporary:
        intermediate = Path(temporary) / 'candidate'
        shutil.copytree(bundle, intermediate)
        copied_problems = verify_bundle(intermediate, None)
        if copied_problems:
            raise ValueError('copied candidate integrity failed: ' + '; '.join(copied_problems))
        if destination.exists() or destination.is_symlink():
            raise ValueError('candidate destination already exists')
        os.rename(intermediate, destination)


def perform(manuscript: Path, paper: Path, export_to: Path | None = None) -> dict:
    validate_input_tree(manuscript)
    if paper.is_symlink() or not paper.is_file():
        raise ValueError('paper PDF must be a real, non-symlink file')
    paper_bytes, pages = inspect_pdf(paper)

    with tempfile.TemporaryDirectory(prefix='opk-first-paper-') as location:
        workspace = Path(location)
        root = workspace / 'source'
        root.mkdir()
        shutil.copytree(ROOT / 'scripts', root / 'scripts', ignore=shutil.ignore_patterns('__pycache__'))
        for area in ('data', 'analysis'):
            shutil.copytree(manuscript / area, root / area,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        copy_regular(manuscript / 'paper.md', root / 'supplements' / 'paper.md')
        copy_regular(manuscript / 'LICENSE-NOTICE.txt', root / 'supplements' / 'LICENSE-NOTICE.txt')
        copy_regular(manuscript / 'research-assets.yaml', root / 'research-assets.yaml')
        copy_regular(manuscript / 'preprint.yaml', root / 'preprint.yaml')
        copy_regular(paper, root / 'paper' / 'paper.pdf')

        baseline = subprocess.run(
            [sys.executable, str(root / 'analysis' / 'summarize_ci.py'),
             '--data', str(root / 'data')],
            capture_output=True, text=True, timeout=20, check=False,
        )
        if baseline.returncode:
            raise ValueError('retained CI hash/count verification failed: ' + baseline.stderr[-400:])
        summary = json.loads(baseline.stdout)
        if (summary.get('evaluated_commit') != PINNED_BASELINE or
                summary.get('tests') != 274 or len(summary.get('modules', {})) != 26 or
                summary.get('skipped') != 0):
            raise ValueError('pinned first-paper CI baseline is inconsistent')

        # User explicitly confirmed author display name, licence and v1. This
        # software can check the declaration, not the account holder's identity.
        config_path = root / 'preprint.yaml'
        approved_text = config_path.read_text(encoding='utf-8')
        metadata = safe_load_unique(approved_text)
        if (not isinstance(metadata, dict) or metadata.get('authors') != [{'name': CONFIRMED_AUTHOR, 'orcid': None}]
                or metadata.get('license') != CONFIRMED_LICENSE or metadata.get('version') != CONFIRMED_VERSION):
            raise ValueError('first-paper author, license or version differs from approved publication metadata')
        asset_declaration = safe_load_unique((root / 'research-assets.yaml').read_text(encoding='utf-8'))
        if (not isinstance(asset_declaration, dict)
                or any(item.get('license') != CONFIRMED_LICENSE
                       for item in asset_declaration.get('public_assets', [])
                       if isinstance(item, dict) and item.get('role') == 'supplementary')):
            raise ValueError('first-paper supplementary assets have an unapproved license')
        # Preserve the old safety gate as a negative control: revoked/draft
        # metadata must fail strict validation, while canonical v1 must pass.
        unapproved = {**metadata, 'version': 'v0', 'license': 'UNSPECIFIED'}
        try:
            config_path.write_text(yaml.safe_dump(unapproved, allow_unicode=True), encoding='utf-8')
            rejected = run_script(root, 'validate.py', '--strict', success=False)
            if ('v0 is a draft version' not in rejected.stderr
                    or 'license is still a placeholder' not in rejected.stderr):
                raise ValueError('unapproved manuscript metadata unexpectedly passed publication gates')
        finally:
            config_path.write_text(approved_text, encoding='utf-8')
        run_script(root, 'validate.py', '--strict')
        prepared = run_script(root, 'prepare_release.py', '--output', str(root / 'bundle'))
        if 'PASS:' not in prepared.stdout:
            raise ValueError('release bundle was not constructed')
        run_script(root, 'citation_validation.py', str(root / 'bundle'))
        run_script(root, 'verify_release.py', str(root / 'bundle'))
        manifest = json.loads((root / 'bundle' / 'manifest.json').read_text('utf-8'))
        if len(manifest.get('files', {})) != 7:
            raise ValueError('first-paper bundle is missing declared research objects')
        assets = json.loads((root / 'bundle' / 'research-assets.json').read_text('utf-8'))
        if len(assets.get('entries', [])) != 7:
            raise ValueError('first-paper input asset count differs from the publication inventory')
        if manifest['files']['paper.pdf']['sha256'] != digest_file(paper):
            raise ValueError('staged PDF is different from the submitted first-paper PDF')

        negatives = {}
        for case, (name, expected) in NEGATIVE_CASES.items():
            tampered = workspace / case
            shutil.copytree(root / 'bundle', tampered)
            target = tampered / name
            if case == 'missing_citation':
                target.unlink()
            elif case == 'changed_manifest':
                target.write_bytes(target.read_bytes() + b'\n{invalid\n')
            else:
                with target.open('ab') as stream:
                    stream.write(b'\nUNAUTHORIZED_MUTATION\n')
            rejected = run_script(root, 'verify_release.py', str(tampered), success=False)
            if expected.lower() not in rejected.stderr.lower():
                raise ValueError(f'{case} was rejected for the wrong reason: {rejected.stderr[-400:]}')
            negatives[case] = True

        if export_to is not None:
            export_candidate(root / 'bundle', export_to)

        return {
            'schema_version': 1,
            'scope': 'LOCAL_SELF_APPLICATION_ONLY',
            'verdict': 'PASS',
            'manuscript': 'OpenPreprint Kit first technical report (APPROVED METADATA; NO RELEASE)',
            'baseline_commit': PINNED_BASELINE,
            'baseline_tests': summary['tests'],
            'baseline_modules': len(summary['modules']),
            'paper_pdf_sha256': digest_file(paper),
            'paper_pdf_bytes': paper_bytes,
            'paper_pdf_pages': pages,
            'manifest_sha256': digest_file(root / 'bundle' / 'manifest.json'),
            'public_research_assets': len(assets['entries']),
            'negative_cases': negatives,
            'unapproved_draft_rejected': True,
            'draft_publication_blocked': True, # retained backwards-compatible gate label
            'citation_schema_validated': True,
            'bundle_integrity_verified': True,
            'provisional_bundle_exported': export_to is not None,
            'approved_version': CONFIRMED_VERSION,
            'approved_license': CONFIRMED_LICENSE,
            'author_display_name': CONFIRMED_AUTHOR,
            'approval_basis': 'USER_CONFIRMED_2026_11_13_NOT_INDEPENDENT_ID_VERIFICATION',
            'timestamp_verified': False,
            'release_published': False,
            'author_approved': True,
            'license_granted': True,
            'independent_witness': False,
            'independent_review': False,
            'pdf_matches_markdown': 'NOT_INDEPENDENTLY_PROVEN',
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manuscript', type=Path, default=DEFAULT_MANUSCRIPT)
    parser.add_argument('--paper-pdf', type=Path, required=True,
                        help='Actual typeset PDF of the first paper, not an unrelated synthetic PDF')
    parser.add_argument('--report', type=Path, help='New JSON report path; existing files are never overwritten')
    parser.add_argument('--export-candidate', type=Path,
                        help='Opt-in export of approved-metadata bundle; this does not publish a Release')
    args = parser.parse_args()
    try:
        if args.report and (args.report.exists() or args.report.is_symlink()):
            raise ValueError('report already exists; refusing overwrite')
        result = perform(args.manuscript, args.paper_pdf, export_to=args.export_candidate)
        text = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
        if args.report:
            with args.report.open('x', encoding='utf-8') as stream:
                stream.write(text)
        print(text, end='')
        return 0
    except (OSError, ValueError, UnicodeError, KeyError, yaml.YAMLError, subprocess.TimeoutExpired) as exc:
        print('FAIL: first-paper self-application: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
