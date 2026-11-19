#!/usr/bin/env python3
"""Build an opt-in public research data/code archive and anonymous commitment records."""
from __future__ import annotations

from io import BytesIO
import hashlib
import json
from pathlib import Path
import os
import tarfile

import yaml
from yaml_strict import safe_load_unique
from verify_research import (ALLOWED_ROLES, ARCHIVE, CATALOG, ID_RE, MAX_FILES,
                             MAX_SINGLE_BYTES, MAX_TOTAL_BYTES, RELATIONS, path_ok, receipt_ok)

CONFIG = 'research-assets.yaml'


# --- Race-safe file reading ------------------------------------------------
# The previous implementation re-checked containment and then called
# path.read_bytes() as two separate operations, which left a window in which
# an attacker who can swap a parent directory (symlink/junction) for one
# pointing outside the repository could feed us a secret file. We therefore
# read through a single handle whose path is verified against the repository
# DURING the open: POSIX walks the component chain with dir_fd + O_NOFOLLOW;
# Windows opens with CreateFileW and validates the resolved final path via
# GetFinalPathNameByHandleW. If either platform cannot prove containment, we
# fail closed rather than read bytes.


def _escape_report(rel: str) -> ValueError:
    return ValueError('research file escaped repository root (reparse point or symlink): ' + rel)


def _normalize_windows_path(path: str) -> str:
    norm = path.replace('/', '\\')
    lowered = norm.lower()
    if lowered.startswith('\\\\?\\'):
        lowered = lowered[4:]
    if lowered.startswith('\\\\.\\'):
        lowered = lowered[4:]
    while lowered.endswith('\\'):
        lowered = lowered[:-1]
    return lowered


def _windows_read(root: Path, rel: str, max_bytes: int) -> bytes:
    import ctypes
    from ctypes import wintypes

    target = (root / rel.replace('/', '\\')).absolute()
    root_real = _normalize_windows_path(str(root.resolve()))
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    GENERIC_READ = 0x80000000
    FILE_SHARE_READ = FILE_SHARE_WRITE = FILE_SHARE_DELETE = 0x1 | 0x2 | 0x4
    OPEN_EXISTING = 3
    FILE_ATTRIBUTE_NORMAL = 0x80
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000

    handle = k32.CreateFileW(str(target), GENERIC_READ,
                             FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                             None, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, None)
    if handle == wintypes.HANDLE(-1).value:
        raise OSError(ctypes.get_last_error(), 'open failed: ' + rel)
    try:
        buf = ctypes.create_unicode_buffer(32768)
        n = k32.GetFinalPathNameByHandleW(handle, buf, 32768, 0x0)  # 0 = normalized
        if n == 0:
            raise _escape_report(rel)
        final = _normalize_windows_path(buf.value)
        if not final.startswith(root_real + '\\') and final != root_real:
            raise _escape_report(rel)
        remainder = final[len(root_real):].lstrip('\\')
        if remainder.lower() != rel.replace('/', '\\').lower():
            raise _escape_report(rel)
        data = bytearray()
        chunk = ctypes.create_string_buffer(65536)
        read = wintypes.DWORD()
        while True:
            ok = k32.ReadFile(handle, chunk, 65536, ctypes.byref(read), None)
            if not ok:
                raise OSError('read failed: ' + rel)
            if read.value == 0:
                break
            data += chunk.raw[:read.value]
            if len(data) > max_bytes:
                raise ValueError('research file exceeds the permitted byte limit: ' + rel)
        return bytes(data)
    finally:
        k32.CloseHandle(handle)


def _posix_read(root: Path, rel: str, max_bytes: int) -> bytes:
    parts = rel.split('/')
    root_dir = os.open(os.fspath(root), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    fd = root_dir
    root_dir = None
    leaf = None
    try:
        for part in parts[:-1]:
            parent = fd
            fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                         dir_fd=parent)
            os.close(parent)
        leaf = fd
        fd = None
        if not _is_regular(leaf):
            raise OSError('research file is not a regular file: ' + rel)
        data = bytearray()
        while len(data) <= max_bytes:
            chunk = os.read(leaf, 65536)
            if not chunk:
                break
            data += chunk
            if len(data) > max_bytes:
                raise ValueError('research file exceeds the permitted byte limit: ' + rel)
        return bytes(data)
    finally:
        for candidate in (root_dir, fd, leaf):
            if candidate is not None:
                os.close(candidate)


def _is_regular(fd: int) -> bool:
    import stat
    return stat.S_ISREG(os.fstat(fd).st_mode)


def safe_read_bytes(root: Path, rel: str, max_bytes: int = MAX_SINGLE_BYTES) -> bytes:
    if os.name == 'posix':
        return _posix_read(root, rel, max_bytes)
    if os.name == 'nt':
        return _windows_read(root, rel, max_bytes)
    raise OSError('unsupported platform for race-safe research reads')


def path_is_safe(root: Path, rel: str, path: Path) -> bool:
    """Re-check containment at the moment of use.

    A validated path can be replaced by a symlink or a Windows junction at any
    later time. Path.is_symlink() does not report junctions, so resolution and
    an explicit junction check are both required. This is used both by collect()
    and again by create_research() immediately before reading the bytes.
    """
    try:
        root_real = root.resolve()
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root_real):
            return False
        parts = rel.split('/')
        for i in range(1, len(parts)):
            ancestor = root / '/'.join(parts[:i])
            if (ancestor.is_symlink()
                    or getattr(ancestor, 'is_junction', lambda: False)()
                    or not ancestor.resolve().is_relative_to(root_real)):
                return False
        return True
    except (OSError, RuntimeError, ValueError):
        return False


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
        if not path_is_safe(root, asset['path'], path):
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
            data = safe_read_bytes(root, rel, MAX_SINGLE_BYTES)
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
            # Files may change between collect and open. Bind digest to the
            # *archived bytes*, and re-run the FULL containment check (leaf and
            # ancestors, including Windows junctions) at read time. The old
            # leaf-only check let an ancestor be swapped for an out-of-tree
            # link between collect() and create_research().
            filename = entry['path']
            path = files[filename]
            if (not path_ok(filename, private=(entry['role'] == 'private_commitment'))
                    or not path_is_safe(root, filename, path)):
                raise ValueError('research file changed or became unsafe during preparation')
            content = safe_read_bytes(root, filename, MAX_TOTAL_BYTES)
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
