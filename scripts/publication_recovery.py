#!/usr/bin/env python3
"""Read-only verification of already published first-paper evidence.

Never mutates GitHub, renews a timestamp, or silently replaces a pinned archive.
The caller chooses fresh trust policy/CRLs and the independently retained ZIP pin.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re

from pilot import GitHub, _files, _same
from preflight import validate_repository
from verify_release import sha256_file as digest_file

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'v1'


def require_template_origin(repo: dict, template: str) -> None:
    """Read-only precondition; enabling a template remains an owner decision."""
    if (not isinstance(repo, dict) or repo.get('private') is not False
            or repo.get('full_name', '').lower() != template.lower()
            or repo.get('is_template') is not True):
        raise ValueError('expected public template is not enabled; stop before repository creation')


def _release_readback(gateway, repository: str, bundle: Path, commit: str) -> dict:
    repo = gateway.api('GET', 'repos/' + repository)
    if (not isinstance(repo, dict) or repo.get('private') is not False
            or repo.get('full_name', '').lower() != repository.lower()):
        raise ValueError('cannot verify public repository identity')
    release = gateway.api('GET', f'repos/{repository}/releases/tags/{VERSION}')
    if (not isinstance(release, dict) or release.get('immutable') is not True
            or release.get('draft') is not False or release.get('tag_name') != VERSION
            or type(release.get('id')) is not int or release['id'] <= 0):
        raise ValueError('published Release is absent or not immutable')
    assets = release.get('assets')
    if (not isinstance(assets, list) or
            any(not isinstance(a, dict) or not isinstance(a.get('name'), str) for a in assets)):
        raise ValueError('published Release asset inventory is malformed')
    names = [a['name'] for a in assets]
    if len(names) != len(set(names)) or set(names) != set(_files(bundle)):
        raise ValueError('published Release asset inventory does not match the verified archive')
    tag = gateway.api('GET', f'repos/{repository}/git/ref/tags/{VERSION}')
    obj = tag.get('object') if isinstance(tag, dict) else None
    visited = set()
    # Lightweight and bounded annotated tags are supported, never guessed.
    for _ in range(5):
        if not isinstance(obj, dict) or not isinstance(obj.get('sha'), str):
            break
        sha = obj['sha']
        if not re.fullmatch(r'[0-9a-f]{40}', sha) or sha in visited:
            break
        visited.add(sha)
        if obj.get('type') == 'commit':
            if sha == commit:
                return release
            break
        if obj.get('type') != 'tag':
            break
        tag = gateway.api('GET', f'repos/{repository}/git/tags/{sha}')
        obj = tag.get('object') if isinstance(tag, dict) else None
    raise ValueError('published tag target does not match the timestamped source commit')


def _verify_remote(gateway, repository: str, bundle: Path, policy_path: Path,
                   output: Path, paper_sha256: str, commit: str) -> dict:
    from observation import download_bundle
    from verify_evidence import verify_all
    release = _release_readback(gateway, repository, bundle, commit)
    # A tag/manifest may name the right commit while its source bytes differ.
    # Check the actual public PDF/data/code at that immutable commit via an
    # independent anonymous HTTPS retrieval path, before claiming provenance.
    from source_provenance import verify_source_snapshot
    source = verify_source_snapshot(repository, commit, bundle,
                                    lambda path: gateway.anonymous_source(repository, commit, path))
    attestation = gateway.command(['release', 'verify', VERSION, '--repo', repository, '--format', 'json'])
    json.loads(attestation)
    (output / 'github-release-attestation.json').write_text(attestation, encoding='utf-8')
    for asset in sorted(bundle.iterdir()):
        gateway.command(['release', 'verify-asset', VERSION, str(asset), '--repo', repository])
    public = output / 'anonymous-download'
    download_bundle(repository, VERSION, public, lambda name: gateway.anonymous(repository, VERSION, name))
    _same(bundle, public)
    verified = verify_all(public, policy_path, repository, VERSION, 'existence',
                          expected_paper_sha256=paper_sha256)
    return {'release_url': f'https://github.com/{repository}/releases/tag/{VERSION}',
            'release_id': release['id'], 'immutable': True,
            'tag_target_commit': commit, 'source_snapshot': source, 'anonymous_integrity': 'VERIFIED',
            'timestamp': verified, 'github_attestation': 'VERIFIED_BY_GH_CLI',
            'assets': _files(public)}


def verify_existing(repository: str, archive: Path, archive_sha256: str,
                    policy_path: Path, output: Path, *, gateway=None) -> dict:
    """Read-only recovery/periodic check; NEVER create, delete, or reissue anything.

    The archive digest must come from outside the archive. Current TSA policy
    and CRLs are independently supplied, not imported from the recovered ZIP.
    Failed runs keep their own report; subsequent checks use a new output path.
    """
    from preserve import restore
    from verify_evidence import verify_all
    validate_repository(repository)
    if output.exists() or output.is_symlink() or output.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('verification output must be new and outside the toolkit repository')
    output.mkdir(parents=True)
    report = {'schema_version': 1, 'status': 'RUNNING',
              'scope': 'READ_ONLY_PUBLICATION_VERIFICATION', 'repository': repository,
              'version': VERSION, 'publication_performed': False,
              'independent_witness': 'NOT_PERFORMED', 'independent_security_review': 'NOT_PERFORMED',
              'production_readiness': 'NOT_ESTABLISHED', 'first_publication': 'NOT_PROVEN'}
    def journal():
        temp = output / '.verification-report.tmp'
        temp.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
        os.replace(temp, output / 'verification-report.json')
    journal()
    try:
        restored = output / 'restored'
        restore(archive, restored, archive_sha256, policy_path)
        bundle = restored / 'bundle'
        metadata = json.loads((bundle / 'preprint-metadata.json').read_text('utf-8'))
        paper_sha = digest_file(bundle / 'paper.pdf')
        verify_all(bundle, policy_path, repository, VERSION, 'existence', expected_paper_sha256=paper_sha)
        claim = metadata.get('source_claim')
        commit = claim.get('commit') if isinstance(claim, dict) else None
        if not isinstance(commit, str) or not re.fullmatch(r'[0-9a-f]{40}', commit):
            raise ValueError('timestamped source commit is missing or invalid')
        gateway = gateway or GitHub()
        gateway.tools()
        checked = _verify_remote(gateway, repository, bundle, policy_path, output, paper_sha, commit)
        report.update(checked, status='PASS', state='VERIFIED_PUBLIC_PREPRINT',
                      paper_sha256=paper_sha, archive_sha256=archive_sha256,
                      source_commit=commit, restore_byte_equality=True)
        journal()
        return report
    except Exception as exc:
        report.update(status='FAIL', failure_type=type(exc).__name__,
                      failure='Verification failed; no remote mutation or rollback was attempted.')
        journal()
        raise
