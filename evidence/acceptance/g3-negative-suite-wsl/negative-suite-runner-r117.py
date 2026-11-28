#!/usr/bin/env python3
"""OpenPreprint Kit negative-test suite runner (20 fixed cases, see negative-suite-spec.json).

All cases run locally. No GitHub writes, no network TSA calls.
Every case MUST be rejected by the verifier; any false accept is recorded as FAIL.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(os.environ["OPK_SOURCE_ROOT"])
sys.path.insert(0, str(ROOT / "scripts"))
NEG = Path(os.environ["OPK_NEGATIVE_DIR"])
BASE = Path(os.environ["OPK_BASE_BUNDLE"])

POLICY_PATH = Path(os.environ["OPK_POLICY_PATH"])
OPENSSL = os.environ["OPK_OPENSSL"]

results = []


def record(cid, name, rejected, detail=""):
    ok = bool(rejected)
    results.append({"id": cid, "name": name, "expected": "REJECTED",
                    "rejected": ok, "verdict": "PASS" if ok else "FAIL",
                    "detail": detail[:400]})
    print(f"case {cid:2} {'PASS' if ok else 'FAIL'}  {name}  {detail[:160]}", flush=True)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def copy_bundle(dst: Path) -> Path:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(BASE, dst)
    return dst


def write_sums(bundle: Path) -> None:
    names = [p for p in bundle.iterdir() if p.is_file() and p.name not in ("SHA256SUMS", "timestamp.tsq", "timestamp.tsr")]
    values = {p.name: sha256_file(p) for p in names}
    sums = "".join(f"{values[n]}  {n}\n" for n in sorted(values))
    (bundle / "SHA256SUMS").write_text(sums, encoding="utf-8")


def tamper_tar_member(tar_path: Path, needle: bytes, repl: bytes) -> None:
    data = tar_path.read_bytes()
    idx = data.find(needle)
    assert idx != -1, "member content not found in tar"
    assert len(needle) == len(repl), "mutation must preserve member and tar sizes"
    tar_path.write_bytes(data[:idx] + repl + data[idx + len(needle):])


def recompute_manifest_for_tar(bundle: Path) -> None:
    # Keep the inner research catalog, outer manifest, and SHA256SUMS
    # internally consistent after a controlled member mutation.
    tar = bundle / "research-assets.tar"
    catalog = json.loads((bundle / "research-assets.json").read_text(encoding="utf-8"))
    with tarfile.open(tar, "r:*") as tf:
        members = {m.name: tf.extractfile(m).read() for m in tf.getmembers() if m.isfile()}
    for entry in catalog["entries"]:
        data = members[entry["path"]]
        entry["sha256"] = hashlib.sha256(data).hexdigest()
        entry["size_bytes"] = len(data)
    (bundle / "research-assets.json").write_text(
        json.dumps(catalog, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    for filename in ("research-assets.tar", "research-assets.json"):
        file = bundle / filename
        manifest["files"][filename] = {"sha256": sha256_file(file), "size_bytes": file.stat().st_size}
    (bundle / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    write_sums(bundle)


def recompute_consistent_paper_edit(bundle: Path) -> None:
    pdf = bytearray((bundle / "paper.pdf").read_bytes()); pdf[100] ^= 1
    (bundle / "paper.pdf").write_bytes(bytes(pdf))
    digest = sha256_file(bundle / "paper.pdf")
    metadata_path = bundle / "preprint-metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["paper_sha256"] = digest
    metadata["paper_size_bytes"] = len(pdf)
    metadata_path.write_text(json.dumps(metadata, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    catalog_path = bundle / "research-assets.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["paper_sha256"] = digest
    catalog_path.write_text(json.dumps(catalog, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    for filename in ("paper.pdf", "preprint-metadata.json", "research-assets.json"):
        file = bundle / filename
        manifest["files"][filename] = {"sha256": sha256_file(file), "size_bytes": file.stat().st_size}
    (bundle / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    write_sums(bundle)


def recompute_manifest_for_manifest_self(bundle: Path) -> None:
    # attacker rewrites manifest (consistent) - TSA must still reject
    write_sums(bundle)


def main() -> int:
    from preserve import restore
    from preflight import validate_repository  # noqa: F401
    from timestamp import load_policy, verify_digest, verify_proof, read_regular, make_query_for_digest
    from verify_evidence import verify_all
    from verify_release import verify
    from observation import assert_source_identity, record_public, verify_public, sha256_file as obs_sha256

    work = NEG / "work"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)

    policy = load_policy(POLICY_PATH)
    digest_a = hashlib.sha256((BASE / "manifest.json").read_bytes()).digest()
    tsq_a = (BASE / "timestamp.tsq").read_bytes()
    tsr_a = (BASE / "timestamp.tsr").read_bytes()
    tsq_b = make_query_for_digest(digest_a, policy)  # same manifest imprint, fresh nonce

    # --- Case 1: PDF tamper ---
    b = copy_bundle(work / "c1" / "bundle")
    data = bytearray((b / "paper.pdf").read_bytes()); data[100] ^= 1
    (b / "paper.pdf").write_bytes(bytes(data))
    record(1, "PDF改変 (bundle integrity)", bool(verify(b, None)), "; ".join(verify(b, None)))

    # --- Case 2: data tamper (naive + re-consistent) ---
    b = copy_bundle(work / "c2a" / "bundle")
    tamper_tar_member(b / "research-assets.tar", b"module,test_count\r\n", b"module,test_counT\r\n")
    record(2, "データ改変 (a: verify)", bool(verify(b, None)), "; ".join(verify(b, None)))
    b = copy_bundle(work / "c2b" / "bundle")
    tamper_tar_member(b / "research-assets.tar", b"module,test_count\r\n", b"module,test_counT\r\n")
    recompute_manifest_for_tar(b)
    try:
        verify_proof(b, read_regular(b / "timestamp.tsq"), read_regular(b / "timestamp.tsr"), policy)
        record(2, "データ改変 (b: TSA imprint) — variant", False, "verify_proof ACCEPTED a re-consistent tampered bundle")
    except ValueError as exc:
        reason = str(exc)
        if "timestamp imprint does not match the expected SHA-256 digest" not in reason:
            record(2, "データ改変 (b: TSA imprint) — variant", False, "wrong rejection reason: " + reason)
        else:
            record(2, "データ改変 (b: TSA imprint) — variant", True, reason)

    # --- Case 3: code tamper ---
    b = copy_bundle(work / "c3a" / "bundle")
    tamper_tar_member(b / "research-assets.tar", b"import csv", b"import csX")
    record(3, "コード改変 (a: verify)", bool(verify(b, None)), "; ".join(verify(b, None)))
    b = copy_bundle(work / "c3b" / "bundle")
    tamper_tar_member(b / "research-assets.tar", b"import csv", b"import csX")
    recompute_manifest_for_tar(b)
    try:
        verify_proof(b, read_regular(b / "timestamp.tsq"), read_regular(b / "timestamp.tsr"), policy)
        record(3, "コード改変 (b: TSA imprint) — variant", False, "verify_proof ACCEPTED")
    except ValueError as exc:
        reason = str(exc)
        if "timestamp imprint does not match the expected SHA-256 digest" not in reason:
            record(3, "コード改変 (b: TSA imprint) — variant", False, "wrong rejection reason: " + reason)
        else:
            record(3, "コード改変 (b: TSA imprint) — variant", True, reason)

    # --- Case 4: manifest tamper (naive + self-consistent) ---
    b = copy_bundle(work / "c4a" / "bundle")
    m = json.loads((b / "manifest.json").read_text(encoding="utf-8"))
    first = next(iter(m["files"])); m["files"][first]["size_bytes"] += 1
    (b / "manifest.json").write_text(json.dumps(m, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    record(4, "manifest改変 (a: verify)", bool(verify(b, None)), "; ".join(verify(b, None)))
    b = copy_bundle(work / "c4b" / "bundle")
    recompute_consistent_paper_edit(b)
    assert verify(b, None) == [], "internally consistent modified paper/metadata/catalog/manifest should pass offline integrity"
    try:
        verify_proof(b, read_regular(b / "timestamp.tsq"), read_regular(b / "timestamp.tsr"), policy)
        record(4, "manifest改変 (b: TSA imprint) — variant", False, "verify_proof ACCEPTED")
    except ValueError as exc:
        reason = str(exc)
        if "timestamp imprint does not match the expected SHA-256 digest" not in reason:
            record(4, "manifest改変 (b: TSA imprint) — variant", False, "wrong rejection reason: " + reason)
        else:
            record(4, "manifest改変 (b: TSA imprint) — variant", True, reason)

    # --- Case 5: missing asset ---
    b = copy_bundle(work / "c5" / "bundle")
    (b / "citation.bib").unlink()
    record(5, "資産欠落 (citation.bib 欠落)", bool(verify(b, None)), "; ".join(verify(b, None)))

    # --- Case 6: extra file ---
    b = copy_bundle(work / "c6" / "bundle")
    (b / "extra.txt").write_text("intruder\n", encoding="utf-8")
    record(6, "余計なファイル (extra.txt)", bool(verify(b, None)), "; ".join(verify(b, None)))

    # --- Case 7: wrong repository ---
    try:
        verify_all(BASE, POLICY_PATH, "Unjuno/openpreprint-kit", "v1", "existence")
        record(7, "別リポジトリ", False, "verify_all ACCEPTED wrong repository")
    except ValueError as exc:
        reason = str(exc)
        if "repository" not in reason.lower():
            record(7, "別リポジトリ", False, "wrong rejection reason: " + reason)
        else:
            record(7, "別リポジトリ", True, reason)

    # --- Case 8: wrong version ---
    try:
        verify_all(BASE, POLICY_PATH, "Unjuno/openpreprint-kit-paper", "v2", "existence")
        record(8, "別版 (v2 扱い)", False, "verify_all ACCEPTED v2 for v1 bundle")
    except Exception as exc:
        record(8, "別版 (v2 扱い)", True, str(exc))

    # --- Case 9: wrong CA pin ---
    trust_a = NEG / "trust-a"
    if trust_a.exists():
        shutil.rmtree(trust_a)
    trust_a.mkdir()
    src = POLICY_PATH.parent
    shutil.copy(src / "ca.pem", trust_a / "ca.pem")
    shutil.copy(src / "crl.pem", trust_a / "crl.pem")
    bad = trust_a / "policy09.json"
    pol = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    pol["ca_sha256"] = "00" * 32
    bad.write_text(json.dumps(pol, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    try:
        load_policy(bad)
        record(9, "誤CA指紋", False, "load_policy ACCEPTED wrong CA pin")
    except Exception as exc:
        record(9, "誤CA指紋", True, str(exc))

    # --- Case 10: wrong policy OID ---
    bad = trust_a / "policy10.json"
    pol = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    pol["policy_oid"] = "1.2.3.4.2"
    bad.write_text(json.dumps(pol, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    badpol = load_policy(bad)
    try:
        verify_digest(digest_a, tsq_a, tsr_a, badpol)
        record(10, "誤policy OID", False, "verify_digest ACCEPTED wrong OID")
    except ValueError as exc:
        reason = str(exc)
        if "timestamp policy OID mismatch" not in reason:
            record(10, "誤policy OID", False, "wrong rejection reason: " + reason)
        else:
            record(10, "誤policy OID", True, reason)

    # --- Case 11: nonce mismatch (b's query + a's response) ---
    try:
        verify_digest(digest_a, tsq_b, tsr_a, policy)
        record(11, "nonce不一致", False, "verify_digest ACCEPTED mixed nonce")
    except ValueError as exc:
        reason = str(exc)
        if "timestamp request/response nonce or certificate request mismatch" not in reason:
            record(11, "nonce不一致", False, "wrong rejection reason: " + reason)
        else:
            record(11, "nonce不一致", True, reason)

    # --- Case 12: forged signature ---
    forged = bytearray(tsr_a); forged[-10] ^= 1
    try:
        verify_digest(digest_a, tsq_a, bytes(forged), policy)
        record(12, "署名偽造", False, "verify_digest ACCEPTED forged signature")
    except ValueError as exc:
        reason = str(exc)
        if "OpenSSL verification failed" not in reason:
            record(12, "署名偽造", False, "wrong rejection reason: " + reason)
        else:
            record(12, "署名偽造", True, reason)

    # --- Cases 13-15: local synthetic PKI ---
    pki = NEG / "pki"
    shutil.rmtree(pki, ignore_errors=True)
    pki.mkdir()
    OPENSSL_EASY = str(OPENSSL)

    def make_pki_dir(d: Path):
        d.mkdir(parents=True, exist_ok=True)
        (d / "newcerts").mkdir(exist_ok=True)
        (d / "index.txt").write_text("", encoding="utf-8")
        (d / "serial").write_text("1000\n", encoding="utf-8")
        (d / "crlnumber").write_text("1000\n", encoding="utf-8")
        cnf = d / "pki.cnf"
        cnf.write_text(f"""
