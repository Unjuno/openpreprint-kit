#!/usr/bin/env python3
"""Create/verify local HMAC commitments for confidential records.

NEVER place originals or secret keys inside a public GitHub repository.
The receipt alone is only a commitment; it is NOT a timestamp, clinical validation,
consent proof, identity proof, or protection from deletion. A verifier who receives
an original and its per-record secret can establish a match to an anchored receipt.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = b'OpenPreprint-Kit private record commitment v1\x00'
MAX_BYTES = 100 * 1024 * 1024
ID_RE = re.compile(r'[0-9a-f]{32}\Z', re.ASCII)
HEX_RE = re.compile(r'[0-9a-f]{64}\Z', re.ASCII)
WINDOWS_SYSTEM_SID = 'S-1-5-18'
WINDOWS_ADMINISTRATORS_SID = 'S-1-5-32-544'
WINDOWS_FULL_CONTROL = 2032127  # FILE_ALL_ACCESS / FileSystemRights.FullControl


def _windows_acl_snapshot(path: Path) -> dict:
    """Read a filesystem DACL as SIDs and numeric rights, never localized names."""
    if os.name != 'nt':
        raise ValueError('Windows ACL inspection is only available on Windows')
    powershell = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / 'WindowsPowerShell' / 'v1.0' / 'powershell.exe'
    if not powershell.is_file():
        raise ValueError('Windows ACL inspection runtime is unavailable')
    command = r'''
$ErrorActionPreference = 'Stop'
Import-Module Microsoft.PowerShell.Security -ErrorAction Stop
$path = $env:OPK_ACL_TARGET
$acl = Get-Acl -LiteralPath $path
$sidType = [System.Security.Principal.SecurityIdentifier]
$rules = @($acl.GetAccessRules($true, $true, $sidType) | ForEach-Object {
    [pscustomobject]@{
        sid = $_.IdentityReference.Value
        type = $_.AccessControlType.ToString()
        rights = [int64]$_.FileSystemRights
        inherited = [bool]$_.IsInherited
        inheritance = [int]$_.InheritanceFlags
        propagation = [int]$_.PropagationFlags
    }
})
[pscustomobject]@{
    ownerSid = $acl.GetOwner($sidType).Value
    currentUserSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    protected = [bool]$acl.AreAccessRulesProtected
    rules = $rules
} | ConvertTo-Json -Compress -Depth 5
'''
    module_path = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / 'WindowsPowerShell' / 'v1.0' / 'Modules'
    env = dict(os.environ, OPK_ACL_TARGET=str(path.resolve()), PSModulePath=str(module_path))
    try:
        result = subprocess.run(
            [str(powershell), '-NoProfile', '-NonInteractive', '-Command', command],
            capture_output=True, text=True, encoding='utf-8', errors='strict',
            check=False, timeout=15, env=env,
        )
        if result.returncode != 0 or not result.stdout.strip():
            raise ValueError('cannot inspect Windows security descriptor')
        snapshot = json.loads(result.stdout)
        if not isinstance(snapshot, dict):
            raise ValueError('invalid Windows security descriptor response')
        return snapshot
    except (OSError, subprocess.SubprocessError, UnicodeError, json.JSONDecodeError, TypeError):
        raise ValueError('cannot inspect Windows security descriptor') from None


def _windows_replace_acl(path: Path, sddl: str) -> None:
    """Replace owner and DACL from an explicit descriptor; discard old ACEs."""
    from ctypes import wintypes

    if os.name != 'nt':
        raise ValueError('Windows ACL replacement is only available on Windows')
    advapi = ctypes.WinDLL('advapi32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    descriptor = ctypes.c_void_p()
    convert = advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW
    convert.argtypes = [wintypes.LPCWSTR, wintypes.DWORD,
                        ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.DWORD)]
    convert.restype = wintypes.BOOL
    if not convert(sddl, 1, ctypes.byref(descriptor), None):
        raise OSError(ctypes.get_last_error(), 'cannot build fixture security descriptor')
    try:
        owner = ctypes.c_void_p()
        owner_defaulted = wintypes.BOOL()
        get_owner = advapi.GetSecurityDescriptorOwner
        get_owner.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p),
                              ctypes.POINTER(wintypes.BOOL)]
        get_owner.restype = wintypes.BOOL
        if not get_owner(descriptor, ctypes.byref(owner), ctypes.byref(owner_defaulted)):
            raise OSError(ctypes.get_last_error(), 'cannot read fixture owner SID')
        present = wintypes.BOOL()
        dacl = ctypes.c_void_p()
        defaulted = wintypes.BOOL()
        get_dacl = advapi.GetSecurityDescriptorDacl
        get_dacl.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.BOOL),
                             ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.BOOL)]
        get_dacl.restype = wintypes.BOOL
        if not get_dacl(descriptor, ctypes.byref(present), ctypes.byref(dacl), ctypes.byref(defaulted)) or not present.value:
            raise OSError(ctypes.get_last_error(), 'fixture DACL is absent')
        set_acl = advapi.SetNamedSecurityInfoW
        set_acl.argtypes = [wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD,
                            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        set_acl.restype = wintypes.DWORD
        # SE_FILE_OBJECT, OWNER_SECURITY_INFORMATION, DACL_SECURITY_INFORMATION,
        # PROTECTED_DACL_SECURITY_INFORMATION. No SACL privileges are requested.
        error = set_acl(str(path.resolve()), 1, 0x1 | 0x4 | 0x80000000,
                        owner, None, dacl, None)
        if error:
            raise OSError(error, 'cannot replace fixture owner and DACL')
    finally:
        kernel.LocalFree(descriptor)


def _windows_acl_is_private(snapshot: dict, *, allow_trusted_inheritance: bool = False) -> bool:
    """Accept a protected DACL limited to user, SYSTEM and admins."""
    try:
        user_sid = snapshot['currentUserSid']
        if not isinstance(user_sid, str) or not re.fullmatch(r'S-1-[0-9]+(?:-[0-9]+)+', user_sid):
            return False
        if snapshot['ownerSid'] != user_sid or snapshot['protected'] is not True:
            return False
        rules = snapshot['rules']
        if not isinstance(rules, list) or len(rules) != 3:
            return False
        expected = {user_sid, WINDOWS_SYSTEM_SID, WINDOWS_ADMINISTRATORS_SID}
        observed = set()
        for rule in rules:
            if (not isinstance(rule, dict)
                    or rule.get('sid') not in expected
                    or rule.get('sid') in observed
                    or rule.get('type') != 'Allow'
                    or rule.get('rights') != WINDOWS_FULL_CONTROL
                    or rule.get('inherited') is not False
                    or rule.get('inheritance') not in ((0, 3) if allow_trusted_inheritance else (0,))
                    or rule.get('propagation') != 0):
                return False
            observed.add(rule['sid'])
        return observed == expected
    except (KeyError, TypeError):
        return False


def _require_windows_private_acl(path: Path, *, allow_trusted_inheritance: bool = False) -> dict:
    snapshot = _windows_acl_snapshot(path)
    if not _windows_acl_is_private(snapshot, allow_trusted_inheritance=allow_trusted_inheritance):
        raise ValueError('Windows ACL is unsafe or unknown; use a protected owner/SYSTEM/Administrators-only directory')
    return snapshot


def _write_windows_private_key(path: Path, key: bytes, user_sid: str) -> None:
    """Create a key file atomically with a protected SID-based DACL from byte zero."""
    from ctypes import wintypes

    advapi = ctypes.WinDLL('advapi32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    kernel.FlushFileBuffers.argtypes = [wintypes.HANDLE]
    kernel.FlushFileBuffers.restype = wintypes.BOOL
    descriptor = ctypes.c_void_p()
    sddl = (f'O:{user_sid}G:{user_sid}D:P'
            f'(A;;FA;;;{user_sid})(A;;FA;;;{WINDOWS_SYSTEM_SID})'
            f'(A;;FA;;;{WINDOWS_ADMINISTRATORS_SID})')
    convert = advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW
    convert.argtypes = [wintypes.LPCWSTR, wintypes.DWORD,
                        ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.DWORD)]
    convert.restype = wintypes.BOOL
    if not convert(sddl, 1, ctypes.byref(descriptor), None):
        raise OSError(ctypes.get_last_error(), 'cannot build protected key DACL')

    class SECURITY_ATTRIBUTES(ctypes.Structure):
        _fields_ = [('nLength', wintypes.DWORD), ('lpSecurityDescriptor', ctypes.c_void_p),
                    ('bInheritHandle', wintypes.BOOL)]

    security = SECURITY_ATTRIBUTES(ctypes.sizeof(SECURITY_ATTRIBUTES), descriptor, False)
    create = kernel.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                       ctypes.POINTER(SECURITY_ATTRIBUTES), wintypes.DWORD,
                       wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    handle = create(str(path.resolve()), 0x40000000, 0x00000007, ctypes.byref(security),
                    1, 0x80, None)  # GENERIC_WRITE, CREATE_NEW, FILE_ATTRIBUTE_NORMAL
    if handle == wintypes.HANDLE(-1).value:
        error = ctypes.get_last_error()
        kernel.LocalFree(descriptor)
        raise OSError(error, 'cannot create private key with protected DACL')
    try:
        _require_windows_private_acl(path)
        buffer = ctypes.create_string_buffer(key)
        written = wintypes.DWORD()
        write = kernel.WriteFile
        write.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                          ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
        write.restype = wintypes.BOOL
        if not write(handle, buffer, len(key), ctypes.byref(written), None) or written.value != len(key):
            raise OSError(ctypes.get_last_error(), 'cannot write private key')
        if not kernel.FlushFileBuffers(handle):
            raise OSError(ctypes.get_last_error(), 'cannot flush private key')
    except BaseException:
        kernel.CloseHandle(handle)
        path.unlink(missing_ok=True)
        raise
    else:
        kernel.CloseHandle(handle)
    finally:
        kernel.LocalFree(descriptor)


def commit_file(path: Path, key: bytes) -> str:
    if len(key) != 32 or path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError('invalid private source/key or record size exceeded')
    digester = hmac.new(key, DOMAIN, hashlib.sha256)
    total = 0
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            total += len(block)
            if total > MAX_BYTES:
                raise ValueError('private record exceeded 100 MiB')
            digester.update(block)
    return digester.hexdigest()


def ensure_outside_root(path: Path) -> None:
    if path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('confidential original and secret key MUST remain outside the public repository')


def receipt_data(receipt: Path) -> dict:
    from json import loads
    def no_duplicates(items):
        obj = {}
        for k, v in items:
            if k in obj:
                raise ValueError('duplicate JSON keys in private receipt')
            obj[k] = v
        return obj
    if receipt.is_symlink() or not receipt.is_file() or receipt.stat().st_size > 4096:
        raise ValueError('invalid receipt')
    with receipt.open('r', encoding='utf-8') as handle:
        text = handle.read(4097)  # bounded read even if the file grows after stat()
    if len(text) > 4096:
        raise ValueError('invalid receipt')
    data = loads(text, object_pairs_hook=no_duplicates)
    if (not isinstance(data, dict) or set(data) != {'schema_version', 'record_id', 'algorithm', 'commitment'}
            or type(data['schema_version']) is not int or data['schema_version'] != 1
            or data['algorithm'] != 'HMAC-SHA256'
            or not isinstance(data['record_id'], str) or not ID_RE.fullmatch(data['record_id'])
            or not isinstance(data['commitment'], str) or not HEX_RE.fullmatch(data['commitment'])
            or receipt.name != data['record_id'] + '.json'):
        raise ValueError('malformed or misnamed receipt')
    return data


def seal(source: Path, key_path: Path) -> Path:
    ensure_outside_root(source)
    ensure_outside_root(key_path)
    if key_path.parent.is_symlink() or not key_path.parent.is_dir():
        raise ValueError('secret directory must already exist and must not be a symlink')
    windows_user_sid = None
    if os.name == 'nt':
        # Display names from icacls are localized. Require an exact protected
        # DACL by SID and reject inherited or unrecognized access rules.
        windows_user_sid = _require_windows_private_acl(
            key_path.parent, allow_trusted_inheritance=True)['currentUserSid']
    key = secrets.token_bytes(32)
    commitment = commit_file(source, key)
    rid = secrets.token_hex(16)
    receipt_dir = ROOT / 'evidence' / 'commitments'
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = receipt_dir / (rid + '.json')
    if receipt_path.exists() or key_path.exists() or key_path.is_symlink():
        raise ValueError('receipt or private key already exists; refuse overwrite')
    receipt = {'schema_version': 1, 'record_id': rid,
               'algorithm': 'HMAC-SHA256', 'commitment': commitment}
    fd = None
    try:
        if os.name == 'nt':
            _write_windows_private_key(key_path, key, windows_user_sid)
        else:
            fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
            with os.fdopen(fd, 'wb') as handle:
                fd = None
                handle.write(key)
        with receipt_path.open('x', encoding='utf-8') as handle:
            json.dump(receipt, handle, sort_keys=True, separators=(',', ':'))
            handle.write('\n')
    except BaseException:
        if fd is not None:
            os.close(fd)
        key_path.unlink(missing_ok=True)
        receipt_path.unlink(missing_ok=True)
        raise
    return receipt_path


def verify(source: Path, key_path: Path, receipt_path: Path) -> bool:
    ensure_outside_root(source)
    ensure_outside_root(key_path)
    data = receipt_data(receipt_path)
    if key_path.is_symlink() or not key_path.is_file():
        raise ValueError('private key missing or unsafe')
    if key_path.stat().st_size != 32:
        raise ValueError('private key must be exactly 32 bytes')
    with key_path.open('rb') as handle:
        key = handle.read(33)  # bounded: never materialize an oversized key
    if len(key) != 32:
        raise ValueError('private key must be exactly 32 bytes')
    return hmac.compare_digest(commit_file(source, key), data['commitment'])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('seal')
    p.add_argument('original', type=Path)
    p.add_argument('--key-output', type=Path, required=True)
    p = sub.add_parser('verify')
    p.add_argument('original', type=Path)
    p.add_argument('--key', type=Path, required=True)
    p.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.cmd == 'seal':
            receipt = seal(args.original, args.key_output)
            print('PASS: created public, non-identifying commitment receipt ' + receipt.relative_to(ROOT).as_posix())
            print('Keep the 256-bit per-record key outside GitHub; never upload your confidential original.')
        else:
            if not verify(args.original, args.key, args.receipt):
                print('FAIL: original record does not match sealed commitment', file=sys.stderr)
                return 1
            print('PASS: confidential record matches independently provided key and public receipt')
            print('NOTE: no timestamp was checked; verify the release manifest and RFC 3161 evidence separately.')
        return 0
    except (ValueError, OSError, UnicodeError, TypeError) as exc:
        print('FAIL: confidential record seal/verification rejected: ' + type(exc).__name__, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
