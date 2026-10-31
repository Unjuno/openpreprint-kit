#!/usr/bin/env python3
"""RFC 3161 manifest evidence. Trust comes from an independently selected policy.

Requires Python >=3.10, asn1crypto 1.5.1 and OpenSSL 3. No private signing keys.
Certificate validity is checked now AND at token time; CRLs must be current now.
This is not archival signature validation, proof of public access, or authorship.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

try:
    from asn1crypto import tsp
except ImportError:
    raise SystemExit("Install requirements.txt to use RFC 3161 commands")

from verify_release import EVIDENCE_FILES, unique_object, verify

LIMIT = 1024 * 1024
POLICY_KEYS = {"schema_version", "tsa_url", "ca_file", "ca_sha256", "crl_file",
               "policy_oid", "timeout_seconds"}


def read_regular(path: Path, limit: int = LIMIT) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"expected a regular non-symlink file: {path.name}")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if not data or len(data) > limit:
        raise ValueError(f"empty or oversized file: {path.name}")
    return data


def endpoint(url: str) -> None:
    if not isinstance(url, str) or any(c.isspace() for c in url):
        raise ValueError("TSA endpoint must be an HTTPS URL")
    parts = urllib.parse.urlsplit(url)
    if (parts.scheme != "https" or not parts.hostname or parts.username is not None
            or parts.password is not None or parts.fragment or parts.query):
        raise ValueError("TSA endpoint requires HTTPS, without credentials, query or fragment")
    # Accessing port validates it; do not include the URL in an error message.
    try:
        parts.port
    except ValueError:
        raise ValueError("invalid TSA endpoint port") from None


def load_policy(path: Path) -> dict:
    policy = json.loads(read_regular(path, 65536), object_pairs_hook=unique_object)
    if not isinstance(policy, dict) or set(policy) != POLICY_KEYS:
        raise ValueError("timestamp policy must contain exactly the documented keys")
    if type(policy["schema_version"]) is not int or policy["schema_version"] != 1:
        raise ValueError("unsupported timestamp policy schema")
    endpoint(policy["tsa_url"])
    timeout = policy["timeout_seconds"]
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError("timeout_seconds must be an integer in 1..60")
    pin = policy["ca_sha256"]
    if not isinstance(pin, str) or re.fullmatch(r"[0-9a-f]{64}", pin) is None:
        raise ValueError("ca_sha256 must be a separately trusted 64-digit lowercase SHA-256")
    oid = policy["policy_oid"]
    if (not isinstance(oid, str) or len(oid) > 128 or
            not re.fullmatch(r"[012](?:\.(?:0|[1-9][0-9]*)){1,}", oid)):
        raise ValueError("policy_oid must be a numeric object identifier")
    parts = [int(x) for x in oid.split(".")]
    if parts[0] < 2 and parts[1] > 39:
        raise ValueError("invalid policy_oid second component")
    for name in ("ca_file", "crl_file"):
        if not isinstance(policy[name], str) or not policy[name].strip():
            raise ValueError(f"{name} must be a PEM file path")
        policy["_" + name] = read_regular(path.absolute().parent / policy[name])
    if hashlib.sha256(policy["_ca_file"]).hexdigest() != pin:
        raise ValueError("CA bundle SHA-256 does not match the independently trusted pin")
    return policy


def check_bundle(folder: Path) -> None:
    errors = verify(folder, None)
    if errors:
        raise ValueError("; ".join(errors))


def make_query(folder: Path, policy: dict) -> bytes:
    check_bundle(folder)
    return tsp.TimeStampReq({
        "version": "v1",
        "message_imprint": {"hash_algorithm": {"algorithm": "sha256"},
                            "hashed_message": hashlib.sha256(read_regular(folder / "manifest.json")).digest()},
        "req_policy": policy["policy_oid"],
        "nonce": secrets.randbits(128) | (1 << 127),
        "cert_req": True,
    }).dump()


def openssl(args: list[str], timeout: int, env: dict | None = None) -> str:
    result = subprocess.run(["openssl", *args], capture_output=True, text=True,
                            timeout=timeout, check=False, env=env)
    if result.returncode:
        raise ValueError("OpenSSL verification failed: " + result.stderr[-2000:].strip())
    return result.stdout.strip()


def accuracy_us(info) -> int | None:
    accuracy = info["accuracy"].native
    if accuracy is None:
        return None
    total = 0
    for key, scale in (("seconds", 1_000_000), ("millis", 1000), ("micros", 1)):
        value = accuracy[key]
        if value is not None:
            if type(value) is not int or value < 0 or (key != "seconds" and not 1 <= value <= 999):
                raise ValueError("invalid signed TSA accuracy")
            total += value * scale
    return total


def verify_proof(folder: Path, query: bytes, response: bytes, policy: dict) -> dict:
    check_bundle(folder)
    if not 0 < len(query) <= LIMIT or not 0 < len(response) <= LIMIT:
        raise ValueError("empty or oversized timestamp proof")
    try:
        request = tsp.TimeStampReq.load(query, strict=True)
        reply = tsp.TimeStampResp.load(response, strict=True)
        if reply["status"]["status"].native not in ("granted", "granted_with_mods"):
            raise ValueError("TSA did not grant a timestamp")
        token = reply["time_stamp_token"]
        if token["content_type"].native != "signed_data":
            raise ValueError("timestamp must contain CMS SignedData")
        content = token["content"]["encap_content_info"]
        if content["content_type"].native != "tst_info":
            raise ValueError("timestamp must contain TSTInfo")
        info = content["content"].parsed
        digest = hashlib.sha256(read_regular(folder / "manifest.json")).digest()
        for item in (request, info):
            imprint = item["message_imprint"]
            if (item["version"].native != "v1"
                    or imprint["hash_algorithm"]["algorithm"].native != "sha256"
                    or imprint["hashed_message"].native != digest):
                raise ValueError("timestamp imprint does not match the SHA-256 manifest")
        nonce = request["nonce"].native
        if (type(nonce) is not int or nonce.bit_length() != 128
                or info["nonce"].native != nonce or request["cert_req"].native is not True):
            raise ValueError("timestamp request/response nonce or certificate request mismatch")
        if request["req_policy"].native != policy["policy_oid"] or info["policy"].native != policy["policy_oid"]:
            raise ValueError("timestamp policy OID mismatch")
        generated = info["gen_time"].native
        if generated.tzinfo is None or not info["gen_time"].contents.endswith(b"Z"):
            raise ValueError("timestamp generation time must be UTC")
        accuracy = accuracy_us(info)
    except (ValueError, TypeError, KeyError, OverflowError, AttributeError) as exc:
        raise ValueError(f"invalid RFC 3161 evidence: {exc}") from None
    now = datetime.now(timezone.utc)
    if generated > now + timedelta(seconds=300):
        raise ValueError("timestamp is more than 300 seconds ahead of the verifier clock")
    version = openssl(["version"], policy["timeout_seconds"])
    if not version.startswith("OpenSSL 3."):
        raise ValueError("OpenSSL 3 is required for this verification policy")
    with tempfile.TemporaryDirectory(prefix="opk-verify-") as temp:
        work = Path(temp)
        ca = work / "trust.pem"
        ca.write_bytes(policy["_ca_file"] + b"\n" + policy["_crl_file"] + b"\n")
        (work / "empty-store").mkdir()
        (work / "request.tsq").write_bytes(query)
        (work / "response.tsr").write_bytes(response)
        env = dict(os.environ, SSL_CERT_FILE=str(ca), SSL_CERT_DIR=str(work / "empty-store"))
        args = ["ts", "-verify", "-queryfile", str(work / "request.tsq"),
                "-in", str(work / "response.tsr"), "-CAfile", str(ca),
                "-CApath", str(work / "empty-store"), "-CAstore", str(ca), "-auth_level", "2"]
        # Only explicit roots. Embedded certificates are untrusted chain material.
        openssl(args + ["-crl_check_all"], policy["timeout_seconds"], env)
        # Also require validity at the signed time; NOT historical revocation proof.
        openssl(args + ["-attime", str(int(generated.timestamp()))], policy["timeout_seconds"], env)
    upper = generated + timedelta(microseconds=accuracy) if accuracy is not None else None
    return {
        "schema_version": 1, "status": "VERIFIED", "basis": "caller_supplied_trust_policy",
        "manifest_sha256": digest.hex(), "ca_sha256": policy["ca_sha256"],
        "policy_oid": policy["policy_oid"], "tsa_time_utc": generated.isoformat(),
        "accuracy_microseconds": accuracy,
        "existence_upper_bound_utc": upper.isoformat() if upper else None,
        "revocation": "checked_current_crls_full_chain",
        "certificate_time_policy": "valid_now_and_at_token_time",
        "verified_at_utc": now.isoformat(), "openssl": version,
        "public_availability": "NOT_PROVEN", "authorship": "NOT_PROVEN",
    }


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("TSA redirects are forbidden; configure the final HTTPS endpoint")


def post_query(url: str, query: bytes, timeout: int) -> bytes:
    endpoint(url)
    request = urllib.request.Request(url, data=query, method="POST", headers={
        "Content-Type": "application/timestamp-query", "Accept": "application/timestamp-reply",
        "User-Agent": "OpenPreprint-Kit/0.2",
    })
    # No ambient proxy credentials, redirects or insecure TLS overrides.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            if response.status != 200 or response.headers.get_content_type() != "application/timestamp-reply":
                raise ValueError("TSA did not return HTTP 200 application/timestamp-reply")
            result = response.read(LIMIT + 1)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ValueError("TSA HTTPS request failed; no timestamp was attached") from exc
    if not result or len(result) > LIMIT:
        raise ValueError("empty or oversized TSA response")
    return result


def attach(folder: Path, query: bytes, response: bytes, policy: dict) -> dict:
    if any((folder / name).exists() or (folder / name).is_symlink() for name in EVIDENCE_FILES):
        raise ValueError("timestamp evidence already exists; never overwrite it")
    report = verify_proof(folder, query, response, policy)
    created = []
    try:
        for name, data in (("timestamp.tsq", query), ("timestamp.tsr", response)):
            path = folder / name
            with path.open("xb") as stream:
                created.append(path)
                stream.write(data)
    except BaseException:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("request", "attach", "stamp", "verify"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--policy", required=True, type=Path, help="independently selected trust policy, not downloaded with the paper")
    parser.add_argument("--out", type=Path, help="request output outside the bundle")
    parser.add_argument("--query", type=Path)
    parser.add_argument("--response", type=Path)
    args = parser.parse_args()
    try:
        policy = load_policy(args.policy)
        if args.operation == "request":
            if args.out is None or args.out.resolve().is_relative_to(args.directory.resolve()):
                raise ValueError("request --out must name a new file outside the bundle")
            query = make_query(args.directory, policy)
            with args.out.open("xb") as stream:
                stream.write(query)
            result = {"status": "REQUEST_CREATED", "timestamp_verified": False}
        elif args.operation == "attach":
            if args.query is None or args.response is None:
                raise ValueError("attach requires --query and --response")
            result = attach(args.directory, read_regular(args.query), read_regular(args.response), policy)
        elif args.operation == "stamp":
            if any((args.directory / name).exists() for name in EVIDENCE_FILES):
                raise ValueError("timestamp evidence already exists")
            query = make_query(args.directory, policy)
            response = post_query(policy["tsa_url"], query, policy["timeout_seconds"])
            result = attach(args.directory, query, response, policy)
        else:
            result = verify_proof(args.directory, read_regular(args.directory / "timestamp.tsq"),
                                  read_regular(args.directory / "timestamp.tsr"), policy)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError, OverflowError, subprocess.TimeoutExpired) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
