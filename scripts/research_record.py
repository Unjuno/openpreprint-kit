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
KINDS = {'review', 'response', 'correction', 'expression_of_concern', 'retraction',
         'editorial_decision'}
DECISIONS = {'accept', 'revise', 'decline', 'pause'}
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
        if (not isinstance(event, dict) or not EVENT_KEYS.issubset(event)
                or set(event) - EVENT_KEYS - {'replacement', 'round_issue', 'decision'}):
            errors.append(f'{prefix}: missing or unknown fields'); continue
        event_id = event['id']
        if not isinstance(event_id, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', event_id) or event_id in ids:
            errors.append(f'{prefix}: invalid or duplicate id')
        else:
            ids.add(event_id)
        kind = event['kind']
        if not isinstance(kind, str) or kind not in KINDS:
            errors.append(f'{prefix}: unsupported kind')
        round_issue = event.get('round_issue')
        if round_issue is not None:
            if (not isinstance(round_issue, str)
                    or not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/[1-9][0-9]*', round_issue)):
                errors.append(f'{prefix}: round_issue must be a canonical public GitHub issue URL')
            elif kind not in {'review', 'response', 'editorial_decision'}:
                errors.append(f'{prefix}: round_issue is only valid for review-round events')
        decision = event.get('decision')
        if kind == 'editorial_decision':
            if round_issue is None:
                errors.append(f'{prefix}: editorial_decision needs a round_issue')
            if not isinstance(decision, str) or decision not in DECISIONS:
                errors.append(f'{prefix}: editorial_decision needs accept, revise, decline or pause')
        elif 'decision' in event:
            errors.append(f'{prefix}: decision is only valid for editorial_decision')
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
    rounds = {(event.get('version'), event.get('paper_sha256'), event.get('round_issue'))
              for event in data['events'] if isinstance(event, dict)
              and event.get('kind') == 'editorial_decision' and isinstance(event.get('round_issue'), str)}
    for version, digest, round_issue in rounds:
        errors.extend(validate_round(data, version, digest, round_issue))
    return errors


def status_for(data: dict, version: str, digest: str) -> str:
    events = [e for e in data['events'] if e['version'] == version and e['paper_sha256'] == digest]
    kinds = {e['kind'] for e in events}
    for kind, status in (('retraction', 'RETRACTED'), ('expression_of_concern', 'EXPRESSION_OF_CONCERN'),
                         ('correction', 'CORRECTION_RECORDED')):
        if kind in kinds:
            return status
    decisions = [e['decision'] for e in events if e['kind'] == 'editorial_decision']
    if decisions:
        return {'accept': 'EDITORIAL_ACCEPTED', 'revise': 'REVISION_REQUESTED',
                'decline': 'EDITORIAL_DECLINED', 'pause': 'REVIEW_PAUSED'}[decisions[-1]]
    if 'review' in kinds:
        return 'REVIEWS_RECORDED'
    return 'UNREVIEWED_PREPRINT'


def validate_round(data: object, version: str, digest: str, round_issue: str) -> list[str]:
    """Validate a complete, public two-reviewer round without certifying people or science."""
    if (not isinstance(round_issue, str)
            or not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/[1-9][0-9]*', round_issue)):
        return ['round issue must be a canonical public GitHub issue URL']
    if not isinstance(data, dict) or not isinstance(data.get('events'), list):
        return ['invalid research record']
    indexed_events = [(i, e) for i, e in enumerate(data['events']) if isinstance(e, dict)
                      and e.get('version') == version and e.get('paper_sha256') == digest
                      and e.get('round_issue') == round_issue]
    events = [e for _, e in indexed_events]
    reviewers = {e.get('actor') for e in events if e.get('kind') == 'review'
                 and isinstance(e.get('actor'), str) and e['actor'].strip()}
    if len(reviewers) < 2:
        return ['round needs review events from two distinct reviewers']
    response_actors = {e.get('actor') for e in events if e.get('kind') == 'response'
                       and isinstance(e.get('actor'), str) and e['actor'].strip()}
    if not response_actors:
        return ['round needs an author response event']
    if reviewers.intersection(response_actors):
        return ['author response actor must be separate from reviewers']
    decisions = [e for e in events if e.get('kind') == 'editorial_decision']
    if not decisions:
        return ['round needs an editorial decision event']
    final_decision_index = max(i for i, e in indexed_events if e.get('kind') == 'editorial_decision')
    required_event_indexes = [i for i, e in indexed_events if e.get('kind') in {'review', 'response'}]
    if required_event_indexes and final_decision_index < max(required_event_indexes):
        return ['editorial decision must be appended after all included reviews and responses']
    if decisions[-1].get('actor') in reviewers | response_actors:
        return ['editorial decision actor must be separate from reviewers and author responders']
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--record', type=Path, default=Path('reviews/record.json'))
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--round-issue', help='Require a complete collaborative round for this public GitHub Issue URL')
    parser.add_argument('--version', help='Release version to validate with --round-issue')
    parser.add_argument('--paper-sha256', help='Exact PDF SHA-256 to validate with --round-issue')
    args = parser.parse_args()
    try:
        data = read_json(args.root / args.record)
        baseline = read_json(args.baseline) if args.baseline else None
        errors = validate_record(data, args.root, baseline)
        round_summary = None
        if args.round_issue:
            if not args.version or not digest_ok(args.paper_sha256):
                raise ValueError('--round-issue requires --version and --paper-sha256')
            errors.extend(validate_round(data, args.version, args.paper_sha256, args.round_issue))
            matching = [e for e in data['events'] if e.get('version') == args.version
                        and e.get('paper_sha256') == args.paper_sha256
                        and e.get('round_issue') == args.round_issue]
            decisions = [e['decision'] for e in matching if e.get('kind') == 'editorial_decision']
            round_summary = {
                'issue': args.round_issue,
                'version': args.version,
                'paper_sha256': args.paper_sha256,
                'reviewers': len({e['actor'] for e in matching if e.get('kind') == 'review'}),
                'responses': sum(1 for e in matching if e.get('kind') == 'response'),
                'decision': decisions[-1] if decisions else None,
                'human_identity_independence': 'NOT_CRYPTOGRAPHICALLY_VERIFIED',
            }
        if errors:
            raise ValueError('; '.join(errors))
        result = {'status': 'PASS', 'events': len(data['events']),
                  'identities': 'NOT_AUTHENTICATED', 'dates': 'CLAIMED',
                  'peer_review_certification': 'NOT_PROVIDED'}
        if round_summary is not None:
            result['round'] = round_summary
        print(json.dumps(result))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr); return 1


if __name__ == '__main__':
    raise SystemExit(main())
