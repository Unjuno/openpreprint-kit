#!/usr/bin/env python3
"""Read-only exact Git-source byte comparison for a versioned public preprint.

This checks the *actual public source commit*, not merely the Release tag
pointer or a source_claim in the manifest. The SHA-256-bound PDF and each
research file must be readable anonymously at that exact commit and byte-match
what was released. This is NOT evidence of independent operator control or
of the scientific correctness of source files.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import tarfile
import urllib.error
import urllib.parse
import urllib.request

from preflight import validate_repository
from verify_release import verify
from verify_research import MAX_FILES, MAX_SINGLE_BYTES, MAX_TOTAL_BYTES, path_ok

MAX_PUBLIC_FILE = 128 * 1024 * 1024


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('public Git source redirected; refusing an unverified download endpoint')


def _safe_source_path(path: str) -> bool:
    return path == 'paper/paper.pdf' or path_ok(path, private=False) or path_ok(path, private=True)


def fetch_source(repository: str, commit: str, path: str, *, max_bytes: int = MAX_PUBLIC_FILE) -> bytes:
    """Anonymous, no-proxy HTTPS read from a pinned Git commit, with no redirects."""
    validate_repository(repository)
    if not isinstance(commit, str) or re.fullmatch(r'[0-9a-f]{40}', commit) is None:
        raise ValueError('an explicit 40-character source commit is required')
    if not _safe_source_path(path):
        raise ValueError('source path is not a declared public research path')
    if type(max_bytes) is not int or not 0 < max_bytes <= MAX_PUBLIC_FILE:
        raise ValueError('invalid source size limit')
    path_q = urllib.parse.quote(path, safe='/')
    url = f'https://raw.githubusercontent.com/{repository}/{commit}/{path_q}'
    request = urllib.request.Request(url, method='GET', headers={
        'User-Agent': 'OpenPreprint-Kit/source-provenance', 'Accept': 'application/octet-stream'})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=45) as reply:
            if reply.status != 200 or urllib.parse.urlsplit(reply.url).hostname != 'raw.githubusercontent.com':
                raise ValueError('source is not anonymously retrievable from GitHub')
            content = reply.read(max_bytes + 1)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise ValueError('source is missing or GitHub HTTPS retrieval failed') from exc
    if len(content) > max_bytes:
        raise ValueError('source is empty or exceeds the expected size limit')
    return content


def expected_source_files(bundle: Path) -> dict[str, bytes]:
    """Return immutable, already-bundle-validated public paper/data/code bytes."""
    problems = verify(bundle, None)
    if problems:
        raise ValueError('source comparison requires a valid bundle: ' + '; '.join(problems))
    expected: dict[str, bytes] = {'paper/paper.pdf': (bundle / 'paper.pdf').read_bytes()}
    if (bundle / 'research-assets.tar').is_file():
        count = 0
        total = 0
        with tarfile.open(bundle / 'research-assets.tar', mode='r:') as archive:
            for member in archive:
                if (not member.isfile() or not _safe_source_path(member.name)
                        or member.name in expected or not 0 <= member.size <= MAX_SINGLE_BYTES):
                    raise ValueError('unsafe or duplicate research source in archive')
                count += 1
                total += member.size
                if count > MAX_FILES or total > MAX_TOTAL_BYTES:
                    raise ValueError('research source inventory exceeds permitted limits')
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError('research source member cannot be read')
                with stream:
                    content = stream.read(member.size + 1)
                if len(content) != member.size:
                    raise ValueError('research source archive member is incomplete')
                expected[member.name] = content
    return expected


def verify_source_snapshot(repository: str, commit: str, bundle: Path, fetcher) -> dict:
    """Reject a tag pointing at a commit whose published scientific bytes differ."""
    validate_repository(repository)
    if not isinstance(commit, str) or re.fullmatch(r'[0-9a-f]{40}', commit) is None:
        raise ValueError('source snapshot requires a full Git source commit')
    expected = expected_source_files(bundle)
    for path in sorted(expected):
        try:
            received = fetcher(path)
        except (OSError, KeyError) as exc:
            raise ValueError('public Git source missing: ' + path) from exc
        if (not isinstance(received, bytes) or len(received) != len(expected[path])
                or hashlib.sha256(received).digest() != hashlib.sha256(expected[path]).digest()):
            raise ValueError('public Git source byte mismatch: ' + path)
    return {'source_snapshot': 'VERIFIED_PUBLIC_GIT_BYTES', 'source_commit': commit,
            'checked_paths': sorted(expected), 'checked_file_count': len(expected),
            'source_provider': 'ANONYMOUS_GITHUB_RAW_PINNED_COMMIT',
            'independent_operator': 'NOT_PROVEN'}