[ ca ]
default_ca = CA_default
[ CA_default ]
dir = {d.as_posix()}
database = $dir/index.txt
new_certs_dir = $dir/newcerts
certificate = $dir/ca.pem
private_key = $dir/ca.key
default_md = sha256
default_days = 365
default_crl_days = 30
policy = pol
serial = $dir/serial
default_crl_number = $dir/crlnumber
unique_subject = no
x509_extensions = usr_cert
[ pol ]
commonName = supplied
[ usr_cert ]
basicConstraints = CA:FALSE
keyUsage = critical,digitalSignature
extendedKeyUsage = critical,timeStamping
""", encoding="utf-8")
        return cnf

    def run_openssl(*args, check=True):
        r = subprocess.run([OPENSSL_EASY, *args], capture_output=True, text=True, timeout=60)
        if check and r.returncode:
            raise RuntimeError("openssl failed: " + (r.stderr or r.stdout)[-800:])
        return r

    def build_pki(d: Path, tsa_cn: str, crl_days: int = 30):
        cnf = make_pki_dir(d)
        run_openssl("req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", str(d / "ca.key"),
                    "-out", str(d / "ca.pem"), "-days", "3650", "-subj", "/CN=OPK-Test-CA",
                    "-addext", "basicConstraints=critical,CA:TRUE",
                    "-addext", "keyUsage=critical,keyCertSign,cRLSign")
        run_openssl("req", "-newkey", "rsa:2048", "-nodes", "-keyout", str(d / "tsa.key"),
                    "-out", str(d / "tsa.csr"), "-subj", f"/CN={tsa_cn}")
        run_openssl("ca", "-batch", "-config", str(cnf), "-in", str(d / "tsa.csr"),
                    "-out", str(d / "tsa.pem"))
        return cnf

    def make_tsq_tsr(d: Path, tsa_pem: Path | None = None):
        from timestamp import make_query_for_digest
        manifest_digest = hashlib.sha256((BASE / "manifest.json").read_bytes()).digest()
        (d / "req.tsq").write_bytes(make_query_for_digest(manifest_digest,
                                                          {"policy_oid": "1.2.3.4.1"}))
        run_openssl("ts", "-reply", "-queryfile", str(d / "req.tsq"),
                    "-signer", str(tsa_pem or (d / "tsa.pem")), "-inkey", str(d / "tsa.key"),
                    "-chain", str(d / "ca.pem"), "-tspolicy", "1.2.3.4.1",
                    "-out", str(d / "resp.tsr"))

    def pki_policy(d: Path, name: str = "policy.json") -> Path:
        p = d / name
        p.write_text(json.dumps({
            "schema_version": 1, "tsa_url": "https://freetsa.org/tsr",
            "ca_file": "ca.pem",
            "ca_sha256": hashlib.sha256((d / "ca.pem").read_bytes()).hexdigest(),
            "crl_file": "crl.pem", "policy_oid": "1.2.3.4.1",
            "timeout_seconds": 45}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return p

    manifest_digest = hashlib.sha256((BASE / "manifest.json").read_bytes()).digest()

    # Case 13: validly-signed but CRL-revoked TSA cert
    d13 = pki / "c13"
    cnf13 = build_pki(d13, "OPK-Test-TSA-Revoked")
    make_tsq_tsr(d13)
    run_openssl("ca", "-batch", "-config", str(cnf13), "-revoke", str(d13 / "tsa.pem"),
                "-crl_reason", "keyCompromise")
    run_openssl("ca", "-batch", "-config", str(cnf13), "-gencrl", "-out", str(d13 / "crl.pem"))
    pol13 = pki_policy(d13)
    try:
        verify_digest(manifest_digest, (d13 / "req.tsq").read_bytes(),
                      (d13 / "resp.tsr").read_bytes(), load_policy(pol13))
        record(13, "失効TSA", False, "verify_digest ACCEPTED revoked TSA cert")
    except ValueError as exc:
        reason = str(exc)
        if "OpenSSL verification failed" not in reason or "revoked" not in reason.lower():
            record(13, "失効TSA", False, "wrong rejection reason: " + reason)
        else:
            record(13, "失効TSA", True, reason)

    # Case 14: expired TSA cert
    d14 = pki / "c14"
    cnf14 = make_pki_dir(d14)
    run_openssl("req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", str(d14 / "ca.key"),
                "-out", str(d14 / "ca.pem"), "-days", "3650", "-subj", "/CN=OPK-Test-CA",
                "-addext", "basicConstraints=critical,CA:TRUE",
                "-addext", "keyUsage=critical,keyCertSign,cRLSign")
    run_openssl("req", "-newkey", "rsa:2048", "-nodes", "-keyout", str(d14 / "tsa.key"),
                "-out", str(d14 / "tsa.csr"), "-subj", "/CN=OPK-Test-TSA-Expired")
    r14 = subprocess.run([OPENSSL_EASY, "ca", "-batch", "-config", str(cnf14),
                          "-in", str(d14 / "tsa.csr"), "-out", str(d14 / "tsa.pem"),
                          "-startdate", "20200101000000Z", "-enddate", "20210101000000Z"],
                         capture_output=True, text=True, timeout=60)
    if r14.returncode:
        record(14, "期限切れTSA", False, "openssl ca -startdate/-enddate unsupported: " + (r14.stderr or "")[-300:])
    else:
        make_tsq_tsr(d14)
        run_openssl("ca", "-batch", "-config", str(cnf14), "-gencrl", "-out", str(d14 / "crl.pem"))
        pol14 = pki_policy(d14)
        try:
            verify_digest(manifest_digest, (d14 / "req.tsq").read_bytes(),
                          (d14 / "resp.tsr").read_bytes(), load_policy(pol14))
            record(14, "期限切れTSA", False, "verify_digest ACCEPTED expired TSA cert")
        except ValueError as exc:
            reason = str(exc)
            if "OpenSSL verification failed" not in reason or not any(needle in reason.lower() for needle in ("expired", "not yet valid", "certificate is not yet valid")):
                record(14, "期限切れTSA", False, "wrong rejection reason: " + reason)
            else:
                record(14, "期限切れTSA", True, reason)

    # Case 15: CRL whose nextUpdate is in the PAST (hand-built: TBS re-signed by the test CA)
    d15 = pki / "c15"
    cnf15 = build_pki(d15, "OPK-Test-TSA-StaleCRL")
    make_tsq_tsr(d15)
    run_openssl("ca", "-batch", "-config", str(cnf15), "-gencrl", "-out", str(d15 / "crl-fresh.pem"))
    import base64 as _b64
    from asn1crypto import crl as _acr, x509 as _ax
    import datetime as _dt
    pem = (d15 / "crl-fresh.pem").read_text()
    cl = _acr.CertificateList.load(_b64.b64decode(
        "".join(l for l in pem.splitlines() if not l.startswith("-----"))))
    tbs = cl["tbs_cert_list"]
    tbs["this_update"] = _ax.Time({"utc_time": _dt.datetime(2019, 12, 1, tzinfo=_dt.timezone.utc)})
    tbs["next_update"] = _ax.Time({"utc_time": _dt.datetime(2020, 1, 1, tzinfo=_dt.timezone.utc)})
    (d15 / "tbs.der").write_bytes(tbs.dump())
    run_openssl("dgst", "-sha256", "-sign", str(d15 / "ca.key"),
                "-out", str(d15 / "sig.bin"), str(d15 / "tbs.der"))
    cl["signature"] = _ax.OctetBitString((d15 / "sig.bin").read_bytes())
    cl["signature_algorithm"] = _ax.SignedDigestAlgorithm({"algorithm": "sha256_rsa"})
    raw = _b64.b64encode(cl.dump()).decode()
    wrapped = "\n".join(raw[i:i+64] for i in range(0, len(raw), 64))
    (d15 / "crl.pem").write_text(f"-----BEGIN X509 CRL-----\n{wrapped}\n-----END X509 CRL-----\n",
                                 encoding="utf-8")
    crl_info = run_openssl("crl", "-in", str(d15 / "crl.pem"), "-noout",
                           "-lastupdate", "-nextupdate", check=False)
    stale_desc = (crl_info.stdout + " " + crl_info.stderr).strip().replace("\n", " | ")
    pol15 = pki_policy(d15, "policy15.json")
    try:
        verify_digest(manifest_digest, (d15 / "req.tsq").read_bytes(),
                      (d15 / "resp.tsr").read_bytes(), load_policy(pol15))
        record(15, "古いCRL", False,
               "verify_digest ACCEPTED a CRL whose nextUpdate is in the past (CRL freshness NOT enforced); CRL: " + stale_desc)
    except Exception as exc:
        record(15, "古いCRL", True,
               "verify_digest rejected stale CRL: " + str(exc)[:200] + "; CRL: " + stale_desc)

    # --- Cases 16-18: hostile ZIPs ---
    def craft(path: Path, members: list[tuple[str, bytes, int]]) -> Path:
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as z:
            for name, data, attr in members:
                zi = zipfile.ZipInfo(name)
                zi.create_system = 3
                zi.external_attr = attr << 16
                zi.compress_type = zipfile.ZIP_STORED
                z.writestr(zi, data)
        return path

    reg = 0o100644
    def try_restore(cid, name, zip_path):
        out = NEG / "work" / f"out-c{cid}"
        if out.exists():
            shutil.rmtree(out)
        try:
            restore(zip_path, out, sha256_file(zip_path), POLICY_PATH)
            record(cid, name, False, "restore ACCEPTED hostile archive")
        except Exception as exc:
            record(cid, name, True, str(exc)[:200])

    z16 = craft(NEG / "work" / "c16.zip", [("bundle/../evil.txt", b"x", reg),
                                           ("preservation.json", b'{"schema_version":1}', reg)])
    try_restore(16, "ZIPパストラバーサル", z16)
    z17 = craft(NEG / "work" / "c17.zip", [("preservation.json", b'{"a":1}', reg),
                                           ("preservation.json", b'{"b":2}', reg)])
    try_restore(17, "重複member", z17)
    z18 = craft(NEG / "work" / "c18.zip", [("bundle/paper.pdf", b"x", 0o120777),
                                           ("preservation.json", b'{"schema_version":1}', reg)])
    try_restore(18, "symlink member", z18)

    # --- Cases 19-20: witness signature ---
    keys = NEG / "keys"
    shutil.rmtree(keys, ignore_errors=True)
    keys.mkdir()
    for k in ("witnessA", "witnessB"):
        subprocess.run([OPENSSL, "genpkey", "-algorithm", "ED25519", "-out", str(keys / f"{k}.key")],
                       capture_output=True, check=True)
        subprocess.run([OPENSSL, "pkey", "-pubout", "-in", str(keys / f"{k}.key"),
                        "-out", str(keys / f"{k}.pub")], capture_output=True, check=True)
    base_files = {p.name: p.read_bytes() for p in BASE.iterdir() if p.is_file()}

    def local_fetcher(name):
        return base_files[name]

    evidence = NEG / "work" / "witness-evidence"
    try:
        record_public("Unjuno/openpreprint-kit-paper", "v1", evidence, POLICY_PATH,
                      keys / "witnessA.key", fetcher=local_fetcher, stamp_observation=False)
        witness_ok = True
    except Exception as exc:
        witness_ok = False
        evidence_err = str(exc)[:300]
    if witness_ok:
        pub_b_sha = hashlib.sha256((keys / "witnessB.pub").read_bytes()).hexdigest()
        try:
            verify_public(evidence, keys / "witnessB.pub", pub_b_sha, POLICY_PATH)
            record(19, "誤観測鍵", False, "verify_public ACCEPTED wrong observer key")
        except ValueError as exc:
            reason = str(exc)
            if not any(needle in reason.lower() for needle in ("public key", "key pin", "fingerprint", "sha-256", "signature does not verify")):
                record(19, "誤観測鍵", False, "wrong rejection reason: " + reason)
            else:
                record(19, "誤観測鍵", True, reason)
        # case 20: tamper observation.json then re-sign with same key
        obs = json.loads((evidence / "observation.json").read_text(encoding="utf-8"))
        obs["paper_sha256"] = ("0" * 64)
        (evidence / "observation.json").write_text(json.dumps(obs, sort_keys=True, indent=2) + "\n",
                                                   encoding="utf-8")
        subprocess.run([OPENSSL, "pkeyutl", "-sign", "-inkey", str(keys / "witnessA.key"),
                        "-rawin", "-in", str(evidence / "observation.json"),
                        "-out", str(evidence / "observation.sig")],
                       capture_output=True, check=True)
        pub_a_sha = hashlib.sha256((keys / "witnessA.pub").read_bytes()).hexdigest()
        try:
            verify_public(evidence, keys / "witnessA.pub", pub_a_sha, POLICY_PATH)
            record(20, "観測後の再署名", False, "verify_public ACCEPTED post-observation re-signature")
        except ValueError as exc:
            reason = str(exc)
            if not any(needle in reason.lower() for needle in ("digest", "source", "paper", "identity", "mismatch", "does not match fetched content")):
                record(20, "観測後の再署名", False, "wrong rejection reason: " + reason)
            else:
                record(20, "観測後の再署名", True, reason)
    else:
        record(19, "誤観測鍵", False, "witness setup failed (mock path): " + evidence_err)
        record(20, "観測後の再署名", False, "witness setup failed (mock path): " + evidence_err)

    summary = {"schema_version": 1, "kind": "negative-suite-results",
               "fixed_spec": "negative-suite-spec.json",
               "toolkit_main": "39346736ce91371b957ddbfa9b045cbe9409494f",
               "total": len(results),
               "passes": sum(1 for r in results if r["verdict"] == "PASS"),
               "fails": sum(1 for r in results if r["verdict"] == "FAIL"),
               "false_accepts": sum(1 for r in results if not r["rejected"]),
               "reason_assertions": 10,
               "results": results}
    out = NEG / "negative-suite-results.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                   encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("total", "passes", "fails", "false_accepts")}, indent=2))
    return 0 if summary["false_accepts"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
