"""Property-based (Hypothesis) adversarial-input tests for trust boundaries.

Hypothesis is a test-only dependency; these tests skip cleanly when it is not
installed so the release test suite stays reproducible from the pinned locks.
"""
from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

HYP = importlib.util.find_spec("hypothesis") is not None

if HYP:
    from hypothesis import given, settings, strategies as st

import preflight
import verify_release
import observation
import citation_validation


@unittest.skipUnless(HYP, "hypothesis not installed (test-only dependency)")
class HypothesisBoundaryTests(unittest.TestCase):
    @settings(max_examples=100, deadline=None)
    @given(st.lists(st.text(min_size=1, max_size=12), max_size=12))
    def test_unique_object_rejects_any_duplicate_key(self, keys):
        pairs = [(k, i) for i, k in enumerate(keys)]
        if len(set(keys)) == len(keys):
            self.assertEqual(verify_release.unique_object(pairs), dict(pairs))
        else:
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                verify_release.unique_object(pairs)

    @settings(max_examples=100, deadline=None)
    @given(st.binary(min_size=1, max_size=512), st.binary(min_size=1, max_size=512))
    def test_receipt_digest_binds_data_and_signature(self, data, sig):
        a = observation.receipt_digest(data, sig)
        b = observation.receipt_digest(data, sig)
        self.assertEqual(a, b)
        changed_data = observation.receipt_digest(data + b"x", sig)
        changed_sig = observation.receipt_digest(data, sig + b"x")
        self.assertNotEqual(a, changed_data)
        self.assertNotEqual(a, changed_sig)

    @settings(max_examples=150, deadline=None)
    @given(st.text(max_size=140))
    def test_repository_validation_properties(self, repo):
        try:
            preflight.validate_repository(repo)
        except ValueError:
            return
        self.assertEqual(repo.count("/"), 1)
        self.assertFalse(any(c.isspace() for c in repo))
        owner, name = repo.split("/")
        self.assertTrue(1 <= len(owner) <= 100 and 1 <= len(name) <= 100)
        self.assertTrue(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", owner))
        self.assertTrue(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name))

    @settings(max_examples=150, deadline=None)
    @given(st.text(max_size=160))
    def test_safe_https_properties(self, url):
        if observation.safe_https(url):
            parts = observation.urllib.parse.urlsplit(url)
            self.assertEqual(parts.scheme, "https")
            self.assertIn(parts.hostname, observation.HOSTS)
            self.assertIsNone(parts.username)
            self.assertIsNone(parts.password)
            self.assertFalse(parts.fragment)
            self.assertIn(parts.port, (None, 443))

    @settings(max_examples=100, deadline=None)
    @given(st.booleans(), st.booleans(), st.booleans(), st.booleans(),
           st.sampled_from(["v0", "v1", "v2"]), st.sampled_from(["a" * 40, "b" * 40]))
    def test_preflight_matches_state_model(self, is_public, immutable, tag, ref, version, commit):
        """Differential property: production preflight PASS iff the verified
        state of the formal model would be reached from the initial state."""
        head = commit if not tag else "c" * 40
        model_pass = (is_public and immutable and not tag and not ref
                      and version != "v0" and head == commit)

        def get(path):
            if path == "":
                return 200, {"private": not is_public, "default_branch": "main"}
            if path == "/immutable-releases":
                return 200, {"enabled": immutable}
            if path == "/commits/main":
                return 200, {"sha": head}
            if path in (f"/releases/tags/{version}", f"/git/ref/tags/{version}"):
                occupied = tag if "releases/tags" in path else ref
                return (200, {"x": 1}) if occupied else (404, {})
            return 404, {}

        old_sleep = preflight.time.sleep
        preflight.time.sleep = lambda _s: None
        try:
            try:
                result = preflight.preflight("Unjuno/paper", version, commit, get)
                prod_pass = result["status"] == "PASS"
            except ValueError:
                prod_pass = False
        finally:
            preflight.time.sleep = old_sleep
        self.assertEqual(prod_pass, model_pass)

    @settings(max_examples=100, deadline=None)
    @given(st.text(max_size=80))
    def test_bibtex_normalization_is_idempotent(self, value):
        once = citation_validation._normalize_bib_text(value)
        twice = citation_validation._normalize_bib_text(once)
        self.assertEqual(once, twice)

    @settings(max_examples=100, deadline=None)
    @given(st.text(max_size=90))
    def test_hex_sha256_pattern_is_exact(self, value):
        matches = verify_release.HEX_SHA256.fullmatch(value) is not None
        self.assertEqual(matches, re.fullmatch(r"[0-9a-f]{64}", value) is not None)


if __name__ == "__main__":
    unittest.main()
