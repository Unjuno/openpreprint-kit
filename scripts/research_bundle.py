#!/usr/bin/env python3
"""Allowlisted research assets and declared provenance; never execute or extract data.

Standard library only. This is not a privacy classifier or a reproducibility claim.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile

RESEARCH_FILES = ('research-manifest.json', 'research-data.zip')
MAX_ITEMS = 100
MAX_JSON = 1024 * 1024
MAX_FILE = 25 * 1024 * 1024
MAX_TOTAL = 100 * 1024 * 1024
SCHEME = 'opk-private-sha256-v1'
ID = re.compile(r'[a-z][a-z0-9_-]{0,63}')
HEX = re.compile(r'[0-9a-f]{64}')
KINDS = {'dataset', 'code', 'protocol', 'environment', 'record', 'supplement'}
COMMON = {'id', 'kind', 'visibility', 'version', 'title', 'description', 'license',
          'sensitivity', 'publication_approved'}
ACTIVITY = {'id', 'inputs', 'outputs', 'code', 'environment', 'command', 'description'}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')


def read_regular(path: Path, limit: int) -> bytes:
    """Bound reads and reject links, devices and files changed during the read."""
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
        raise ValueError('expected a bounded regular non-symlink file')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    with os.fdopen(os.open(path, flags), 'rb') as stream:
        opened = os.fstat(stream.fileno())
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise ValueError('file changed before reading')
        data = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    if (len(data) > limit or len(data) != before.st_size
            or (after.st_size, after.st_mtime_ns) != (before.st_size, before.st_mtime_ns)):
        raise ValueError('file oversized or changed during reading')
    return data


def read_json(path: Path):
    return json.loads(read_regular(path, MAX_JSON), object_pairs_hook=unique_object)


def text_ok(value, limit=4096):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= limit and '\0' not in value


def valid_id(value):
    return isinstance(value, str) and ID.fullmatch(value) is not None and value != 'paper'


def safe_name(value: str) -> None:
    if not isinstance(value, str) or len(value) > 512:
        raise ValueError('invalid relative artifact path')
    parts = value.split('/')
    if not parts or any(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}', p) is None
                        or p in ('.', '..') for p in parts):
        raise ValueError('artifact paths must be plain non-hidden relative POSIX paths')
    if any(p.lower() in {'private', 'secrets', 'health', 'trust'} or
           p.lower().endswith('.opk-private.json') for p in parts):
        raise ValueError('private/trust material cannot be a public artifact')


def source_path(root: Path, relative: str) -> Path:
    safe_name(relative)
    current = root.resolve()
    for part in relative.split('/'):
        current = current / part
        if current.is_symlink():
            raise ValueError('symlink artifact paths are forbidden')
    if not current.resolve().is_relative_to(root.resolve()):
        raise ValueError('artifact path escapes repository')
    return current


def validate_items(artifacts, activities, packaged=False):
    if not isinstance(artifacts, list) or len(artifacts) > MAX_ITEMS:
        raise ValueError('artifacts must be a list of at most 100 entries')
    by_id = {}
    paths = set()
    for item in artifacts:
        if not isinstance(item, dict) or not valid_id(item.get('id')) or item['id'] in by_id:
            raise ValueError('invalid or duplicate artifact id')
        if item.get('visibility') == 'private':
            if (set(item) != {'id', 'kind', 'visibility', 'commitment'} or item['kind'] != 'record'
                    or re.fullmatch(r'pr-[0-9a-f]{32}', item['id']) is None):
                raise ValueError('private records permit only opaque id and commitment; no names or paths')
            c = item['commitment']
            if (not isinstance(c, dict) or set(c) != {'scheme', 'digest'} or c['scheme'] != SCHEME
                    or not isinstance(c['digest'], str) or HEX.fullmatch(c['digest']) is None):
                raise ValueError('invalid private commitment')
        elif item.get('visibility') == 'public':
            extra = {'archive_path', 'sha256', 'size_bytes'} if packaged else {'path'}
            if set(item) != COMMON | extra or item.get('kind') not in KINDS:
                raise ValueError('invalid public artifact fields or kind')
            if item['sensitivity'] != 'non-sensitive' or item['publication_approved'] is not True:
                raise ValueError('public data require explicit non-sensitive classification and publication approval')
            if not all(text_ok(item[key], 4096 if key == 'description' else 256)
                       for key in ('title', 'description', 'version', 'license')):
                raise ValueError('artifact title/description/version/license are required')
            path = item['archive_path' if packaged else 'path']
            safe_name(path)
            if path in paths:
                raise ValueError('duplicate artifact path')
            paths.add(path)
            if packaged:
                if (not path.startswith('artifacts/' + item['id'] + '/') or len(path.split('/')) != 3
                        or not isinstance(item['sha256'], str) or HEX.fullmatch(item['sha256']) is None
                        or type(item['size_bytes']) is not int or not 0 <= item['size_bytes'] <= MAX_FILE):
                    raise ValueError('invalid packaged artifact path/hash/size')
        else:
            raise ValueError('artifact visibility must be public or private')
        by_id[item['id']] = item
    if not isinstance(activities, list) or len(activities) > MAX_ITEMS:
        raise ValueError('activities must be a list of at most 100 entries')
    activity_ids, producers = set(), set()
    edges = {key: set() for key in [*by_id, 'paper']}
    for activity in activities:
        if (not isinstance(activity, dict) or set(activity) != ACTIVITY or not valid_id(activity.get('id'))
                or activity['id'] in activity_ids or activity['id'] in by_id):
            raise ValueError('invalid or duplicate activity id/fields')
        activity_ids.add(activity['id'])
        if not text_ok(activity['command']) or not text_ok(activity['description']):
            raise ValueError('activity command/description must be text (never executed)')
        for role in ('inputs', 'outputs', 'code', 'environment'):
            refs = activity[role]
            if (not isinstance(refs, list) or len(refs) > MAX_ITEMS
                    or not all(isinstance(x, str) for x in refs) or len(set(refs)) != len(refs)):
                raise ValueError('activity references must be unique id lists')
            for ref in refs:
                if ref == 'paper' and role == 'outputs':
                    continue
                if ref not in by_id:
                    raise ValueError('activity references unknown artifact')
                if role in ('code', 'environment') and by_id[ref]['kind'] != role:
                    raise ValueError('activity code/environment reference has the wrong kind')
        if not activity['outputs'] or producers.intersection(activity['outputs']):
            raise ValueError('each output must have one producer and each activity an output')
        producers.update(activity['outputs'])
        for target in activity['outputs']:
            edges[target].update(activity['inputs'] + activity['code'] + activity['environment'])
    seen, active = set(), set()
    def visit(node):
        if node in active:
            raise ValueError('cyclic declared provenance')
        if node in seen:
            return
        active.add(node)
        for parent in edges[node]:
            visit(parent)
        active.remove(node); seen.add(node)
    for node in edges:
        visit(node)


def load_spec(root: Path):
    path = root / 'research.json'
    if not path.exists() and not path.is_symlink():
        return None  # Legacy paper-only repositories.
    spec = read_json(path)
    if (not isinstance(spec, dict) or set(spec) != {'schema_version', 'artifacts', 'activities'}
            or type(spec['schema_version']) is not int or spec['schema_version'] != 1):
        raise ValueError('unsupported research inventory schema')
    validate_items(spec['artifacts'], spec['activities'])
    return spec


def build_research(root: Path, paper_sha256: str, version: str) -> dict[str, bytes]:
    spec = load_spec(root)
    if spec is None:
        return {}
    items, total = [], 0
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_STORED) as archive:
        for original in sorted(spec['artifacts'], key=lambda x: x['id']):
            item = dict(original)
            if item['visibility'] == 'public':
                data = read_regular(source_path(root, item['path']), MAX_FILE)
                total += len(data)
                if total > MAX_TOTAL:
                    raise ValueError('public research data exceed 100 MiB total')
                name = 'artifacts/' + item['id'] + '/' + PurePosixPath(item.pop('path')).name
                item.update(archive_path=name, sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))
                zi = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                zi.create_system = 3; zi.external_attr = (stat.S_IFREG | 0o644) << 16
                archive.writestr(zi, data)
            items.append(item)
    index = dict(schema_version=1, paper_sha256=paper_sha256, paper_version=version,
                 artifacts=items, activities=sorted(spec['activities'], key=lambda x: x['id']),
                 provenance_status='DECLARED_NOT_EXECUTED')
    raw = json_bytes(index)
    if len(raw) > MAX_JSON:
        raise ValueError('research index exceeds 1 MiB')
    return {RESEARCH_FILES[0]: raw, RESEARCH_FILES[1]: buffer.getvalue()}


def verify_research(folder: Path, metadata: dict) -> None:
    index = read_json(folder / RESEARCH_FILES[0])
    if (not isinstance(index, dict) or set(index) != {'schema_version', 'paper_sha256', 'paper_version',
            'artifacts', 'activities', 'provenance_status'} or type(index['schema_version']) is not int
            or index['schema_version'] != 1 or index['provenance_status'] != 'DECLARED_NOT_EXECUTED'):
        raise ValueError('unsupported research index schema')
    if index['paper_sha256'] != metadata.get('paper_sha256') or index['paper_version'] != metadata.get('version'):
        raise ValueError('research index is bound to different paper bytes or version')
    validate_items(index['artifacts'], index['activities'], packaged=True)
    expected = {item['archive_path']: item for item in index['artifacts'] if item['visibility'] == 'public'}
    if sum(item['size_bytes'] for item in expected.values()) > MAX_TOTAL:
        raise ValueError('research data exceed total size limit')
    raw = read_regular(folder / RESEARCH_FILES[1], MAX_TOTAL + MAX_ITEMS * 2048 + 65536)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if len(names) != len(set(names)) or set(names) != set(expected) or archive.comment:
            raise ValueError('ZIP members differ from research inventory')
        for entry in entries:
            mode = stat.S_IFMT(entry.external_attr >> 16)
            if (entry.compress_type != zipfile.ZIP_STORED or entry.flag_bits & 1 or entry.is_dir()
                    or mode not in (0, stat.S_IFREG) or entry.comment or entry.extra
                    or entry.file_size != expected[entry.filename]['size_bytes']
                    or entry.compress_size != entry.file_size):
                raise ValueError('ZIP entry is compressed, encrypted, nonregular or has invalid size')
            with archive.open(entry) as stream:
                data = stream.read(MAX_FILE + 1)
            if len(data) != entry.file_size or hashlib.sha256(data).hexdigest() != expected[entry.filename]['sha256']:
                raise ValueError('research artifact checksum/size mismatch')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        result = build_research(args.root, '0'*64, 'validation-only')
        print('PASS: research inventory and public source files checked; provenance not executed' if result
              else 'NOTE: legacy paper-only repository; no research inventory declared')
        return 0
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr); return 1


if __name__ == '__main__':
    raise SystemExit(main())
