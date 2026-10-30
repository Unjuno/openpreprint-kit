"""Regression tests for malformed public inputs (not cryptographic assurance)."""
import hashlib
import json
import unittest
import test_release


class HardeningTests(unittest.TestCase):
    def setUp(self):
        self.h = test_release.ReleaseBundleTests()
        self.h.setUp()

    def tearDown(self):
        self.h.tearDown()

    def assert_invalid_metadata(self):
        self.h.write_metadata()
        result = self.h.run_script("validate.py", "--strict")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_x_in_orcid_body_is_rejected_without_crash(self):
        self.h.metadata["authors"][0]["orcid"] = "0000-0002-1825-X097"
        self.assert_invalid_metadata()

    def test_boolean_schema_is_not_integer_version(self):
        self.h.metadata["schema_version"] = True
        self.assert_invalid_metadata()

    def test_zero_dotted_version_is_still_a_draft(self):
        self.h.metadata["version"] = "v0.0"
        self.assert_invalid_metadata()

    def test_unicode_digits_are_not_release_tags(self):
        self.h.metadata["version"] = "v1\u0661"
        self.assert_invalid_metadata()

    def test_padded_placeholder_is_not_a_title(self):
        self.h.metadata["title"] = " Untitled Preprint "
        self.assert_invalid_metadata()

    def test_explicit_null_entity_name_is_rejected(self):
        self.h.metadata["authors"][0]["name"] = None
        self.assert_invalid_metadata()

    def test_duplicate_manifest_key_is_rejected(self):
        self.h.make_bundle()
        path = self.h.bundle / "manifest.json"
        path.write_text(path.read_text().replace('{', '{"algorithm":"sha512",', 1))
        sums = self.h.bundle / "SHA256SUMS"
        lines = sums.read_text().splitlines()
        lines = [hashlib.sha256(path.read_bytes()).hexdigest() + "  manifest.json"
                 if line.endswith("  manifest.json") else line for line in lines]
        sums.write_text("\n".join(lines) + "\n")
        result = self.h.run_script("verify_release.py", self.h.bundle)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("duplicate", result.stderr.lower())

    def test_sidecar_pair_is_recognized_but_not_claimed_verified(self):
        self.h.make_bundle()
        for name in ("timestamp.tsq", "timestamp.tsr"):
            (self.h.bundle / name).write_bytes(b"not-validated-by-integrity-command")
        result = self.h.run_script("verify_release.py", self.h.bundle)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("NOT verified", result.stdout)

    def test_partial_sidecar_pair_is_rejected(self):
        self.h.make_bundle()
        (self.h.bundle / "timestamp.tsq").write_bytes(b"partial")
        result = self.h.run_script("verify_release.py", self.h.bundle)
        self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
