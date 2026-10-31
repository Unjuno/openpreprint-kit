#!/usr/bin/env python3
"""Validate append-only human review/correction assertions, not scientific truth.

The trusted baseline must be acquired independently (for CI: the actual base commit).
An owner can rewrite an unanchored repository; neither names nor dates are authenticated.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

EVENT_KEYS = {'id', 'kind', 'version', 'paper_sha256', 'recorded_at', 'actor',
              'conflicts', 'summary', 'evidence'}
KINDS = {'review', 'response', 'correction', 'expression_of_concern', 'retraction'}
MAX_RECORD = 2 * 1024 * 1024
MAX_REPORT = 256 * 1024
HEX = re.compile(r'[0-9a-f]{64}')
VERSION = re.compile(r'v(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*)){0,2}')


def nonblank(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def version_ok(value: object) -> bool:
    return isinstance(value, str) and VERSION.fullmatch(value) is not None and any(int(p) for p in value[1:].split('.'))


def digest_ok(value: object) -> bool:
    return isinstance(value, str) and HEX.fullmatch(value) is not None


def unique(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def read_json(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_RECORD:
        raise ValueError('record must be a regular non-symlink JSON file <= 2 MiB')
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)


def evidence_path(root: Path, name: str) -> Path:
    if not isinstance(name, str) or '\\' in name:
        raise ValueError('invalid evidence path')
    parts = PurePosixPath(name).parts
    if (len(parts) < 3 or parts[:2] != ('reviews', 'evidence') or '..' in parts
            or '.' in parts or str(PurePosixPath(name)) != name):
        raise ValueError('evidence must be below reviews/evidence/')
    candidate = root
    for component in parts:
        candidate = candidate / component
        if candidate.is_symlink():
            raise ValueError('symlink evidence is forbidden')
    if not candidate.resolve().is_relative_to(root.resolve()) or not candidate.is_file():
        raise ValueError('missing or escaped evidence file')
    if candidate.suffix.lower() not in ('.md', '.txt') or candidate.stat().st_size > MAX_REPORT:
        raise ValueError('evidence must be .md/.txt <= 256 KiB')
    return candidate


def validate_record(data: object, root: Path, baseline: object = None) -> list[str]:
    if (not isinstance(data, dict) or set(data) != {'schema_version', 'events'}
            or type(data.get('schema_version')) is not int or data['schema_version'] != 1
            or not isinstance(data.get('events'), list) or len(data['events']) > 1000):
        return ['invalid research-record schema (maximum 1000 events)']
    errors = []
    if baseline is not None:
        if (not isinstance(baseline, dict) or type(baseline.get('schema_version')) is not int
                or baseline.get('schema_version') != 1 or not isinstance(baseline.get('events'), list)):
            errors.append('invalid trusted baseline')
        elif data['events'][:len(baseline['events'])] != baseline['events']:
            errors.append('prior events were deleted, reordered or edited; append a new event instead')
    ids, versions = set(), {}
    for i, event in enumerate(data['events']):
        prefix = f'events[{i}]'
        if not isinstance(event, dict) or not EVENT_KEYS.issubset(event) or set(event) - EVENT_KEYS - {'replacement'}:
            errors.append(f'{prefix}: missing or unknown fields'); continue
        event_id = event['id']
        if not isinstance(event_id, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', event_id) or event_id in ids:
            errors.append(f'{prefix}: invalid or duplicate id')
        else:
            ids.add(event_id)
        kind = event['kind']
        if not isinstance(kind, str) or kind not in KINDS:
            errors.append(f'{prefix}: unsupported kind')
        version, digest = event['version'], event['paper_sha256']
        if not version_ok(version) or not digest_ok(digest):
            errors.append(f'{prefix}: invalid version or paper_sha256')
        else:
            if version in versions and versions[version] != digest:
                errors.append(f'{prefix}: one version cannot identify two different PDFs')
            versions[version] = digest
        for field in ('actor', 'conflicts', 'summary'):
            if not nonblank(event[field]) or len(event[field]) > 10000:
                errors.append(f'{prefix}: {field} is required (maximum 10000 characters)')
        time = event['recorded_at']
        try:
            if not isinstance(time, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', time):
                raise ValueError()
            datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            errors.append(f'{prefix}: recorded_at must be a UTC claimed timestamp ending in Z')
        evidence = event['evidence']
        if not isinstance(evidence, list) or not 1 <= len(evidence) <= 20:
            errors.append(f'{prefix}: 1..20 evidence files required')
        else:
            seen = set()
            for item in evidence:
                try:
                    if not isinstance(item, dict) or set(item) != {'path', 'sha256'} or not digest_ok(item['sha256']):
                        raise ValueError('invalid evidence entry')
                    path = evidence_path(root, item['path'])
                    if item['path'] in seen:
                        raise ValueError('duplicate evidence path')
                    seen.add(item['path'])
                    raw = path.read_bytes()
                    raw.decode('utf-8')
                    if hashlib.sha256(raw).hexdigest() != item['sha256']:
                        raise ValueError('evidence SHA-256 mismatch')
                except (OSError, ValueError, TypeError, UnicodeError) as exc:
                    errors.append(f'{prefix}: {exc}')
        replacement = event.get('replacement')
        if kind == 'correction':
            if (not isinstance(replacement, dict) or set(replacement) != {'version', 'paper_sha256'}
                    or not version_ok(replacement['version']) or replacement['version'] == version
                    or not digest_ok(replacement['paper_sha256'])):
                errors.append(f'{prefix}: correction needs a replacement with a new version and PDF hash')
        elif 'replacement' in event:
            errors.append(f'{prefix}: replacement is only valid for a correction')
    return errors


def status_for(data: dict, version: str, digest: str) -> str:
    kinds = {e['kind'] for e in data['events'] if e['version'] == version and e['paper_sha256'] == digest}
    for kind, status in (('retraction', 'RETRACTED'), ('expression_of_concern', 'EXPRESSION_OF_CONCERN'),
                         ('correction', 'CORRECTION_RECORDED'), ('review', 'REVIEWS_RECORDED')):
        if kind in kinds:
            return status
    return 'UNREVIEWED_PREPRINT'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--record', type=Path, default=Path('reviews/record.json'))
    parser.add_argument('--baseline', type=Path)
    args = parser.parse_args()
    try:
        data = read_json(args.root / args.record)
        baseline = read_json(args.baseline) if args.baseline else None
        errors = validate_record(data, args.root, baseline)
        if errors:
            raise ValueError('; '.join(errors))
        print(json.dumps({'status': 'PASS', 'events': len(data['events']),
                          'identities': 'NOT_AUTHENTICATED', 'dates': 'CLAIMED',
                          'peer_review_certification': 'NOT_PROVIDED'}))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr); return 1


if __name__ == '__main__':
    raise SystemExit(main())
