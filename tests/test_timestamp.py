"""Real RFC 3161 crypto tests using an ephemeral CA/TSA, never a public service."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import contextlib
import io
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from asn1crypto import tsp
import test_release

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "timestamp.py"
OID = "1.2.3.4.1"


def run(*args):
    return subprocess.run([str(x) for x in args], capture_output=True, text=True, timeout=30)


def ssl(*args):
    result = run("openssl", *args)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout


class Authority:
    """Test-only keys are generated in temporary directories and never committed."""
    def __init__(self, root: Path, accuracy=True, expired=False):
        self.root = root
        root.mkdir()
        (root / "newcerts").mkdir()
        (root / "index").touch()
        for name in ("serial", "crlnumber", "tsserial"):
            (root / name).write_text("1000\n")
        self.ca = root / "root.pem"
        self.crl = root / "root.crl.pem"
        self.config = root / "ca.cnf"
        self.tsa_config = root / "tsa.cnf"
        ssl("req", "-new", "-x509", "-newkey", "rsa:2048", "-nodes",
            "-keyout", root / "root.key", "-out", self.ca, "-days", "2",
            "-subj", "/CN=OPK TEST ROOT - NOT A PUBLIC AUTHORITY",
            "-addext", "basicConstraints=critical,CA:TRUE",
            "-addext", "keyUsage=critical,keyCertSign,cRLSign")
        ssl("req", "-new", "-newkey", "rsa:2048", "-nodes",
            "-keyout", root / "tsa.key", "-out", root / "tsa.csr",
            "-subj", "/CN=Ephemeral test timestamp signer")
        self.config.write_text(f"""[ca]
default_ca=ca_default
[ca_default]
dir={root}
new_certs_dir=$dir/newcerts
database=$dir/index
serial=$dir/serial
crlnumber=$dir/crlnumber
certificate=$dir/root.pem
private_key=$dir/root.key
default_md=sha256
default_days=2
default_crl_days=1
policy=policy
x509_extensions=tsa_ext
unique_subject=no
[policy]
commonName=supplied
[tsa_ext]
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature
extendedKeyUsage=critical,timeStamping
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid,issuer
""")
        args = ["ca", "-batch", "-notext", "-config", self.config,
                "-in", root / "tsa.csr", "-out", root / "tsa.pem"]
        if expired:
            now = datetime.now(timezone.utc)
            args += ["-startdate", (now - timedelta(days=2)).strftime("%Y%m%d%H%M%SZ"),
                     "-enddate", (now - timedelta(days=1)).strftime("%Y%m%d%H%M%SZ")]
        ssl(*args)
        self.make_crl()
        self.tsa_config.write_text(f"""[tsa]
