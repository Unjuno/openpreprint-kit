#!/usr/bin/env python3
"""Generic OpenPreprint manuscript publisher (v1/v2, new or existing repo).

Reuses the proven primitives from the first-paper flow (Git API commit helper,
release bundle builder, citation/integrity/TSA verifiers, pack/restore) but
takes the manuscript directory, expected author/license/version, destination
repository and policy as explicit arguments. No trust decision is made for you:
the caller must supply the independently computed paper PDF SHA-256 and the
author-approved metadata is required to match that supplied value.

Modes:
  --plan            offline: check inputs only, publish nothing (default)
  --verify-inputs   build a local bundle and validate it without GitHub writes
  --publish         full release flow (new repo or new version on existing repo)

This is the owner-authorized path for G2 releases. It never rewrites an
existing immutable Release, never operates on a repo whose immutable setting
cannot be confirmed, and refuses to publish without an owner-approved policy
and PDF fingerprint.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from acceptance import run
from first_paper_publish import _commit_inputs, require_template_origin
from first_paper_selftest import copy_regular, digest_file, validate_input_tree
from observation import download_bundle
from pdf_validation import inspect_pdf
from pilot import GitHub, _files, _get, _same
from preflight import preflight, require_immutable, validate_repository
from preserve import pack, restore
from publish_first_paper import check_paper as _check_paper_v1  # noqa: F401 (documents v1 pin)
from source_provenance import verify_source_snapshot
from timestamp import attach, load_policy, make_query, post_query
from verify_evidence import verify_all
from verify_release import sha256_file
from yaml_strict import safe_load_unique

VERSION_RE = re.compile(r'^v(?:0|[1-9][0-9]*)(?:\.[0-9]+){0,2}$')
CC_BY_4_0 = 'CC-BY-4.0'
CONFIRMED_AUTHOR = 'Unjuno'


def read_metadata(manuscript: Path, expected: dict) -> dict:
    meta_path = manuscript / 'preprint.yaml'
    metadata = safe_load_unique(meta_path.read_text(encoding='utf-8'))
    required = {'authors', 'license', 'version', 'title', 'abstract'}
    if not isinstance(metadata, dict) or not required <= set(metadata):
        raise ValueError('preprint.yaml missing required keys: ' + ', '.join(sorted(required - set(metadata or {}))))
    if metadata['version'] != expected['version']:
        raise ValueError('version differs from expected')
    if metadata['license'] != CC_BY_4_0:
        raise ValueError('license must be CC-BY-4.0 for this publication')
    if metadata['authors'] != [{'name': CONFIRMED_AUTHOR, 'orcid': None}]:
        raise ValueError('authors differ from owner-approved [Unjuno / no ORCID]')
    if not isinstance(metadata['title'], str) or not metadata['title'].strip():
        raise ValueError('title must be a non-empty string')
    return metadata



def expected_assets_in(stage_dir: Path) -> list[str]:
    assets = safe_load_unique((stage_dir / 'research-assets.yaml').read_text(encoding='utf-8'))
    if not isinstance(assets, dict) or not isinstance(assets.get('public_assets'), list):
        raise ValueError('research-assets.yaml malformed')
    seen, declared = set(), []
    for item in assets['public_assets']:
        if not isinstance(item, dict):
            raise ValueError('public_assets entries must be objects')
        path = item.get('path')
        if not isinstance(path, str) or not path or path.startswith('/') or '..' in Path(path).parts:
            raise ValueError('unsafe asset path: ' + str(path))
        if path in seen:
            raise ValueError('duplicate asset path: ' + path)
        seen.add(path)
        declared.append(path)
    return declared


def validate_assets_in(stage_dir: Path) -> dict:
    names: dict[str, str] = {}
    for item in expected_assets_in(stage_dir):
        cand = stage_dir / item
        if not cand.is_file() or cand.is_symlink():
            raise ValueError('declared asset missing or unsafe: ' + item)
        names[item] = sha256_file(cand)
    return names


def stage(manuscript: Path, paper_pdf: Path, source: Path, metadata: dict) -> tuple[list[str], str]:
    source.mkdir()
    copy_regular(manuscript / 'preprint.yaml', source / 'preprint.yaml')
    copy_regular(manuscript / 'research-assets.yaml', source / 'research-assets.yaml')
    copy_regular(manuscript / 'paper.md', source / 'supplements' / 'paper.md')
    copy_regular(manuscript / 'LICENSE-NOTICE.txt', source / 'supplements' / 'LICENSE-NOTICE.txt')
    copy_regular(paper_pdf, source / 'paper' / 'paper.pdf')
    for area in ('data', 'analysis'):
        shutil.copytree(manuscript / area, source / area,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    title = metadata['title']
    version = metadata['version']
    source.joinpath('README.md').write_text(
        f'# {title}\n\n'
        f'Author: Unjuno. Version: {version}. License: {metadata["license"]}. Unreviewed preprint.\n'
        'Unreviewed; timestamps do not prove authorship, scientific truth, first publication or peer review.\n'
        'Verify the versioned Release assets (manifest.json + SHA256SUMS), not this editable README.\n'
        'Verification tools: https://github.com/Unjuno/openpreprint-kit\n',
        encoding='utf-8')
    names = sorted({'preprint.yaml', 'research-assets.yaml', 'paper/paper.pdf', 'README.md',
                    'supplements/paper.md', 'supplements/LICENSE-NOTICE.txt',
                    *('data/' + p.name for p in (source / 'data').iterdir()),
                    *('analysis/' + p.name for p in (source / 'analysis').iterdir())})
    return names, (source / 'README.md').read_text(encoding='utf-8')


def headline(report: dict) -> dict:
    return {
        'schema_version': 1,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        **report,
    }


def verify_existing_v2_preserved(repository: str, policy_path: Path, output: Path) -> dict:
    """After a new version is published, re-fetch v1 and pin it against what it was."""
    downloaded = output / 'v1-after-v2'
    gateway = GitHub()
    download_bundle(repository, 'v1', downloaded, lambda name: gateway.anonymous(repository, 'v1', name))
    verified = verify_all(downloaded, policy_path, repository, 'v1', 'existence')
    return {'v1': {'anonymous_integrity': 'VERIFIED', 'paper_sha256': verified['paper_sha256'],
                   'manifest_sha256': verified['manifest_sha256']}}


def plan(manuscript: Path, version: str, repository: str, new_repo: bool) -> dict:
    return {'mode': 'PLAN_ONLY', 'repository': repository, 'version': version,
            'new_repo_required': new_repo, 'template': 'Unjuno/openpreprint-kit',
            'publication_performed': False}


def execute(manuscript: Path, version: str, repository: str, new_repo: bool,
            paper_pdf: Path, paper_sha256: str, policy_path: Path, output: Path) -> dict:
    validate_repository(repository)
    if output.exists() or output.is_symlink() or output.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('output must be new and outside the toolkit source tree')
    if paper_pdf.is_symlink() or not paper_pdf.is_file():
        raise ValueError('paper PDF must be a regular non-symlink file')
    if digest_file(paper_pdf) != paper_sha256:
        raise ValueError('paper PDF SHA-256 mismatch against the owner-retained fingerprint')
    output.mkdir(parents=True)
    report = {'schema_version': 1, 'status': 'RUNNING', 'state': 'LOCAL_CHECKS',
              'repository': repository, 'version': version, 'new_repo': new_repo,
              'paper_sha256': paper_sha256,
              'synthetic_only': False, 'first_publication': 'NOT_PROVEN',
              'production_readiness': 'NOT_ESTABLISHED', 'rollback_performed': False}
    journal_path = output / 'publication-report.json'

    def journal():
        temp = journal_path.with_suffix('.tmp')
        temp.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n',
                        encoding='utf-8')
        os.replace(temp, journal_path)

    journal()
    try:
        validate_input_tree(manuscript)
        metadata = read_metadata(manuscript, {'version': version})
        paper_bytes, pages = inspect_pdf(paper_pdf)
        report['paper_pages'] = pages

        policy = load_policy(policy_path)

        # Pre-flight: strictly validate and build the bundle locally BEFORE any
        # GitHub write, so unapproved/unlisted assets are never pushed publicly.
        source = output / 'source'
        names, _ = stage(manuscript, paper_pdf, source, metadata)
        if digest_file(source / 'paper' / 'paper.pdf') != paper_sha256:
            raise ValueError('paper fingerprint changed during staging')
        asset_sha = validate_assets_in(source)
        report['assets'] = asset_sha
        scripts_stage = source / 'scripts'
        shutil.copytree(ROOT / 'scripts', scripts_stage,
                        ignore=shutil.ignore_patterns('__pycache__'))
        pre_bundle = output / 'preflight-bundle'
        run(scripts_stage / 'prepare_release.py', '--output', pre_bundle,
            '--repository', repository, '--commit', '0' * 40)
        run(scripts_stage / 'citation_validation.py', pre_bundle)
        report['preflight'] = 'PASS'; journal()

        gateway = GitHub()
        gateway.tools()
        source_repo = gateway.api('GET', 'repos/Unjuno/openpreprint-kit')
        require_template_origin(source_repo, 'Unjuno/openpreprint-kit')

        existing = gateway.api('GET', 'repos/' + repository, allow_missing=True)
        if new_repo and existing is not None:
            raise ValueError('destination already exists; refusing to overwrite it')
        if not new_repo and existing is None:
            raise ValueError('destination does not exist; use --new-repo to create it')

        if new_repo:
            report['state'] = 'REPOSITORY_CREATION_REQUESTED'; journal()
            gateway.command(['repo', 'create', repository, '--public',
                             '--template', 'Unjuno/openpreprint-kit',
                             '--description', 'OpenPreprint Kit technical report: Unjuno, CC BY 4.0, unreviewed'])
            report['state'] = 'REPOSITORY_CREATED'; journal()
            created = gateway.api('GET', 'repos/' + repository)
            if (created.get('private') is not False or created.get('permissions', {}).get('admin') is not True
                    or created.get('full_name', '').lower() != repository.lower()):
                raise ValueError('new paper repository identity/administration not confirmed')
            origin = created.get('template_repository')
            if not isinstance(origin, dict) or origin.get('full_name', '').lower() != 'unjuno/openpreprint-kit':
                raise ValueError('new repository template origin does not match the requested toolkit')
            report.update(template_origin_verified=True)
            journal()
            gateway.api('PUT', f'repos/{repository}/immutable-releases')
        else:
            have_status = gateway.api('GET', f'repos/{repository}/releases/tags/{version}',
                                      allow_missing=True)
            if have_status is not None:
                raise ValueError('release tag already exists; refusing to overwrite or modify it')

        require_immutable(_get(gateway, repository))

        commit = _commit_inputs(gateway, repository, source, names)
        report.update(state='SOURCE_COMMITTED', source_commit=commit); journal()

        bundle = output / 'bundle'
        run(source / 'scripts/prepare_release.py', '--output', bundle,
            '--repository', repository, '--commit', commit)
        run(ROOT / 'scripts/citation_validation.py', bundle)
        preflight(repository, version, commit, _get(gateway, repository))
        query = make_query(bundle, policy)
        attach(bundle, query, post_query(policy['tsa_url'], query, policy['timeout_seconds']), policy)
        verify_all(bundle, policy_path, repository, version, 'existence',
                   expected_paper_sha256=paper_sha256)
        report['state'] = 'TIMESTAMP_VERIFIED'; journal()

        gateway.command(['release', 'create', version, *map(str, sorted(bundle.iterdir())),
                         '--repo', repository, '--draft', '--target', commit, '--latest=false',
                         '--title', f'OpenPreprint Kit — {version} (unreviewed)',
                         '--notes-file', str(bundle / 'RELEASE_NOTES.md')])
        report['state'] = 'DRAFT_CREATED'; journal()
        downloaded = output / 'draft-download'
        gateway.command(['release', 'download', version, '--repo', repository,
                         '--dir', str(downloaded)])
        _same(bundle, downloaded)
        verify_all(downloaded, policy_path, repository, version, 'existence',
                   expected_paper_sha256=paper_sha256)
        snapshot = verify_source_snapshot(repository, commit, downloaded,
                                          lambda p: gateway.anonymous_source(repository, commit, p))
        report.update(source_snapshot_prepublication=snapshot)
        journal()
        require_immutable(_get(gateway, repository))
        archive_dir = output / 'archives'
        archive_dir.mkdir()
        archive = archive_dir / f'{version.replace("/", "-")}.opk.zip'
        packed = pack(downloaded, archive, policy_path)
        report.update(state='RECOVERY_ARCHIVE_VERIFIED', archive_sha256=packed['archive_sha256'])
        journal()
        report['state'] = 'PROMOTION_REQUESTED'; journal()
        gateway.command(['release', 'edit', version, '--repo', repository,
                         '--draft=false', '--latest=false'])
        report['state'] = 'PUBLIC_VERIFICATION_PENDING'; journal()
        checked = verify_all(downloaded, policy_path, repository, version, 'existence',
                             expected_paper_sha256=paper_sha256)
        restored_dir = output / 'restored'
        restore(archive, restored_dir, packed['archive_sha256'], policy_path)
        _same(downloaded, restored_dir / 'bundle')
        # v1 integrity re-check for the new-repo case keeps both versions pinned
        if version != 'v1':
            report.update(verify_existing_v2_preserved(repository, policy_path, output))
        gateway.command(['release', 'verify', version, '--repo', repository, '--format', 'json'])
        for asset in sorted(bundle.iterdir()):
            gateway.command(['release', 'verify-asset', version, str(asset), '--repo', repository])
        public = output / 'public-download'
        download_bundle(repository, version, public,
                        lambda name: gateway.anonymous(repository, version, name))
        _same(bundle, public)
        verify_all(public, policy_path, repository, version, 'existence',
                   expected_paper_sha256=paper_sha256)
        report.update(status='PASS', state='VERIFIED_PUBLIC_PREPRINT',
                      restore_byte_equality=True,
                      release_url=f'https://github.com/{repository}/releases/tag/{version}',
                      existence_tsa_time_utc=checked.get('existence_tsa_time_utc'))
        journal()
        return report
    except Exception as exc:
        report.update(status='FAIL', failure_type=type(exc).__name__,
                      failure='Inspect actual GitHub state; no rollback was performed.')
        journal()
        raise


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manuscript', type=Path, required=True)
    p.add_argument('--repository', required=True)
    p.add_argument('--version', required=True)
    p.add_argument('--new-repo', action='store_true')
    p.add_argument('--paper-pdf', type=Path)
    p.add_argument('--paper-sha256')
    p.add_argument('--policy', type=Path)
    p.add_argument('--out', type=Path)
    p.add_argument('--plan', action='store_true')
    p.add_argument('--verify-inputs', action='store_true')
    p.add_argument('--publish', action='store_true')
    a = p.parse_args()
    if not VERSION_RE.fullmatch(a.version or ''):
        print('FAIL: invalid --version', file=sys.stderr); return 2
    if not ((a.plan or a.verify_inputs or a.publish) and not (a.verify_inputs and a.publish)):
        print('FAIL: choose exactly one of --plan/--verify-inputs/--publish', file=sys.stderr); return 2
    try:
        if a.plan:
            print(json.dumps(plan(a.manuscript, a.version, a.repository, a.new_repo),
                             ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        if a.verify_inputs or a.publish:
            if any(v is None for v in (a.policy, a.out)):
                raise ValueError('--policy and --out are required for verify/publish')
        paper_pdf = a.paper_pdf or (a.manuscript / 'paper.pdf')
        if a.verify_inputs:
            if paper_pdf.is_symlink() or not paper_pdf.is_file():
                raise ValueError('paper PDF must be regular')
            if a.paper_sha256 and digest_file(paper_pdf) != a.paper_sha256:
                raise ValueError('paper PDF SHA-256 mismatch')
            validate_input_tree(a.manuscript)
            metadata = read_metadata(a.manuscript, {'version': a.version})
            paper_bytes, pages = inspect_pdf(paper_pdf)
            paper_sha = a.paper_sha256 or sha256_file(paper_pdf)
            stage_dir = a.out / 'stage'
            if stage_dir.exists():
                shutil.rmtree(stage_dir)
            names, _ = stage(a.manuscript, paper_pdf, stage_dir, metadata)
            asset_sha = validate_assets_in(stage_dir)
            scripts_out = stage_dir / 'scripts'
            shutil.copytree(ROOT / 'scripts', scripts_out,
                            ignore=shutil.ignore_patterns('__pycache__'))
            bundle = a.out / 'bundle'
            if bundle.exists():
                shutil.rmtree(bundle)
            run(scripts_out / 'prepare_release.py', '--output', bundle,
                '--repository', a.repository, '--commit', '0' * 40)
            run(scripts_out / 'citation_validation.py', bundle)
            print(json.dumps({'status': 'VERIFY_INPUTS_PASS',
                              'repository': a.repository, 'version': a.version,
                              'paper_pdf_sha256': paper_sha, 'pages': pages,
                              'assets': asset_sha,
                              'bundle_files': sorted(p.name for p in bundle.iterdir())},
                             ensure_ascii=False, indent=2))
            return 0
        if not a.paper_sha256:
            raise ValueError('--paper-sha256 is required for --publish (owner-retained fingerprint)')
        result = execute(a.manuscript, a.version, a.repository, a.new_repo,
                         paper_pdf, a.paper_sha256, a.policy, a.out)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get('status') == 'PASS' else 1
    except (OSError, ValueError, RuntimeError, TimeoutError) as exc:
        print('FAIL: ' + str(exc)[:400], file=sys.stderr)
        print('Do not retry an uncertain publication; inspect GitHub state and evidence.',
              file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
