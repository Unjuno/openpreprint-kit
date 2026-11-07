#!/usr/bin/env python3
"""Build an opt-in public research data/code archive and anonymous commitment records."""
from __future__ import annotations

from io import BytesIO
import hashlib
import json
from pathlib import Path
import tarfile

import yaml
from yaml_strict import safe_load_unique
from verify_research import (ALLOWED_ROLES, ARCHIVE, CATALOG, ID_RE, MAX_FILES,
                             MAX_SINGLE_BYTES, MAX_TOTAL_BYTES, RELATIONS, path_ok, receipt_ok)

CONFIG = 'research-assets.yaml'


def collect(root: Path) -> tuple[list[dict], list[dict], dict[str, Path]] | None:
    cfg_file = root / CONFIG
    receipt_dir = root / 'evidence' / 'commitments'
    if not cfg_file.exists():
        if receipt_dir.exists() and any(receipt_dir.iterdir()):
            raise ValueError('confidential record receipts exist without research-assets.yaml')
        return None
    if cfg_file.is_symlink() or not cfg_file.is_file():
        raise ValueError('research configuration must be a regular file')
    config = safe_load_unique(cfg_file.read_text('utf-8'))
    if (not isinstance(config, dict) or set(config) != {'schema_version', 'public_assets', 'relations'}
            or type(config['schema_version']) is not int or config['schema_version'] != 1
            or not isinstance(config['public_assets'], list) or not isinstance(config['relations'], list)):
        raise ValueError('invalid research-assets.yaml schema')
    entries, files = [], {}
    if len(config['public_assets']) > MAX_FILES:
        raise ValueError('too many research public assets')
    for asset in config['public_assets']:
        if (not isinstance(asset, dict) or set(asset) != {'path', 'role', 'description', 'license', 'public_confirmed'}
                or not path_ok(asset['path']) or asset['role'] not in ALLOWED_ROLES
                or asset['path'].split('/')[0] != ALLOWED_ROLES[asset['role']]):
            raise ValueError('invalid public research asset entry or path')
        if asset['public_confirmed'] is not True:
            raise ValueError('public_confirmed must be explicitly true for each public asset')
        if not all(isinstance(asset[x], str) and asset[x].strip() for x in ('description', 'license')):
            raise ValueError('public asset description and license required')
        if asset['path'] in files:
            raise ValueError('duplicate public asset path')
        path = root / asset['path']
        if (path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve())
                or any((root / '/'.join(asset['path'].split('/')[:i])).is_symlink()
                       for i in range(1, len(asset['path'].split('/'))))):
            raise ValueError('public asset missing or unsafe: ' + asset['path'])
        if path.stat().st_size > MAX_SINGLE_BYTES:
            raise ValueError('public asset exceeds 25 MiB: ' + asset['path'])
        files[asset['path']] = path
        entries.append({k: asset[k] for k in ('path', 'role', 'description', 'license', 'public_confirmed')})
    if receipt_dir.exists():
        if (receipt_dir.is_symlink() or (root / 'evidence').is_symlink()
                or not receipt_dir.is_dir() or not receipt_dir.resolve().is_relative_to(root.resolve())):
            raise ValueError('unsafe receipt directory')
        for receipt in sorted(receipt_dir.iterdir()):
            if receipt.name == 'README.md':
                continue
            rel = receipt.relative_to(root).as_posix()
            if not path_ok(rel, private=True) or not receipt.is_file() or receipt.is_symlink():
                raise ValueError('unsafe private receipt entry')
            data = receipt.read_bytes()
            if not receipt_ok(data, rel):
                raise ValueError('invalid confidential record commitment')
            files[rel] = receipt
            entries.append({'path': rel, 'role': 'private_commitment'})
    # Every file in the public research areas must be explicitly declared.
    # Otherwise a public repository can silently contain untracked scientific inputs.
    for area in ('data', 'analysis', 'supplements'):
        directory = root / area
        if directory.exists():
            if directory.is_symlink() or not directory.is_dir():
                raise ValueError('unsafe public research directory: ' + area)
            for item in directory.rglob('*'):
                if item.is_symlink() or (not item.is_file() and not item.is_dir()):
                    raise ValueError('unsafe research entry: ' + item.name)
                if item.is_file() and item.relative_to(root).as_posix() not in files:
                    raise ValueError('undeclared research file: ' + item.relative_to(root).as_posix())
    if not entries:
        return None
    if len(entries) > MAX_FILES or sum(p.stat().st_size for p in files.values()) > MAX_TOTAL_BYTES:
        raise ValueError('research package exceeds file count or aggregate byte limit')
    public_paths = {e['path'] for e in entries if e['role'] != 'private_commitment'}
    relations = []
    if len(config['relations']) > MAX_FILES:
        raise ValueError('too many research relations')
    for relation in config['relations']:
        if (not isinstance(relation, dict) or set(relation) != {'source', 'target', 'kind'}
                or relation['kind'] not in RELATIONS or relation['source'] not in public_paths
                or relation['target'] not in public_paths):
            raise ValueError('invalid research relationship')
        relations.append(dict(relation))
    if len({(x['source'], x['target'], x['kind']) for x in relations}) != len(relations):
        raise ValueError('duplicate research relationship')
    return sorted(entries, key=lambda x: x['path']), sorted(relations, key=lambda x: (x['source'], x['target'], x['kind'])), files


def create_research(root: Path, output: Path, plan: tuple, paper_sha256: str, version: str) -> None:
    entries, relations, files = plan
    archive = output / ARCHIVE
    total_bytes = 0
    with tarfile.open(archive, mode='w', format=tarfile.USTAR_FORMAT) as tar:
        for entry in entries:
            # Files may change between collect and open. Bind digest to the *archived bytes*.
            filename = entry['path']
            path = files[filename]
            if path.is_symlink() or not path.is_file():
                raise ValueError('research file changed or became symlink during preparation')
            content = path.read_bytes()
            total_bytes += len(content)
            if len(content) > MAX_SINGLE_BYTES or total_bytes > MAX_TOTAL_BYTES:
                raise ValueError('research data byte limit exceeded while building')
            if entry['role'] == 'private_commitment' and not receipt_ok(content, filename):
                raise ValueError('invalid confidential receipt during bundle generation')
            entry['sha256'] = hashlib.sha256(content).hexdigest()
            entry['size_bytes'] = len(content)
            info = tarfile.TarInfo(filename)
            info.size = len(content)
            info.mtime = 0
            info.mode = 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ''
            tar.addfile(info, BytesIO(content))
    catalog = {'schema_version': 1, 'archive': ARCHIVE,
               'paper_sha256': paper_sha256, 'version': version,
               'entries': entries, 'relations': relations}
    (output / CATALOG).write_text(
        json.dumps(catalog, sort_keys=True, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )


def main() -> int:
    import argparse
    import sys
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='validate the declared research inputs without creating a bundle')
    args = parser.parse_args()
    try:
        plan = collect(Path(__file__).resolve().parents[1])
        print('PASS: research catalog validated; assets=' + str(len(plan[0]) if plan else 0))
        print('NOTE: this is not a privacy audit, publication proof, or timestamp')
        return 0
    except (ValueError, OSError, yaml.YAMLError, UnicodeError, TypeError, KeyError) as exc:
        print('FAIL: research catalog validation: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
