#!/usr/bin/env python3
"""Read-only GitHub publication gates. Requires an Administration:read token.

Only an HTTP 404 means a free release/tag; authorization errors and outages stop
publication. Does not alter GitHub settings or claim an atomic settings lock.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable

MAX_RESPONSE = 1024 * 1024
Get = Callable[[str], tuple[int, object]]


def validate_repository(repository: str) -> None:
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}', repository):
        raise ValueError('repository must be OWNER/REPO, not a URL or path')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('GitHub redirect refused; configure the canonical repository')


def api_client(repository: str) -> Get:
    validate_repository(repository)
    token = os.environ.get('GH_TOKEN', '')
    if not token or any(c.isspace() for c in token):
        raise ValueError('GH_TOKEN must contain a repository-scoped Administration:read credential')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def get(path: str) -> tuple[int, object]:
        request = urllib.request.Request(
            f'https://api.github.com/repos/{repository}{path}',
            headers={'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json',
                     'X-GitHub-Api-Version': '2026-03-10', 'User-Agent': 'OpenPreprint-Kit'},
            method='GET')
        try:
            response = opener.open(request, timeout=30)
        except urllib.error.HTTPError as exc:
            response = exc
        except (urllib.error.URLError, TimeoutError):
            raise ValueError('GitHub API unavailable; publication stopped') from None
        with response:
            status = response.code
            raw = response.read(MAX_RESPONSE + 1)
        if len(raw) > MAX_RESPONSE:
            raise ValueError('GitHub response exceeds size limit')
        try:
            return status, json.loads(raw)
        except (ValueError, UnicodeError):
            raise ValueError(f'GitHub returned invalid JSON (HTTP {status}); publication stopped') from None
    return get


def require_object(get: Get, path: str) -> dict:
    status, data = get(path)
    if status != 200 or not isinstance(data, dict):
        raise ValueError(f'cannot confirm {path or "repository"} (HTTP {status})')
    return data


def require_immutable(get: Get) -> None:
    if require_object(get, '/immutable-releases').get('enabled') is not True:
        raise ValueError('immutable releases are not enabled; publication stopped')


def preflight(repository: str, version: str, commit: str, get: Get) -> dict:
    validate_repository(repository)
    if not re.fullmatch(r'v(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*)){0,2}', version) or not any(int(x) for x in version[1:].split('.')):
        raise ValueError('invalid or draft release version')
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('expected a complete lowercase source commit SHA')
    repo = require_object(get, '')
    if repo.get('private') is not False:
        raise ValueError('repository must be public')
    branch = repo.get('default_branch')
    if not isinstance(branch, str) or not branch:
        raise ValueError('default branch is unknown')
    require_immutable(get)
    head = require_object(get, '/commits/' + urllib.parse.quote(branch, safe=''))
    if head.get('sha') != commit:
        raise ValueError('default branch moved; inspect changes and restart from its current commit')
    for path in (f'/releases/tags/{version}', f'/git/ref/tags/{version}'):
        status, _ = get(path)
        if status != 404:
            raise ValueError(f'version is occupied or cannot be checked (HTTP {status}): {path}')
    return {'status': 'PASS', 'repository': repository, 'version': version,
            'commit': commit, 'immutable': True, 'publication_performed': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--version')
    parser.add_argument('--commit')
    parser.add_argument('--immutable-only', action='store_true')
    args = parser.parse_args()
    try:
        get = api_client(args.repository)
        if args.immutable_only:
            require_immutable(get)
            result = {'status': 'PASS', 'immutable': True, 'publication_performed': False}
        else:
            if args.version is None or args.commit is None:
                raise ValueError('--version and --commit are required')
            result = preflight(args.repository, args.version, args.commit, get)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
