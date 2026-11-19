#!/usr/bin/env python3
"""Portable owner-operated entry point for the approved first-paper release.

Runs on CPython 3.10+ without a Unix shell. Default --plan is offline and
side-effect free. Only --publish can create a new public repository/Release.
Actual publication and trust checks remain in first_paper_publish.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import sys
import tempfile
import urllib.request
import venv

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "manuscripts/openpreprint-kit/approved-v1/paper.pdf"
PAPER_SHA256 = "0860b735379fb1b9b223f5d535442dae8421f456d7ae1c6bf6ce8d3141a1b07c"
CA_SHA256 = "2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438"
CA_URL = "https://freetsa.org/files/cacert.pem"
CRL_URL = "https://www.freetsa.org/crl/root_ca.crl"
DESTINATION = "Unjuno/openpreprint-kit-paper"
TEMPLATE = "Unjuno/openpreprint-kit"
MAX_TRUST_BYTES = 1024 * 1024


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("TSA trust download redirected; refusing replacement")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_paper(path: Path = PAPER) -> str:
    if not path.is_file() or path.is_symlink():
        raise ValueError("approved version-controlled PDF is missing or is a symlink")
    actual = sha256(path)
    if actual != PAPER_SHA256:
        raise ValueError("approved PDF SHA-256 mismatch; do not retypeset or substitute the PDF")
    return actual


def venv_python(directory: Path, *, windows: bool | None = None) -> Path:
    if windows is None:
        windows = os.name == "nt"
    return directory / ("Scripts/python.exe" if windows else "bin/python")


def command(args: list[str], *, timeout: int = 180,
            path_prefix: Path | None = None) -> str:
    env = dict(os.environ, GH_HOST="github.com", GH_PROMPT_DISABLED="1")
    # Windows may otherwise decode gh's UTF-8 output using the cp932 locale.
    # Use UTF-8 consistently in this process and its Python descendants.
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    if path_prefix is not None:
        if not path_prefix.is_dir():
            raise ValueError("virtual environment executable directory is missing")
        # Nested citation_validation.py invokes the cffconvert console script
        # by name. Windows venv Scripts/ is not inherited when launching an
        # absolute python.exe without activating the venv. Never edit the
        # caller's process environment or its global PATH.
        env["PATH"] = str(path_prefix) + os.pathsep + env.get("PATH", "")
    try:
        result = subprocess.run(args, cwd=ROOT, env=env, text=True,
                                encoding="utf-8", errors="strict",
                                capture_output=True, timeout=timeout, check=False)
    except FileNotFoundError as exc:
        raise ValueError("required command is unavailable: " + Path(args[0]).name) from exc
    if result.returncode:
        # Never echo CLI output: a tool may accidentally print auth/host details.
        raise ValueError("command failed: " + Path(args[0]).name +
                         f" (exit {result.returncode}); inspect the local environment")
    return result.stdout.strip()


def check_owner_environment() -> None:
    if sys.version_info < (3, 10):
        raise ValueError("CPython 3.10 or newer is required")
    for tool in ("gh", "openssl"):
        if not shutil.which(tool):
            raise ValueError(tool + " must be installed and available on PATH")
    if not command(["openssl", "version"], timeout=15).startswith("OpenSSL 3."):
        raise ValueError("OpenSSL 3 is required (LibreSSL is not accepted)")
    command(["gh", "auth", "status", "--hostname", "github.com"], timeout=30)
    command(["gh", "release", "verify", "--help"], timeout=15)
    command(["gh", "release", "verify-asset", "--help"], timeout=15)
    if command(["gh", "api", "--hostname", "github.com",
                "repos/" + TEMPLATE, "--jq", ".is_template"], timeout=30) != "true":
        raise ValueError("the public toolkit must have Template repository enabled")


def trust_download(url: str, *, expected_sha256: str | None = None) -> bytes:
    if url not in (CA_URL, CRL_URL):
        raise ValueError("unexpected TSA trust URL; no redirects or alternate roots allowed")
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}), NoRedirect(),
        urllib.request.HTTPSHandler(context=context),
    )
    request = urllib.request.Request(url, headers={"User-Agent": "OpenPreprint-Kit"})
    with opener.open(request, timeout=45) as response:
        if response.status != 200 or response.geturl() != url:
            raise ValueError("unexpected TSA trust response")
        data = response.read(MAX_TRUST_BYTES + 1)
    if not data or len(data) > MAX_TRUST_BYTES:
        raise ValueError("empty or oversized TSA trust response")
    if expected_sha256 is not None and hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError("TSA CA fingerprint mismatch; do not accept a replacement CA")
    return data


def create_policy(work: Path) -> Path:
    trust = work / "trust"
    trust.mkdir()
    ca = trust / "ca.pem"
    crl = trust / "crl.pem"
    ca.write_bytes(trust_download(CA_URL, expected_sha256=CA_SHA256))
    crl.write_bytes(trust_download(CRL_URL))
    command(["openssl", "crl", "-in", str(crl), "-noout", "-verify",
             "-CAfile", str(ca)], timeout=30)
    policy = trust / "policy.json"
    policy.write_text(json.dumps({
        "schema_version": 1,
        "tsa_url": "https://freetsa.org/tsr",
        "ca_file": "ca.pem",
        "ca_sha256": CA_SHA256,
        "crl_file": "crl.pem",
        "policy_oid": "1.2.3.4.1",
        "timeout_seconds": 45,
    }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return policy


def allocate_workspace(base: Path | None = None) -> Path:
    """Keep verification evidence in a stable owner directory, never the OS temp cache."""
    root = base if base is not None else Path.home() / "OpenPreprintKitEvidence"
    if root.exists() and (root.is_symlink() or not root.is_dir()):
        raise ValueError("evidence root must be an ordinary directory")
    if root.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("evidence must remain outside the toolkit source repository")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="first-paper-", dir=str(root))).resolve()


def publish() -> int:
    # This order is deliberate: mismatched source cannot trigger auth/network
    # operations or produce a new public repository.
    check_paper()
    check_owner_environment()
    work = allocate_workspace()
    print("Owner evidence directory: " + str(work), flush=True)
    print("Installing hash-locked dependencies in an isolated environment", flush=True)
    environment = work / "venv"
    venv.EnvBuilder(with_pip=True).create(environment)
    python = venv_python(environment)
    if not python.is_file():
        raise ValueError("could not locate the platform-specific venv Python")
    command([str(python), "-m", "pip", "install", "--require-hashes",
             "-r", str(ROOT / "requirements-build.lock")], timeout=600)
    command([str(python), "-m", "pip", "install", "--require-hashes",
             "--no-build-isolation", "-r", str(ROOT / "requirements.lock")], timeout=600)
    print("Downloading independently pinned TSA CA and checking signed CRL", flush=True)
    policy = create_policy(work)
    print("Starting explicit public GitHub publication (no automatic rollback)", flush=True)
    output = work / "publication"
    result = command([str(python), str(ROOT / "scripts/first_paper_publish.py"),
                      "--repository", DESTINATION,
                      "--paper-pdf", str(PAPER),
                      "--paper-sha256", PAPER_SHA256,
                      "--policy", str(policy),
                      "--out", str(output), "--publish"], timeout=1200,
                     path_prefix=python.parent)
    report = json.loads(result)
    if report.get("status") != "PASS" or report.get("state") != "VERIFIED_PUBLIC_PREPRINT":
        raise ValueError("public verification did not return PASS; inspect evidence")
    print(json.dumps({
        "status": "PASS",
        "state": report["state"],
        "repository": DESTINATION,
        "evidence_directory": str(output),
        "independent_review": "NOT_PERFORMED",
        "production_v1": "NOT_ESTABLISHED",
    }, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="offline plan; no writes (default)")
    mode.add_argument("--check-pdf", action="store_true", help="offline approved-byte check only")
    mode.add_argument("--preflight", action="store_true", help="read-only tooling/auth/template check")
    mode.add_argument("--publish", action="store_true", help="create a NEW public paper repo and immutable v1")
    args = parser.parse_args(argv)
    try:
        if args.publish:
            return publish()
        if args.check_pdf:
            print(json.dumps({"status": "PASS", "scope": "APPROVED_PDF_ONLY",
                              "sha256": check_paper()}, indent=2))
        elif args.preflight:
            check_paper()
            check_owner_environment()
            print(json.dumps({"status": "PASS", "scope": "READ_ONLY_OWNER_PREFLIGHT"}, indent=2))
        else:
            print(json.dumps({"mode": "PLAN_ONLY", "platform": sys.platform,
                              "repository": DESTINATION, "version": "v1",
                              "author": "Unjuno", "license": "CC BY 4.0",
                              "publication_performed": False}, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print("FAIL: " + str(exc)[:400], file=sys.stderr)
        print("Do not retry an uncertain publication; inspect its evidence and GitHub state.",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
