#!/usr/bin/env python3
"""GitHub-only release-asset mirror for an independently pinned OPK custody store.

PLAN: no network or writes. PUBLISH: explicit --apply, authenticated `gh`,
immutable GitHub Release, pre-promotion byte check, and anonymous re-download.
VERIFY: public HTTPS download + out-of-band SHA-256 pins + real RFC 3161 audit.

No claim of independently managed custody, first-publication date, or
survivability of a platform-wide GitHub outage is made by this program.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

from custody import CATALOG_NAME, MAX_CATALOG, MAX_ITEMS, HEX, audit, valid_version
from observation import ControlledRedirect, safe_https, VERSION_RE
from pilot import GitHub as PilotGateway
from preflight import validate_repository
from preserve import MAX_ARCHIVE, restore
from verify_release import sha256_file, unique_object, EXPECTED_FILES, EVIDENCE_FILES, RESEARCH_FILES

RECEIPT_NAME = 'github-mirror-receipt.json'
FORMAT = 'opk-github-mirror-v1'
MAX_RECEIPT = 65536
TAG_RE = re.compile(r'opk-custody-[0-9a-f]{24}\Z', re.ASCII)


def safe_github_url(url: str) -> bool:
    """Never download GitHub evidence from user-supplied arbitrary domains."""
    return safe_https(url)


def snapshot_tag(source: str, catalog_pin: str) -> str:
    key = (source.lower() + '\0' + catalog_pin).encode('utf-8')
    return 'opk-custody-' + hashlib.sha256(key).hexdigest()[:24]


def plan(source: str, mirror: str, catalog_pin: str) -> dict:
    validate_repository(source)
    validate_repository(mirror)
    if source.lower() == mirror.lower():
        raise ValueError('source and mirror repositories must be distinct')
    if not isinstance(catalog_pin, str) or not HEX.fullmatch(catalog_pin):
        raise ValueError('an out-of-band catalog SHA-256 is mandatory')
    return {'status': 'PLAN_ONLY', 'mode': 'PLAN_ONLY', 'github_changes': False,
            'source_repository': source, 'mirror_repository': mirror,
            'tag': snapshot_tag(source, catalog_pin), 'cloud_provider': 'GitHub Releases',
            'next_step': 'publish with --apply, an existing public mirror repository and owner-authenticated gh',
            'operator_independence': 'NOT_PROVEN',
            'github_wide_disaster_recovery': 'NOT_PROVEN',
            'durability': 'NOT_PROVEN'}


def _expected_names(entries: list[dict]) -> set[str]:
    return {CATALOG_NAME, RECEIPT_NAME} | {row['filename'] for row in entries}


def _canonical_json(data: dict) -> bytes:
    return (json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def _receipt(source: str, mirror: str, tag: str, catalog_pin: str, entries: list[dict]) -> dict:
    return {'schema_version': 1, 'format': FORMAT,
            'source_repository': source, 'mirror_repository': mirror,
            'tag': tag, 'catalog_sha256': catalog_pin,
            'archives': [{'filename': row['filename'], 'version': row['version'],
                          'archive_sha256': row['archive_sha256'],
                          'size_bytes': row['size_bytes']} for row in entries],
            'release_immutability': 'REQUIRED', 'operator_independence': 'NOT_PROVEN',
            'durability': 'NOT_PROVEN', 'first_publication': 'NOT_PROVEN',
            'github_wide_disaster_recovery': 'NOT_PROVEN'}


def _read_catalog(store: Path, pin: str, source: str) -> list[dict]:
    catalog_path = store / CATALOG_NAME
    if catalog_path.is_symlink() or not catalog_path.is_file() or catalog_path.stat().st_size > MAX_CATALOG:
        raise ValueError('missing or unsafe custody catalog')
    raw = catalog_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != pin:
        raise ValueError('catalog SHA-256 mismatch with out-of-band value')
    catalog = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
    if not isinstance(catalog, dict) or str(catalog.get('repository', '')).lower() != source.lower():
        raise ValueError('source repository does not match custody catalog')
    entries = catalog.get('entries')
    if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_ITEMS:
        raise ValueError('invalid custody catalog versions')
    for item in entries:
        if not isinstance(item, dict) or not isinstance(item.get('version'), str):
            raise ValueError('malformed custody catalog entry')
        valid_version(item['version'])
        if item.get('filename') != item['version'] + '.opk.zip':
            raise ValueError('unsafe custody archive filename')
    if len({row['version'] for row in entries}) != len(entries):
        raise ValueError('duplicate custody versions')
    return entries


def _readback(gateway, mirror: str, tag: str, expected_names: set[str], *, published: bool) -> dict:
    response = gateway.api('GET', f'repos/{mirror}/releases/tags/{tag}', allow_missing=not published)
    if not isinstance(response, dict):
        raise ValueError('GitHub Release is missing after publication')
    files = response.get('assets')
    if (response.get('tag_name') != tag or response.get('draft') is not (not published)
            or (published and response.get('immutable') is not True)
            or not isinstance(files, list)
            or any(not isinstance(x, dict) or not isinstance(x.get('name'), str) for x in files)
            or {x['name'] for x in files} != expected_names or len(files) != len(expected_names)):
        raise ValueError('GitHub mirror Release immutable status or asset inventory mismatch')
    return response


def _validate_immutable(gateway, mirror: str) -> None:
    result = gateway.api('GET', f'repos/{mirror}/immutable-releases')
    if not isinstance(result, dict) or result.get('enabled') is not True:
        raise ValueError('mirror repository immutable Releases must be enabled')


def _validate_repository(gateway, mirror: str, *, must_admin: bool) -> str:
    repo = gateway.api('GET', 'repos/' + mirror)
    if (not isinstance(repo, dict) or repo.get('private') is not False
            or str(repo.get('full_name', '')).lower() != mirror.lower()):
        raise ValueError('mirror must be the expected public GitHub repository')
    if must_admin and repo.get('permissions', {}).get('admin') is not True:
        raise ValueError('mirror publication requires owner administration rights')
    branch = repo.get('default_branch')
    if not isinstance(branch, str) or not branch or any(c in branch for c in '\r\n'):
        raise ValueError('mirror default branch is invalid')
    return branch


def _compare_files(local: Path, downloaded: Path, expected: set[str]) -> None:
    if {p.name for p in downloaded.iterdir()} != expected:
        raise ValueError('GitHub release assets mismatch (unexpected/missing asset)')
    for name in sorted(expected):
        original = local / name
        replica = downloaded / name
        if replica.is_symlink() or not replica.is_file() or replica.stat().st_size != original.stat().st_size:
            raise ValueError('GitHub release file mismatch: ' + name)
        if sha256_file(replica) != sha256_file(original):
            raise ValueError('GitHub release SHA-256 mismatch: ' + name)


class GitHubGateway(PilotGateway):
    """Authenticated owner writes; public evidence reads have NO credentials."""
    def anonymous(self, repository: str, tag: str, name: str) -> bytes:
        validate_repository(repository)
        is_mirror_tag = TAG_RE.fullmatch(tag) is not None
        is_source_tag = VERSION_RE.fullmatch(tag) is not None and any(
            int(part) for part in tag[1:].split('.'))
        mirror_asset = name in (CATALOG_NAME, RECEIPT_NAME) or re.fullmatch(
            r'v[0-9]+(?:\.[0-9]+){0,2}\.opk\.zip', name, re.ASCII) is not None
        source_asset = name in EXPECTED_FILES | EVIDENCE_FILES | RESEARCH_FILES
        if not ((is_mirror_tag and mirror_asset) or (is_source_tag and source_asset)):
            raise ValueError('invalid public release asset path')
        url = f'https://github.com/{repository}/releases/download/{tag}/{name}'
        if not safe_github_url(url):
            raise ValueError('unsafe public download URL')
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), ControlledRedirect())
        request = urllib.request.Request(url, method='GET', headers={'User-Agent': 'OpenPreprint-Kit/GitHub-mirror'})
        with opener.open(request, timeout=45) as response:
            if response.status != 200 or not safe_github_url(response.url):
                raise ValueError('anonymous public mirror download unavailable')
            cap = MAX_RECEIPT if name == RECEIPT_NAME else MAX_ARCHIVE
            contents = response.read(cap + 1)
        if not 0 < len(contents) <= cap:
            raise ValueError('empty or oversized public mirror asset')
        return contents


class AnonymousGateway(GitHubGateway):
    """Read public repository metadata anonymously, without GitHub CLI auth."""
    def api(self, method: str, path: str, data=None, *, allow_missing: bool = False):
        if method != 'GET' or data is not None or not re.fullmatch(
                r'repos/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+'
                r'(?:/releases/tags/(?:opk-custody-[0-9a-f]{24}|v[0-9]+(?:\.[0-9]+){0,2}))?',
                path, re.ASCII):
            raise ValueError('anonymous verifier supports only public GitHub repository/release GET')
        endpoint = 'https://api.github.com/' + path

        class APIRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                parts = urllib.parse.urlsplit(newurl)
                if (parts.scheme != 'https' or parts.hostname != 'api.github.com'
                        or parts.port not in (None, 443) or parts.username or parts.password):
                    raise ValueError('public metadata redirected outside GitHub API')
                return super().redirect_request(req, fp, code, msg, headers, newurl)

        request = urllib.request.Request(endpoint, method='GET', headers={
            'User-Agent':'OpenPreprint-Kit/anonymous-verifier',
            'Accept':'application/vnd.github+json'})
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}), APIRedirect())
        try:
            with opener.open(request,timeout=30) as response:
                if response.status != 200 or urllib.parse.urlsplit(response.url).hostname != 'api.github.com':
                    raise ValueError('unexpected anonymous GitHub API response')
                raw=response.read(2*1024*1024+1)
        except urllib.error.HTTPError as exc:
            if exc.code == 404 and allow_missing:
                return None
            raise ValueError('GitHub public metadata request failed (HTTP ' + str(exc.code) + ')') from exc
        if not 0 < len(raw) <= 2*1024*1024:
            raise ValueError('public GitHub API response is empty or too large')
        result=json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
        if not isinstance(result, dict):
            raise ValueError('GitHub public metadata must be JSON object')
        return result


def _validate_receipt(contents: bytes, source: str, mirror: str, tag: str,
                      catalog_pin: str, entries: list[dict]) -> None:
    if not 0 < len(contents) <= MAX_RECEIPT:
        raise ValueError('invalid mirror receipt length')
    received = json.loads(contents, object_pairs_hook=unique_object)
    if received != _receipt(source, mirror, tag, catalog_pin, entries):
        raise ValueError('mirror receipt source or version identity mismatch')


def _check_remote(gateway, source: str, mirror: str, tag: str, catalog_pin: str,
                  receipt_pin: str, policy: Path, downloaded: Path) -> dict:
    if not isinstance(receipt_pin, str) or not HEX.fullmatch(receipt_pin):
        raise ValueError('out-of-band mirror receipt SHA-256 is mandatory')
    _validate_repository(gateway, mirror, must_admin=False)
    # The public Release itself, not the admin-only settings endpoint, must be immutable.
    receipt_bytes = gateway.anonymous(mirror, tag, RECEIPT_NAME)
    if not isinstance(receipt_bytes, bytes) or hashlib.sha256(receipt_bytes).hexdigest() != receipt_pin:
        raise ValueError('mirror receipt SHA-256 does not match out-of-band pin')
    if not downloaded.parent.is_dir():
        raise ValueError('mirror destination parent does not exist')
    downloaded.mkdir()
    (downloaded / RECEIPT_NAME).write_bytes(receipt_bytes)
    (downloaded / CATALOG_NAME).write_bytes(gateway.anonymous(mirror, tag, CATALOG_NAME))
    entries = _read_catalog(downloaded, catalog_pin, source)
    expected = _expected_names(entries)
    _readback(gateway, mirror, tag, expected, published=True)
    _validate_receipt(receipt_bytes, source, mirror, tag, catalog_pin, entries)
    if len(entries) > MAX_ITEMS:
        raise ValueError('too many mirrored files')
    for item in entries:
        filename = item['filename']
        contents = gateway.anonymous(mirror, tag, filename)
        if not isinstance(contents, bytes) or not 0 < len(contents) <= MAX_ARCHIVE:
            raise ValueError('empty or oversized public archive: ' + filename)
        if len(contents) != item['size_bytes'] or hashlib.sha256(contents).hexdigest() != item['archive_sha256']:
            raise ValueError('GitHub archive SHA-256 mismatch: ' + filename)
        (downloaded / filename).write_bytes(contents)
    # Don't allow an extra local file (secret) to pass custody.audit().
    if {x.name for x in downloaded.iterdir()} != expected:
        raise ValueError('extra or missing GitHub mirror file')
    # Existing custody audit must run on exactly the expected custody set.
    receipt = downloaded / RECEIPT_NAME
    receipt.unlink()
    try:
        report = audit(source, downloaded, catalog_pin, policy)
    finally:
        receipt.write_bytes(receipt_bytes)
    return report


def _verify_public_source(gateway, source: str, storage: Path,
                          entries: list[dict], policy: Path, *,
                          verify_attestations: bool = True) -> None:
    """Require each archived version to be an actual immutable public source Release.

    An offline, self-consistent custody archive does not by itself prove that
    its contents were ever anonymously available from the claimed GitHub repo.
    """
    # Anonymous source checks validate public bytes, NOT Sigstore attestations.
    info = gateway.api('GET', f'repos/{source}')
    if (not isinstance(info, dict) or info.get('private') is not False
            or str(info.get('full_name','')).lower() != source.lower()):
        raise ValueError('source Release repository must be public and match expected identity')
    with tempfile.TemporaryDirectory(prefix='.opk-source-check-') as tempdir:
        base=Path(tempdir)
        for item in entries:
            version=item['version']
            release=gateway.api('GET',f'repos/{source}/releases/tags/{version}',allow_missing=True)
            if (not isinstance(release,dict) or release.get('tag_name')!=version
                    or release.get('draft') is not False or release.get('immutable') is not True):
                raise ValueError('source Release must exist and be public and immutable: ' + version)
            restored=base/version
            restore(storage/item['filename'],restored,item['archive_sha256'],policy)
            bundle=restored/'bundle'
            files=sorted(bundle.iterdir())
            names={p.name for p in files}
            listed=release.get('assets')
            if (not isinstance(listed,list) or len(listed)!=len(names)
                    or any(not isinstance(a,dict) or not isinstance(a.get('name'),str) for a in listed)
                    or {a['name'] for a in listed} != names):
                raise ValueError('source Release asset inventory mismatch: '+version)
            if verify_attestations:
                gateway.command(['release','verify',version,'--repo',source,'--format','json'])
            for item_path in files:
                if item_path.is_symlink() or not item_path.is_file():
                    raise ValueError('unsafe source Release bundle file')
                actual=gateway.anonymous(source,version,item_path.name)
                expected_size=item_path.stat().st_size
                if (not isinstance(actual,bytes) or len(actual)!=expected_size
                        or hashlib.sha256(actual).hexdigest()!=sha256_file(item_path)):
                    raise ValueError('source Release asset mismatch: '+version+'/'+item_path.name)
                if verify_attestations:
                    gateway.command(['release','verify-asset',version,str(item_path),'--repo',source])


def publish(source: str, mirror: str, storage: Path, catalog_pin: str,
            policy: Path, output: Path, gateway=None) -> dict:
    layout = plan(source, mirror, catalog_pin)
    if output.exists() or output.is_symlink():
        raise ValueError('mirror journal destination already exists')
    if not output.parent.is_dir() or output.parent.is_symlink():
        raise ValueError('mirror journal parent must be an existing directory')
    # Do not start GitHub changes before complete real RFC 3161 validation.
    result = audit(source, storage, catalog_pin, policy)
    entries = _read_catalog(storage, catalog_pin, source)
    tag = layout['tag']
    gateway = gateway or GitHubGateway()
    gateway.tools()
    branch = _validate_repository(gateway, mirror, must_admin=True)
    _validate_immutable(gateway, mirror)
    path = f'repos/{mirror}/releases/tags/{tag}'
    if gateway.api('GET', path, allow_missing=True) is not None:
        raise ValueError('mirror Release already exists; no overwriting is allowed')
    if gateway.api('GET', f'repos/{mirror}/git/ref/tags/{tag}', allow_missing=True) is not None:
        raise ValueError('mirror tag already exists; no overwriting is allowed')
    head = gateway.api('GET',f'repos/{mirror}/git/ref/heads/{urllib.parse.quote(branch, safe="")}')
    sha = head.get('object', {}).get('sha') if isinstance(head, dict) else None
    if not isinstance(sha, str) or re.fullmatch(r'[0-9a-f]{40}\Z', sha) is None:
        raise ValueError('mirror default branch SHA unavailable')
    # Source publication and its GitHub attestation must already exist.
    # This occurs before ANY mirror Release publication.
    _verify_public_source(gateway,source,storage,entries,policy)

    output.mkdir()
    report = {'status': 'RUNNING', 'stage': 'PREPARED', 'source_repository':source,
              'mirror_repository':mirror, 'tag':tag, 'archive_count':len(entries),
              'rollback':'NOT_PERFORMED', 'operator_independence':'NOT_PROVEN',
              'durability':'NOT_PROVEN', 'github_wide_disaster_recovery':'NOT_PROVEN'}

    def journal():
        destination=output/'mirror-report.json'
        temp=output/'.report.tmp'
        temp.write_bytes(_canonical_json(report))
        os.replace(temp,destination)

    journal()
    try:
        with tempfile.TemporaryDirectory(prefix='.opk-github-mirror-',dir=output) as tempdir:
            base=Path(tempdir)
            upload=base/'upload'
            upload.mkdir()
            receipt_bytes=_canonical_json(_receipt(source,mirror,tag,catalog_pin,entries))
            (upload / RECEIPT_NAME).write_bytes(receipt_bytes)
            for name in [CATALOG_NAME]+[e['filename'] for e in entries]:
                p=storage/name
                if p.is_symlink() or not p.is_file():
                    raise ValueError('missing or symlinked source evidence')
                shutil.copyfile(p,upload/name)
            expected=_expected_names(entries)
            if {p.name for p in upload.iterdir()} != expected:
                raise ValueError('unexpected source evidence')
            _validate_immutable(gateway, mirror)
            gateway.command(['release','create',tag,*[str(upload/n) for n in sorted(expected)],
                            '--repo',mirror,'--draft','--prerelease','--latest=false',
                            '--target',sha,'--title','OpenPreprint evidence mirror '+tag,
                            '--notes','Content integrity proof requires out-of-band SHA-256 and an independent TSA policy.'])
            report['stage']='DRAFT_CREATED'; journal()
            downloaded=base/'draft-download'
            gateway.command(['release','download',tag,'--repo',mirror,'--dir',str(downloaded)])
            _compare_files(upload,downloaded,expected)
            # Require correct draft metadata before irreversible publication.
            _readback(gateway,mirror,tag,expected,published=False)
            _validate_immutable(gateway,mirror)
            report['stage']='PROMOTION_REQUESTED'; journal()
            gateway.command(['release','edit',tag,'--repo',mirror,'--draft=false','--latest=false'])
            report['stage']='PUBLISHED_PENDING_AUDIT';journal()
            _readback(gateway,mirror,tag,expected,published=True)
            gateway.command(['release','verify',tag,'--repo',mirror,'--format','json'])
            for name in sorted(expected):
                gateway.command(['release','verify-asset',tag,str(upload/name),'--repo',mirror])
            report['stage']='PUBLIC_AUDIT';journal()
            public=base/'public'
            public_report=_check_remote(gateway,source,mirror,tag,catalog_pin,
                            hashlib.sha256(receipt_bytes).hexdigest(),policy,public)
            # Verify exact bytes against source, not just an inner self-consistent catalog.
            _compare_files(upload,public,expected)
            if public_report.get('status') != 'PASS':
                raise ValueError('public mirror audit did not PASS')
            report.update(status='PASS',stage='COMPLETE',catalog_sha256=catalog_pin,
                          receipt_sha256=hashlib.sha256(receipt_bytes).hexdigest(),
                          timestamp='VERIFIED_USING_CURRENT_POLICY',
                          remote_attestation='VERIFIED_BY_GITHUB_CLI',
                          url=f'https://github.com/{mirror}/releases/tag/{tag}')
            journal()
    except Exception:
        report['status']='FAIL'
        journal()
        raise
    return report


def verify_mirror(source: str, mirror: str, tag: str, catalog_pin: str,
                  receipt_pin: str, policy: Path, output: Path, gateway=None, *,
                  require_source_release: bool = False) -> dict:
    layout=plan(source,mirror,catalog_pin)
    if tag!=layout['tag']:
        raise ValueError('source repository/catalog and mirror tag identity mismatch')
    if not isinstance(receipt_pin,str) or not HEX.fullmatch(receipt_pin):
        raise ValueError('independent mirror receipt SHA-256 is required')
    if output.exists() or output.is_symlink() or output.parent.is_symlink() or not output.parent.is_dir():
        raise ValueError('mirror audit output must be a new directory with an existing parent')
    gateway=gateway or AnonymousGateway()
    with tempfile.TemporaryDirectory(prefix='.opk-github-retrieval-',dir=output.parent) as tempdir:
        stage=Path(tempdir)/'store'
        result=_check_remote(gateway,source,mirror,tag,catalog_pin,receipt_pin,policy,stage)
        if result.get('status')!='PASS':
            raise ValueError('remote custody audit failed')
        if require_source_release:
            entries = _read_catalog(stage, catalog_pin, source)
            _verify_public_source(gateway, source, stage, entries, policy,
                                  verify_attestations=False)
        if output.exists() or output.is_symlink():
            raise ValueError('mirror audit output appeared concurrently')
        os.rename(stage,output)
    return {'status':'PASS','source_repository':source,'mirror_repository':mirror,'tag':tag,
            'catalog_sha256':catalog_pin,'receipt_sha256':receipt_pin,
            'archive_count':result['archive_count'],'timestamp':result['timestamp'],
            'source_publication': ('PUBLIC_IMMUTABLE_ASSETS_MATCH' if require_source_release
                                   else 'NOT_CHECKED'),
            'github_attestation':'NOT_VERIFIED_BY_ANONYMOUS_MODE',
            'operator_independence':'NOT_PROVEN','durability':'NOT_PROVEN',
            'github_wide_disaster_recovery':'NOT_PROVEN'}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('plan','publish','verify'))
    parser.add_argument('--source',required=True)
    parser.add_argument('--mirror',required=True)
    parser.add_argument('--catalog-sha256',required=True)
    parser.add_argument('--store',type=Path)
    parser.add_argument('--policy',type=Path)
    parser.add_argument('--out',type=Path)
    parser.add_argument('--tag')
    parser.add_argument('--receipt-sha256')
    parser.add_argument('--require-source-release', action='store_true',
                        help='also anonymously verify original immutable Releases and exact assets')
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    try:
        if args.operation=='plan':
            if any((args.store,args.policy,args.out,args.tag,args.receipt_sha256,
                    args.apply,args.require_source_release)):
                raise ValueError('plan requires only source/mirror/catalog SHA-256 and makes no changes')
            result=plan(args.source,args.mirror,args.catalog_sha256)
        elif args.operation=='publish':
            if (not args.apply or args.store is None or args.policy is None or args.out is None
                    or args.tag or args.receipt_sha256 or args.require_source_release):
                raise ValueError('publish requires --apply, --store, --policy and --out')
            result=publish(args.source,args.mirror,args.store,args.catalog_sha256,args.policy,args.out)
        else:
            if not args.tag or not args.receipt_sha256 or args.policy is None or args.out is None or args.apply or args.store:
                raise ValueError('verify requires --tag, --receipt-sha256, --policy and new --out')
            result=verify_mirror(args.source,args.mirror,args.tag,args.catalog_sha256,
                                 args.receipt_sha256,args.policy,args.out,
                                 require_source_release=args.require_source_release)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,RuntimeError,urllib.error.URLError) as exc:
        print(json.dumps({'status':'FAIL','error':str(exc)[:800],
                          'durability':'NOT_PROVEN','operator_independence':'NOT_PROVEN'},sort_keys=True),file=sys.stderr)
        return 1


if __name__=='__main__':
    raise SystemExit(main())
