#!/usr/bin/env python3
"""Verify the optional research archive without extracting any TAR members.

Standard library only; internal consistency is not authenticity or publication-time proof.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import tarfile

MAX_FILES = 100
MAX_SINGLE_BYTES = 25 * 1024 * 1024
MAX_TOTAL_BYTES = 100 * 1024 * 1024
ARCHIVE = 'research-assets.tar'
CATALOG = 'research-assets.json'
ALLOWED_ROLES = {'dataset': 'data', 'analysis_code': 'analysis',
                 'supplementary': 'supplements', 'protocol': 'supplements'}
RELATIONS = {'analyzes', 'derived_from', 'documents', 'produced_by'}
SHA_RE = re.compile(r'[0-9a-f]{64}\Z', flags=re.ASCII)
ID_RE = re.compile(r'[0-9a-f]{32}\Z', flags=re.ASCII)
PART_RE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z', flags=re.ASCII)


def path_ok(path: object, private: bool = False) -> bool:
    if not isinstance(path, str) or len(path) > 100 or '/' not in path:
        return False
    components = path.split('/')
    if len(components) > 6 or any(not PART_RE.fullmatch(p) or p in {'.', '..'} for p in components):
        return False
    if private:
        return len(components) == 3 and components[:2] == ['evidence', 'commitments'] and bool(ID_RE.fullmatch(components[2][:-5])) and components[2].endswith('.json')
    return components[0] in {'data', 'analysis', 'supplements'}


def unique_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def receipt_ok(blob: bytes, filename: str) -> bool:
    if len(blob) > 4096:
        return False
    try:
        item = json.loads(blob.decode('utf-8'), object_pairs_hook=unique_object)
    except (ValueError, UnicodeError):
        return False
    return (isinstance(item, dict) and set(item) == {'schema_version', 'record_id', 'algorithm', 'commitment'}
            and type(item['schema_version']) is int and item['schema_version'] == 1
            and isinstance(item['record_id'], str) and ID_RE.fullmatch(item['record_id']) is not None
            and filename == f'evidence/commitments/{item["record_id"]}.json'
            and item['algorithm'] == 'HMAC-SHA256'
            and isinstance(item['commitment'], str) and SHA_RE.fullmatch(item['commitment']) is not None)


def verify_research_bundle(folder: Path, paper_sha256: str, version: str) -> list[str]:
    """Compare each regular TAR member and JSON catalog entry; never extract files."""
    errors: list[str] = []
    try:
        catalog = json.loads((folder / CATALOG).read_text('utf-8'), object_pairs_hook=unique_object)
        if not isinstance(catalog, dict) or set(catalog) != {'schema_version', 'archive', 'paper_sha256', 'version', 'entries', 'relations'}:
            return ['invalid research catalog schema']
        if (type(catalog['schema_version']) is not int or catalog['schema_version'] != 1
                or catalog['archive'] != ARCHIVE or catalog['paper_sha256'] != paper_sha256
                or catalog['version'] != version):
            return ['research catalog is not bound to this paper version']
        entries = catalog['entries']
        if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_FILES:
            return ['research catalog must enumerate 1..100 files']
        index = {}
        for entry in entries:
            if not isinstance(entry, dict):
                return ['research entry is not an object']
            role = entry.get('role')
            private = role == 'private_commitment'
            fields = {'path', 'role', 'sha256', 'size_bytes'} if private else {'path', 'role', 'sha256', 'size_bytes', 'description', 'license', 'public_confirmed'}
            if set(entry) != fields or not path_ok(entry.get('path'), private=private):
                return ['invalid research path or entry fields']
            path = entry['path']
            if role not in ALLOWED_ROLES and not private:
                return ['unknown research role']
            if not private and path.split('/')[0] != ALLOWED_ROLES[role]:
                return ['research role/path mismatch']
            if not private and (not all(isinstance(entry[key], str) and entry[key].strip() for key in ('description', 'license'))
                                or entry['public_confirmed'] is not True):
                return ['research public metadata or public confirmation missing']
            if (type(entry['size_bytes']) is not int or not 0 <= entry['size_bytes'] <= MAX_SINGLE_BYTES
                    or not isinstance(entry['sha256'], str) or SHA_RE.fullmatch(entry['sha256']) is None):
                return ['invalid research hash or asset size']
            if path in index:
                return ['duplicate research path']
            index[path] = entry
        if sum(e['size_bytes'] for e in entries) > MAX_TOTAL_BYTES:
            return ['research asset byte limit exceeded']
        if list(index) != sorted(index):
            return ['research catalog is not in canonical path order']
        relations = catalog['relations']
        if not isinstance(relations, list) or len(relations) > MAX_FILES:
            return ['invalid research relations']
        public_paths = {k for k, v in index.items() if v['role'] != 'private_commitment'}
        for relation in relations:
            if (not isinstance(relation, dict) or set(relation) != {'source', 'target', 'kind'}
                    or relation['kind'] not in RELATIONS or relation['source'] not in public_paths
                    or relation['target'] not in public_paths):
                return ['invalid research relationship']
        archive = folder / ARCHIVE
        if archive.is_symlink() or not archive.is_file() or archive.stat().st_size > MAX_TOTAL_BYTES + 1024 * 512:
            return ['oversized or unsafe research archive']
        seen = set()
        with tarfile.open(archive, mode='r:') as tar:
            members = tar.getmembers()
            if len(members) != len(index):
                return ['research TAR contains missing or undeclared entries']
            for member in members:
                name = member.name
                if (name not in index or name in seen or not member.isfile() or member.size != index[name]['size_bytes']):
                    return ['research TAR contains undeclared, duplicate or unsafe member']
                seen.add(name)
                stream = tar.extractfile(member)
                if stream is None:
                    return ['research TAR member could not be read']
                digester = hashlib.sha256()
                private_blob = bytearray() if index[name]['role'] == 'private_commitment' else None
                while True:
                    block = stream.read(1024 * 1024)
                    if not block:
                        break
                    digester.update(block)
                    if private_blob is not None:
                        private_blob.extend(block)
                if digester.hexdigest() != index[name]['sha256']:
                    errors.append(f'research member checksum mismatch: {name}')
                if private_blob is not None and not receipt_ok(bytes(private_blob), name):
                    errors.append('invalid private commitment receipt')
        return errors
    except (OSError, ValueError, UnicodeError, KeyError, TypeError, tarfile.TarError, OverflowError) as exc:
        return [f'invalid research archive or catalog: {type(exc).__name__}']
