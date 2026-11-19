#!/usr/bin/env python3
"""Publish the approved Unjuno/CC-BY-4.0 first paper using owner-authenticated gh.

Default is PLAN_ONLY. --publish creates ONE NEW template-derived paper repo and v1.
--verify-existing rechecks a published version without any remote writes.
It never modifies an existing destination, promotes a software release, changes
branch protection, uploads a private original/key, or claims independent review.
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
import subprocess
import sys
import urllib.parse

from first_paper_selftest import DEFAULT_MANUSCRIPT, ROOT, copy_regular, digest_file, perform
from pilot import GitHub, _files, _get, _same
from preflight import preflight, require_immutable, validate_repository
from research_package import collect
from publication_recovery import require_template_origin, verify_existing, _verify_remote

VERSION = 'v1'


def plan(template: str, repository: str) -> dict:
    validate_repository(template)
    validate_repository(repository)
    if template.lower() == repository.lower():
        raise ValueError('the toolkit cannot be the paper publication destination')
    return {'mode': 'PLAN_ONLY', 'toolkit': template, 'repository': repository,
            'version': VERSION, 'author_display_name': 'Unjuno', 'license': 'CC-BY-4.0',
            'publication_performed': False,
            'requires': ['owner-authenticated gh', 'enabled public template', 'pinned approved PDF', 'independently selected TSA policy'],
            'mutations_when_published': ['create NEW public paper repository from the specified template',
                'enable immutable Releases in NEW repository', 'commit approved public inputs',
                'issue fresh source-bound timestamp', 'publish one immutable v1 preprint'],
            'independent_witness': 'NOT_PERFORMED', 'production_readiness': 'NOT_ESTABLISHED'}


def _stage(paper: Path, source: Path) -> list[str]:
    """Only the approved manuscript's declared scientific files, never a workspace."""
    manuscript = DEFAULT_MANUSCRIPT
    for area in ('data', 'analysis'):
        shutil.copytree(manuscript / area, source / area,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ('preprint.yaml', 'research-assets.yaml'):
        copy_regular(manuscript / name, source / name)
    for name in ('paper.md', 'LICENSE-NOTICE.txt'):
        copy_regular(manuscript / name, source / 'supplements' / name)
    copy_regular(paper, source / 'paper' / 'paper.pdf')
    research = collect(source)
    if research is None or len(research[0]) != 7:
        raise ValueError('first paper must contain exactly seven approved public inputs')
    names = ['preprint.yaml', 'research-assets.yaml', 'paper/paper.pdf', *research[2]]
    (source / 'README.md').write_text(
        '# OpenPreprint Kit — first technical report\n\n'
        'Author display name: Unjuno. Manuscript: CC BY 4.0. Unreviewed preprint.\n'
        'The paper PDF and source Markdown are CC-BY-4.0; analysis code and engineering data retain MIT. '
        'See supplements/LICENSE-NOTICE.txt and research-assets.yaml for per-file rights.\n\n'
        'Recompute the fixed baseline: `python analysis/summarize_ci.py`. '
        'Use the versioned Release assets, not this editable README, for verification.\n'
        'Verification tools: https://github.com/Unjuno/openpreprint-kit\n'
        'Timestamps do not prove authorship, scientific truth, first publication, or peer review.\n',
        encoding='utf-8')
    return sorted([*names, 'README.md'])


def _commit_inputs(gateway, repository: str, source: Path, names: list[str]) -> str:
    repo = gateway.api('GET', 'repos/' + repository)
    branch = repo.get('default_branch')
    if not isinstance(branch, str) or not branch:
        raise ValueError('default branch is unknown')
    ref = urllib.parse.quote(branch, safe='')
    parent = gateway.api('GET', f'repos/{repository}/git/ref/heads/{ref}')['object']['sha']
    old = gateway.api('GET', f'repos/{repository}/git/commits/{parent}')
    entries = []
    for name in names:
        path = source / name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(source.resolve()):
            raise ValueError('unsafe publication input')
        blob = gateway.api('POST', f'repos/{repository}/git/blobs', {
            'encoding': 'base64', 'content': base64.b64encode(path.read_bytes()).decode('ascii')})
        entries.append({'path': name, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
    tree = gateway.api('POST', f'repos/{repository}/git/trees', {'base_tree': old['tree']['sha'], 'tree': entries})
    commit = gateway.api('POST', f'repos/{repository}/git/commits', {
        'message': 'paper: approved Unjuno / CC BY 4.0 v1 with reproducible data',
        'tree': tree['sha'], 'parents': [parent]})['sha']
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('invalid publication commit')
    gateway.api('PATCH', f'repos/{repository}/git/refs/heads/{ref}', {'sha': commit, 'force': False})
    if gateway.api('GET', f'repos/{repository}/git/ref/heads/{ref}')['object']['sha'] != commit:
        raise ValueError('publication source branch changed')
    return commit



def execute(template: str, repository: str, paper: Path, paper_sha256: str,
            policy_path: Path, output: Path, *, gateway=None) -> dict:
    plan(template, repository)
    if output.exists() or output.is_symlink() or output.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('output must be new and outside the toolkit repository')
    if paper.is_symlink() or not paper.is_file():
        raise ValueError('paper must be a regular non-symlink PDF')
    if not re.fullmatch(r'[0-9a-f]{64}', paper_sha256) or digest_file(paper) != paper_sha256:
        raise ValueError('paper fingerprint does not match the independently retained SHA-256')
    from acceptance import run
    from observation import download_bundle
    from preserve import pack, restore
    from timestamp import attach, load_policy, make_query, post_query
    from verify_evidence import verify_all
    policy = load_policy(policy_path)
    gateway = gateway or GitHub()
    gateway.tools()
    source_repo = gateway.api('GET', 'repos/' + template)
    require_template_origin(source_repo, template)
    if gateway.api('GET', 'repos/' + repository, allow_missing=True) is not None:
        raise ValueError('destination already exists; refusing to modify it')
    output.mkdir(parents=True)
    report = {'schema_version': 1, 'status': 'RUNNING', 'state': 'LOCAL_CHECKS',
              'repository': repository, 'version': VERSION, 'synthetic_only': False,
              'author_display_name': 'Unjuno', 'license': 'CC-BY-4.0',
              'paper_sha256': paper_sha256, 'rollback_performed': False,
              'independent_witness': 'NOT_PERFORMED', 'independent_security_review': 'NOT_PERFORMED',
              'production_readiness': 'NOT_ESTABLISHED', 'first_publication': 'NOT_PROVEN'}

    def journal():
        temp = output / '.publication-report.tmp'
        temp.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
        os.replace(temp, output / 'publication-report.json')

    journal()
    try:
        selftest = perform(DEFAULT_MANUSCRIPT, paper)
        if not selftest['author_approved'] or not selftest['license_granted']:
            raise ValueError('approved author/license declaration was not verified')
        (output / 'local-selftest.json').write_text(json.dumps(selftest, indent=2) + '\n', encoding='utf-8')
        source = output / 'source'
        source.mkdir()
        names = _stage(paper, source)
        if digest_file(source / 'paper' / 'paper.pdf') != paper_sha256:
            raise ValueError('paper fingerprint changed during staging')
        # From here a partial error may leave public source or a public Release.
        report['state'] = 'REPOSITORY_CREATION_REQUESTED'; journal()
        gateway.command(['repo', 'create', repository, '--public', '--template', template,
                         '--description', 'OpenPreprint Kit technical report: Unjuno, CC BY 4.0, unreviewed'])
        report['state'] = 'REPOSITORY_CREATED'; journal()
        created = gateway.api('GET', 'repos/' + repository)
        if (created.get('private') is not False or created.get('permissions', {}).get('admin') is not True
                or created.get('full_name', '').lower() != repository.lower()):
            raise ValueError('new paper repository identity/administration not confirmed')
        origin = created.get('template_repository')
        if not isinstance(origin, dict) or origin.get('full_name', '').lower() != template.lower():
            raise ValueError('new repository template origin does not match the requested toolkit')
        report.update(template_repository=template, template_origin_verified=True)
        journal()
        gateway.api('PUT', f'repos/{repository}/immutable-releases')
        require_immutable(_get(gateway, repository))
        commit = _commit_inputs(gateway, repository, source, names)
        report.update(state='SOURCE_COMMITTED', source_commit=commit); journal()
        shutil.copytree(ROOT / 'scripts', source / 'scripts', ignore=shutil.ignore_patterns('__pycache__'))
        bundle = output / 'bundle'
        run(source / 'scripts/prepare_release.py', '--output', bundle, '--repository', repository, '--commit', commit)
        run(ROOT / 'scripts/citation_validation.py', bundle)
        preflight(repository, VERSION, commit, _get(gateway, repository))
        query = make_query(bundle, policy)
        attach(bundle, query, post_query(policy['tsa_url'], query, policy['timeout_seconds']), policy)
        verify_all(bundle, policy_path, repository, VERSION, 'existence', expected_paper_sha256=paper_sha256)
        report['state'] = 'TIMESTAMP_VERIFIED'; journal()
        gateway.command(['release', 'create', VERSION, *map(str, sorted(bundle.iterdir())),
                         '--repo', repository, '--draft', '--target', commit, '--latest=false',
                         '--title', 'OpenPreprint Kit — paper v1 (unreviewed)',
                         '--notes-file', str(bundle / 'RELEASE_NOTES.md')])
        report['state'] = 'DRAFT_CREATED'; journal()
        downloaded = output / 'draft-download'
        gateway.command(['release', 'download', VERSION, '--repo', repository, '--dir', str(downloaded)])
        _same(bundle, downloaded)
        verify_all(downloaded, policy_path, repository, VERSION, 'existence', expected_paper_sha256=paper_sha256)
        from source_provenance import verify_source_snapshot
        # The Git commit needs to contain the actual declared paper/data/code,
        # not merely be the tag target. Fail before irreversible publication.
        snapshot = verify_source_snapshot(repository, commit, downloaded,
                                          lambda path: gateway.anonymous_source(repository, commit, path))
        report.update(source_snapshot_prepublication=snapshot)
        journal()
        require_immutable(_get(gateway, repository))
        archive = output / 'first-paper.opk.zip'
        packed = pack(downloaded, archive, policy_path)
        report.update(state='RECOVERY_ARCHIVE_VERIFIED', archive_sha256=packed['archive_sha256'])
        journal()
        report['state'] = 'PROMOTION_REQUESTED'; journal()
        gateway.command(['release', 'edit', VERSION, '--repo', repository, '--draft=false', '--latest=false'])
        report['state'] = 'PUBLIC_VERIFICATION_PENDING'; journal()
        checked = _verify_remote(gateway, repository, downloaded, policy_path, output, paper_sha256, commit)
        restore(archive, output / 'restored', packed['archive_sha256'], policy_path)
        _same(output / 'anonymous-download', output / 'restored' / 'bundle')
        report.update(checked, status='PASS', state='VERIFIED_PUBLIC_PREPRINT',
                      restore_byte_equality=True, archive_sha256=packed['archive_sha256'])
        journal()
        return report
    except Exception as exc:
        report.update(status='FAIL', failure_type=type(exc).__name__,
                      failure='Inspect actual GitHub state and local report; no rollback or deletion was performed.')
        journal()
        raise


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--template', default='Unjuno/openpreprint-kit', help='read-only toolkit origin; never modified')
    p.add_argument('--repository', default='Unjuno/openpreprint-kit-paper')
    p.add_argument('--paper-pdf', type=Path)
    p.add_argument('--paper-sha256')
    p.add_argument('--policy', type=Path)
    p.add_argument('--out', type=Path)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--publish', action='store_true', help='Actually create a NEW public repository and publish v1')
    mode.add_argument('--verify-existing', action='store_true', help='Read-only re-verification of a published v1; never republish')
    p.add_argument('--archive', type=Path, help='Exact preservation ZIP retained before publication')
    p.add_argument('--archive-sha256', help='Independently retained ZIP SHA-256, not a value trusted from inside the ZIP')
    a = p.parse_args()
    try:
        if a.verify_existing:
            if any(v is None for v in (a.archive, a.archive_sha256, a.policy, a.out)):
                raise ValueError('--verify-existing requires --archive, --archive-sha256, --policy and --out')
            result = verify_existing(a.repository, a.archive, a.archive_sha256, a.policy, a.out)
        elif not a.publish:
            if a.archive is not None or a.archive_sha256 is not None:
                raise ValueError('archive arguments require --verify-existing')
            result = plan(a.template, a.repository)
        else:
            if any(v is None for v in (a.paper_pdf, a.paper_sha256, a.policy, a.out)):
                raise ValueError('--publish requires --paper-pdf, --paper-sha256, --policy and --out')
            result = execute(a.template, a.repository, a.paper_pdf, a.paper_sha256, a.policy, a.out)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired) as exc:
        print('FAIL: first-paper publication: ' + str(exc)[:500], file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