default_tsa=signer
[signer]
serial={root}/tsserial
signer_cert={root}/tsa.pem
certs={root}/root.pem
signer_key={root}/tsa.key
signer_digest=sha256
default_policy={OID}
other_policies=1.2.3.4.2
digests=sha256
ordering=yes
tsa_name=yes
ess_cert_id_chain=yes
ess_cert_id_alg=sha256
""" + ("accuracy=secs:1\n" if accuracy else ""))

    def make_crl(self, stale=False):
        args = ["ca", "-gencrl", "-config", self.config, "-out", self.crl]
        if stale:
            now = datetime.now(timezone.utc)
            args += ["-crl_lastupdate", (now - timedelta(days=2)).strftime("%Y%m%d%H%M%SZ"),
                     "-crl_nextupdate", (now - timedelta(days=1)).strftime("%Y%m%d%H%M%SZ")]
        ssl(*args)

    def policy(self):
        return {"schema_version": 1, "tsa_url": "https://tsa.example.invalid/",
                "ca_file": str(self.ca),
                "ca_sha256": hashlib.sha256(self.ca.read_bytes()).hexdigest(),
                "crl_file": str(self.crl), "policy_oid": OID, "timeout_seconds": 5}

    def sign(self, query: Path, response: Path):
        ssl("ts", "-reply", "-config", self.tsa_config,
            "-queryfile", query, "-out", response)


class TimestampTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        cls.authority = Authority(cls.root / "authority")
        cls.bundle_helper = test_release.ReleaseBundleTests()
        cls.bundle_helper.setUp()
        cls.bundle_helper.make_bundle()

    @classmethod
    def tearDownClass(cls):
        cls.bundle_helper.tearDown()
        cls.temporary.cleanup()

    def setUp(self):
        self.case = tempfile.TemporaryDirectory()
        self.path = Path(self.case.name)
        self.bundle = self.path / "bundle"
        shutil.copytree(self.bundle_helper.bundle, self.bundle)
        self.policy = self.path / "policy.json"
        self.settings = self.authority.policy()
        self.save_policy()
        self.query = self.path / "query.tsq"
        self.response = self.path / "response.tsr"

    def tearDown(self):
        self.case.cleanup()

    def save_policy(self):
        self.policy.write_text(json.dumps(self.settings))

    def command(self, verb, *args):
        self.assertTrue(SCRIPT.is_file(), "RFC 3161 command is not implemented")
        return run(sys.executable, SCRIPT, verb, self.bundle, "--policy", self.policy, *args)

    def make_response(self, authority=None):
        result = self.command("request", "--out", self.query)
        self.assertEqual(result.returncode, 0, result.stderr)
        (authority or self.authority).sign(self.query, self.response)

    def attach(self):
        return self.command("attach", "--query", self.query, "--response", self.response)

    def make_evidence(self):
        self.make_response()
        result = self.attach()
        self.assertEqual(result.returncode, 0, result.stderr)

    def assert_rejected(self, result):
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_request_contains_sha256_nonce_and_policy(self):
        result = self.command("request", "--out", self.query)
        self.assertEqual(result.returncode, 0, result.stderr)
        request = tsp.TimeStampReq.load(self.query.read_bytes(), strict=True).native
        self.assertEqual(request["message_imprint"]["hash_algorithm"]["algorithm"], "sha256")
        self.assertEqual(request["message_imprint"]["hashed_message"],
                         hashlib.sha256((self.bundle / "manifest.json").read_bytes()).digest())
        self.assertGreaterEqual(request["nonce"].bit_length(), 128)
        self.assertEqual(request["req_policy"], OID)

    def test_real_signature_chain_crl_and_accuracy(self):
        self.make_evidence()
        result = self.command("verify")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "VERIFIED")
        self.assertEqual(report["revocation"], "checked_current_crls_full_chain")
        self.assertEqual(report["accuracy_microseconds"], 1_000_000)
        self.assertEqual(
            (datetime.fromisoformat(report["existence_upper_bound_utc"]) -
             datetime.fromisoformat(report["tsa_time_utc"])).total_seconds(), 1.0)
        self.assertEqual(report["public_availability"], "NOT_PROVEN")
        self.assertEqual(report["authorship"], "NOT_PROVEN")

    def test_wrong_ca_pin_fails(self):
        self.make_evidence()
        self.settings["ca_sha256"] = "0" * 64
        self.save_policy()
        self.assert_rejected(self.command("verify"))

    def test_unknown_but_correctly_pinned_ca_fails(self):
        self.make_evidence()
        other = Authority(self.path / "other")
        self.settings = other.policy()
        self.save_policy()
        self.assert_rejected(self.command("verify"))

    def test_wrong_nonce_fails_without_attaching_files(self):
        self.make_response()
        self.query.unlink()
        result = self.command("request", "--out", self.query)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_rejected(self.attach())
        self.assertFalse((self.bundle / "timestamp.tsr").exists())
        self.assertFalse((self.bundle / "timestamp.tsq").exists())

    def test_wrong_policy_oid_fails(self):
        self.make_evidence()
        self.settings["policy_oid"] = "1.2.3.4.2"
        self.save_policy()
        self.assert_rejected(self.command("verify"))

    def test_corrupt_response_fails_without_traceback(self):
        self.make_response()
        self.response.write_bytes(b"not ASN.1")
        self.assert_rejected(self.attach())

    def test_revoked_signer_fails(self):
        authority = Authority(self.path / "revoked")
        self.settings = authority.policy()
        self.save_policy()
        self.make_response(authority)
        ssl("ca", "-config", authority.config, "-revoke", authority.root / "tsa.pem")
        authority.make_crl()
        self.assert_rejected(self.attach())

    def test_stale_crl_fails(self):
        authority = Authority(self.path / "stale")
        self.settings = authority.policy()
        self.save_policy()
        self.make_response(authority)
        authority.make_crl(stale=True)
        self.assert_rejected(self.attach())

    def test_expired_signer_fails(self):
        authority = Authority(self.path / "expired", expired=True)
        self.settings = authority.policy()
        self.save_policy()
        self.make_response(authority)
        self.assert_rejected(self.attach())

    def test_forged_signature_is_rejected_by_openssl(self):
        self.make_response()
        response = tsp.TimeStampResp.load(self.response.read_bytes())
        signer = response["time_stamp_token"]["content"]["signer_infos"][0]
        signature = signer["signature"].native
        signer["signature"] = signature[:-1] + bytes([signature[-1] ^ 1])
        self.response.write_bytes(response.dump())
        result = self.attach()
        self.assert_rejected(result)
        self.assertIn("OpenSSL verification failed", result.stderr)

    def test_stamp_path_uses_real_crypto_with_mocked_network_only(self):
        module = TransportTests().module()
        def local_tsa(url, query, timeout):
            self.query.write_bytes(query)
            self.authority.sign(self.query, self.response)
            return self.response.read_bytes()
        output = io.StringIO()
        with mock.patch.object(module, "post_query", side_effect=local_tsa), \
                mock.patch.object(sys, "argv", [str(SCRIPT), "stamp", str(self.bundle),
                                               "--policy", str(self.policy)]), \
                contextlib.redirect_stdout(output):
            self.assertEqual(module.main(), 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "VERIFIED")
        self.assertTrue((self.bundle / "timestamp.tsq").is_file())
        self.assertTrue((self.bundle / "timestamp.tsr").is_file())

    def test_missing_crl_fails(self):
        self.settings["crl_file"] = str(self.path / "missing.pem")
        self.save_policy()
        self.assert_rejected(self.command("request", "--out", self.query))

    def test_all_checksums_rewritten_still_fails_timestamp(self):
        self.make_evidence()
        (self.bundle / "paper.pdf").write_bytes(b"%PDF-1.7\nDifferent paper\n")
        path = self.bundle / "preprint-metadata.json"
        record = json.loads(path.read_text())
        record["paper_sha256"] = hashlib.sha256((self.bundle / "paper.pdf").read_bytes()).hexdigest()
        record["paper_size_bytes"] = (self.bundle / "paper.pdf").stat().st_size
        path.write_text(json.dumps(record))
        manifest_file = self.bundle / "manifest.json"
        manifest = json.loads(manifest_file.read_text())
        for name in manifest["files"]:
            data = (self.bundle / name).read_bytes()
            manifest["files"][name] = {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}
        manifest_file.write_text(json.dumps(manifest))
        names = sorted(set(manifest["files"]) | {"manifest.json"})
        (self.bundle / "SHA256SUMS").write_text("".join(
            hashlib.sha256((self.bundle / name).read_bytes()).hexdigest() + "  " + name + "\n"
            for name in names))
        integrity = run(sys.executable, ROOT / "scripts/verify_release.py", self.bundle)
        self.assertEqual(integrity.returncode, 0, integrity.stderr)
        self.assert_rejected(self.command("verify"))

    def test_existing_evidence_is_never_overwritten(self):
        self.make_evidence()
        original = (self.bundle / "timestamp.tsr").read_bytes()
        self.assert_rejected(self.attach())
        self.assertEqual(original, (self.bundle / "timestamp.tsr").read_bytes())

    def test_partial_evidence_fails(self):
        self.make_evidence()
        (self.bundle / "timestamp.tsq").unlink()
        self.assert_rejected(self.command("verify"))

    def test_missing_accuracy_is_unknown_not_zero(self):
        authority = Authority(self.path / "no-accuracy", accuracy=False)
        self.settings = authority.policy()
        self.save_policy()
        self.make_response(authority)
        result = self.attach()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(self.command("verify").stdout)
        self.assertIsNone(report["accuracy_microseconds"])
        self.assertIsNone(report["existence_upper_bound_utc"])

    def test_http_endpoint_is_rejected(self):
        self.settings["tsa_url"] = "http://tsa.example.invalid/"
        self.save_policy()
        self.assert_rejected(self.command("stamp"))

    def test_url_credentials_are_rejected(self):
        self.settings["tsa_url"] = "https://secret:password@tsa.example.invalid/"
        self.save_policy()
        result = self.command("stamp")
        self.assert_rejected(result)
        self.assertNotIn("password", result.stderr)

    def test_query_output_does_not_overwrite_existing_file(self):
        self.query.write_bytes(b"KEEP")
        self.assert_rejected(self.command("request", "--out", self.query))
        self.assertEqual(self.query.read_bytes(), b"KEEP")

    def test_noninteger_policy_schema_is_rejected(self):
        self.settings["schema_version"] = True
        self.save_policy()
        self.assert_rejected(self.command("request", "--out", self.query))


class TransportTests(unittest.TestCase):
    def module(self):
        self.assertTrue(SCRIPT.is_file(), "RFC 3161 transport is not implemented")
        sys.path.insert(0, str(ROOT / "scripts"))
        spec = importlib.util.spec_from_file_location("opk_timestamp_test", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_wrong_mime_type_is_not_a_timestamp(self):
        module = self.module()
        response = mock.MagicMock()
        response.status = 200
        response.headers.get_content_type.return_value = "text/html"
        opener = mock.MagicMock()
        opener.open.return_value.__enter__.return_value = response
        with mock.patch.object(module.urllib.request, "build_opener", return_value=opener):
            with self.assertRaises(ValueError):
                module.post_query("https://tsa.example.invalid/", b"query", 5)

    def test_response_size_is_bounded(self):
        module = self.module()
        response = mock.MagicMock()
        response.status = 200
        response.headers.get_content_type.return_value = "application/timestamp-reply"
        response.read.return_value = b"x" * (1024 * 1024 + 1)
        opener = mock.MagicMock()
        opener.open.return_value.__enter__.return_value = response
        with mock.patch.object(module.urllib.request, "build_opener", return_value=opener):
            with self.assertRaises(ValueError):
                module.post_query("https://tsa.example.invalid/", b"query", 5)

    def test_redirect_is_not_followed(self):
        module = self.module()
        handler = module.NoRedirect()
        with self.assertRaises(ValueError):
            handler.redirect_request(None, None, 302, "Found", {}, "https://other.invalid/")


if __name__ == "__main__":
    unittest.main()
