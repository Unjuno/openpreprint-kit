#!/usr/bin/env python3
"""Owner-operated, synthetic-only GitHub publication acceptance.

Default: print a plan, no network or writes. --publish-synthetic creates TWO
new public opk-demo-* repositories and publishes v1/v2 to each. Uses an owner's
already authenticated gh; never exports credentials or reads a real manuscript.
Does not simulate an independent observer, archival custodian, or human review.
Failures leave inspectable drafts/public Releases and a journal; never delete,
force-push, weaken branch rules, or silently overwrite a previous run.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.parse

from preflight import preflight, require_immutable, validate_repository

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = ('v1', 'v2')


def plan(template: str, repositories: list[str]) -> dict:
    validate_repository(template)
    if len(repositories) != 2 or len({r.lower() for r in repositories}) != 2:
        raise ValueError('exactly two distinct new repositories are required')
    for repository in repositories:
        validate_repository(repository)
        if not repository.split('/')[1].startswith('opk-demo-'):
            raise ValueError('synthetic destination names must begin opk-demo-')
        if repository.lower() == template.lower():
            raise ValueError('the template cannot be a destination')
    return {'mode': 'PLAN_ONLY', 'template': template, 'repositories': repositories,
            'versions': list(VERSIONS), 'release_count': 4, 'publication_performed': False,
            'requires': 'Owner-authenticated gh with repository creation, administration and contents rights',
            'mutations_when_opted_in': ['enable template flag if absent', 'create two new public repositories',
                                      'enable release immutability', 'commit synthetic sources', 'publish four synthetic prereleases'],
            'not_performed': ['independent witness', 'offsite custody', 'human peer review', 'security certification']}


class GitHub:
    """Bounded gh adapter. HTTP errors never become false resource absence."""
    def command(self, args: list[str]) -> str:
        result = subprocess.run(['gh', *args], capture_output=True, text=True, timeout=180, check=False,
                                env=dict(os.environ, GH_HOST='github.com', GH_PROMPT_DISABLED='1'))
        if result.returncode:
            raise ValueError('GitHub CLI operation failed; check permissions/network. No automatic rollback.')
        if len(result.stdout) > 2 * 1024 * 1024:
            raise ValueError('GitHub CLI response exceeds bound')
        return result.stdout

    def tools(self) -> None:
        self.command(['--version'])
        self.command(['release', 'verify', '--help'])
        self.command(['release', 'verify-asset', '--help'])

    def api(self, method: str, path: str, data=None, *, allow_missing: bool = False):
        args = ['gh', 'api', '--hostname', 'github.com', '--method', method, '--include', path,
                '-H', 'Accept: application/vnd.github+json', '-H', 'X-GitHub-Api-Version: 2026-03-10']
        if data is not None:
            args += ['--input', '-']
        result = subprocess.run(args, input=json.dumps(data) if data is not None else None,
                                capture_output=True, text=True, timeout=60, check=False)
        if len(result.stdout) > 2 * 1024 * 1024:
            raise ValueError('GitHub API response exceeds bound')
        header, separator, body = result.stdout.replace('\r\n', '\n').partition('\n\n')
        match = re.match(r'HTTP/\S+\s+([0-9]{3})\b', header)
        if not match or not separator:
            raise ValueError('Cannot determine GitHub HTTP status; stopped without guessing')
        status = int(match.group(1))
        if status == 404 and allow_missing and method == 'GET':
            return None
        if not 200 <= status < 300 or result.returncode:
            raise ValueError(f'GitHub {method} failed (HTTP {status}); inspect owner permissions')
        return json.loads(body) if body.strip() else None

    def anonymous_source(self, repository: str, commit: str, path: str) -> bytes:
        from source_provenance import fetch_source
        return fetch_source(repository, commit, path)

    def anonymous(self, repository: str, version: str, name: str) -> bytes:
        from observation import fetch_asset
        return fetch_asset(repository, version, name)


def _get(gateway, repository):
    def read(path):
        data = gateway.api('GET', f'repos/{repository}{path}', allow_missing=True)
        return (404, {}) if data is None else (200, data)
    return read


def _files(folder: Path) -> dict:
    from verify_release import sha256_file
    return {p.name: {'sha256': sha256_file(p), 'size_bytes': p.stat().st_size}
            for p in sorted(folder.iterdir()) if p.is_file() and not p.is_symlink()}


def _same(expected: Path, actual: Path) -> None:
    from verify_release import verify
    errors = verify(actual, None)
    if errors or _files(expected) != _files(actual):
        raise ValueError('downloaded or restored bytes differ from the verified source bundle')


def _commit(gateway, repository: str, source: Path) -> str:
    repo = gateway.api('GET', 'repos/' + repository)
    branch = repo.get('default_branch')
    if not isinstance(branch, str) or not branch:
        raise ValueError('cannot determine default branch')
    ref = urllib.parse.quote(branch, safe='')
    parent = gateway.api('GET', f'repos/{repository}/git/ref/heads/{ref}')['object']['sha']
    old = gateway.api('GET', f'repos/{repository}/git/commits/{parent}')
    entries = []
    # Source is generated locally and explicitly allowlisted by fixture(); never a user directory.
    for path in sorted(source.rglob('*')):
        if path.is_symlink():
            raise ValueError('synthetic source contains an unexpected symlink')
        if not path.is_file():
            continue
        relative = path.relative_to(source).as_posix()
        allowed = relative in {'preprint.yaml', 'research-assets.yaml', 'paper/paper.pdf',
                               'data/synthetic.csv', 'analysis/reproduce.py'}
        allowed |= bool(re.fullmatch(r'evidence/commitments/[A-Za-z0-9_.-]+\.json', relative))
        if not allowed:
            raise ValueError('unexpected synthetic source: ' + relative)
        blob = gateway.api('POST', f'repos/{repository}/git/blobs',
                           {'encoding': 'base64', 'content': base64.b64encode(path.read_bytes()).decode('ascii')})
        entries.append({'path': relative, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
    tree = gateway.api('POST', f'repos/{repository}/git/trees', {'base_tree': old['tree']['sha'], 'tree': entries})
    commit = gateway.api('POST', f'repos/{repository}/git/commits',
                         {'message': 'test: synthetic publication acceptance (NOT RESEARCH)',
                          'tree': tree['sha'], 'parents': [parent]})['sha']
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('invalid source commit')
    gateway.api('PATCH', f'repos/{repository}/git/refs/heads/{ref}', {'sha': commit, 'force': False})
    if gateway.api('GET', f'repos/{repository}/git/ref/heads/{ref}')['object']['sha'] != commit:
        raise ValueError('source branch changed; inspect before retrying')
    return commit


def execute(template: str, repositories: list[str], policy_path: Path, output: Path, *, gateway=None) -> dict:
    plan(template, repositories)
    if output.exists() or output.is_symlink() or output.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('output must be a new directory outside the toolkit repository')
    from acceptance import fixture, run
    from observation import download_bundle
    from timestamp import attach, load_policy, make_query, post_query
    from verify_evidence import verify_all
    policy = load_policy(policy_path)
    gateway = gateway or GitHub()
    report = {'schema_version': 1, 'status': 'RUNNING', 'scope': 'SYNTHETIC_PUBLICATION_ACCEPTANCE',
              'template': template, 'repositories': repositories, 'synthetic_only': True,
              'created_repositories': [], 'releases': [], 'v1_preserved_after_v2': False,
              'independent_witness': 'NOT_PERFORMED', 'offsite_custodian': 'NOT_PERFORMED',
              'human_review': 'NOT_PERFORMED', 'production_readiness': 'NOT_ESTABLISHED'}
    output.mkdir(parents=True)

    def journal():
        temp = output / '.report.tmp'
        temp.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
        os.replace(temp, output / 'pilot-report.json')

    journal()
    try:
        gateway.tools()
        source_repo = gateway.api('GET', 'repos/' + template)
        if source_repo.get('private') is not False or source_repo.get('full_name', '').lower() != template.lower():
            raise ValueError('template must be the expected public repository')
        if not source_repo.get('is_template') and source_repo.get('permissions', {}).get('admin') is not True:
            raise ValueError('template activation requires repository owner administration')
        # Check ALL destination names before making any GitHub change.
        for repository in repositories:
            if gateway.api('GET', 'repos/' + repository, allow_missing=True) is not None:
                raise ValueError('destination already exists; never modify an existing repository: ' + repository)
        if source_repo.get('is_template') is not True:
            gateway.api('PATCH', 'repos/' + template, {'is_template': True})
            if gateway.api('GET', 'repos/' + template).get('is_template') is not True:
                raise ValueError('template setting readback failed')
        for index, repository in enumerate(repositories, start=1):
            gateway.command(['repo', 'create', repository, '--public', '--template', template,
                             '--description', 'OpenPreprint Kit SYNTHETIC acceptance only; not research or clinical data'])
            report['created_repositories'].append(repository); journal()
            current = gateway.api('GET', 'repos/' + repository)
            if (current.get('private') is not False or current.get('full_name', '').lower() != repository.lower()
                    or current.get('permissions', {}).get('admin') is not True
                    or current.get('template_repository', {}).get('full_name', '').lower() != template.lower()):
                raise ValueError('new repository identity, template or administration could not be verified')
            gateway.api('PUT', f'repos/{repository}/immutable-releases')
            require_immutable(_get(gateway, repository))
            prior_source = None
            for version in VERSIONS:
                work = output / f'repository-{index}' / version
                fixture(work, version, export_source=True)
                source = work / 'source'
                if prior_source is not None:
                    for receipt in (prior_source/'evidence/commitments').glob('*.json'):
                        shutil.copy2(receipt, source/'evidence/commitments'/receipt.name)
                commit = _commit(gateway, repository, source)
                # Build from the exact committed public inputs, using trusted local kit code.
                shutil.rmtree(work/'bundle')  # fixture's unbound bundle only; never user content
                shutil.copytree(ROOT/'scripts', source/'scripts', ignore=shutil.ignore_patterns('__pycache__'))
                bundle = work/'bundle'
                run(source/'scripts/prepare_release.py', '--output', bundle, '--repository', repository, '--commit', commit)
                run(ROOT/'scripts/citation_validation.py', bundle)
                preflight(repository, version, commit, _get(gateway, repository))
                query = make_query(bundle, policy)
                attach(bundle, query, post_query(policy['tsa_url'], query, policy['timeout_seconds']), policy)
                verify_all(bundle, policy_path, repository, version, 'existence')
                entry = {'repository': repository, 'version': version, 'source_commit': commit,
                         'state': 'PREPARED', 'anonymous_integrity': 'NOT_CHECKED', 'restore_byte_equality': False}
                report['releases'].append(entry); journal()
                assets = [str(p) for p in sorted(bundle.iterdir())]
                gateway.command(['release', 'create', version, *assets, '--repo', repository, '--draft',
                                 '--target', commit, '--prerelease', '--latest=false',
                                 '--title', 'SYNTHETIC ACCEPTANCE ONLY - '+version, '--notes-file', str(bundle/'RELEASE_NOTES.md')])
                entry['state'] = 'DRAFT_CREATED'; journal()
                downloaded = work/'draft-download'
                gateway.command(['release', 'download', version, '--repo', repository, '--dir', str(downloaded)])
                _same(bundle, downloaded)
                verify_all(downloaded, policy_path, repository, version, 'existence')
                require_immutable(_get(gateway, repository))
                entry['state'] = 'PROMOTION_REQUESTED'; journal()
                gateway.command(['release', 'edit', version, '--repo', repository, '--draft=false', '--latest=false'])
                entry['state'] = 'PUBLIC_VERIFICATION_PENDING'; journal()
                release = gateway.api('GET', f'repos/{repository}/releases/tags/{version}')
                if (release.get('immutable') is not True or release.get('draft') is not False
                        or release.get('tag_name') != version
                        or {a['name'] for a in release.get('assets', [])} != {p.name for p in bundle.iterdir()}):
                    raise ValueError('already public Release failed immutable/asset readback; NO rollback claimed')
                attestation = gateway.command(['release', 'verify', version, '--repo', repository, '--format', 'json'])
                json.loads(attestation)  # Store machine-readable attestation only after CLI verified it.
                (work/'github-release-attestation.json').write_text(attestation, encoding='utf-8')
                for asset in sorted(bundle.iterdir()):
                    gateway.command(['release', 'verify-asset', version, str(asset), '--repo', repository])
                public = work/'anonymous-download'
                download_bundle(repository, version, public, lambda name: gateway.anonymous(repository, version, name))
                _same(bundle, public)
                verified = verify_all(public, policy_path, repository, version, 'existence')
                archive = work/'evidence.opk.zip'
                packed = json.loads(run(ROOT/'scripts/preserve.py', 'pack', public, '--out', archive, '--policy', policy_path))
                run(ROOT/'scripts/preserve.py', 'restore', archive, '--out', work/'restored',
                    '--expected-sha256', packed['archive_sha256'], '--policy', policy_path)
                _same(public, work/'restored'/'bundle')
                entry.update(state='VERIFIED_PUBLIC_SYNTHETIC', anonymous_integrity='VERIFIED',
                             restore_byte_equality=True, archive_sha256=packed['archive_sha256'],
                             archive=str(archive.relative_to(output)), assets=_files(public),
                             timestamp=verified, github_attestation='VERIFIED_BY_GH_CLI',
                             url=f'https://github.com/{repository}/releases/tag/{version}')
                journal(); prior_source=source
            # Check v1 against its previously fixed bytes AFTER v2 exists.
            again = output/f'repository-{index}'/'v1-after-v2'
            download_bundle(repository, 'v1', again, lambda name: gateway.anonymous(repository, 'v1', name))
            _same(output/f'repository-{index}'/'v1'/'bundle', again)
        report.update(status='PASS', v1_preserved_after_v2=True)
        journal()
        return report
    except Exception as exc:
        report['status'] = 'FAIL'
        report['failure_type'] = type(exc).__name__
        report['failure'] = 'Inspect local evidence and actual GitHub state. Never assume a publication was rolled back.'
        journal()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template', required=True)
    parser.add_argument('--repos', nargs=2, required=True, metavar=('OWNER/opk-demo-A', 'OWNER/opk-demo-B'))
    parser.add_argument('--policy', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--publish-synthetic', action='store_true', help='explicitly create two new public repos and four synthetic Releases')
    args = parser.parse_args()
    try:
        report = plan(args.template, args.repos)
        if args.publish_synthetic:
            if args.policy is None or args.out is None:
                raise ValueError('--publish-synthetic requires --policy and --out')
            report = execute(args.template, args.repos, args.policy, args.out)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({'status':'FAIL','error':str(exc)[:1000], 'production_readiness':'NOT_ESTABLISHED'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
