"""Regression tests for the 2026-11-18 cycle-4 audit (AUD-14..AUD-17)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class Iteration4FixTests(unittest.TestCase):
    """AUD-14: validated metadata must be bound to the published bundle."""

    def test_raced_metadata_cannot_leak_outside_file(self):
        import prepare_release as pr
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            secret = base / "secret.txt"
            secret.write_bytes(b"TOP-SECRET-CONFIDENTIAL\n")
            evil = {"schema_version": 1, "title": "t", "version": "v1",
                    "license": "CC-BY-4.0", "paper": str(secret),
                    "authors": [], "abstract": "a", "keywords": []}
            out = base / "dist"
            with mock.patch.object(pr, "validate", return_value=(0, evil)):
                with self.assertRaisesRegex(ValueError, "paper path must stay inside"):
                    pr.create_bundle(out, None, None)
            self.assertFalse((out / "paper.pdf").exists())

    """AUD-15: PDF associated files (/AF, /EF) must be rejected."""

    def test_pdf_af_embedded_file_is_rejected(self):
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import ArrayObject, NameObject
        import pdf_validation
        with tempfile.TemporaryDirectory() as td:
            pdf = Path(td) / "paper.pdf"
            w = PdfWriter()
            w.add_blank_page(width=595, height=842)
            w.add_attachment("payload.txt", b"EMBEDDED-MALICIOUS-PAYLOAD")
            with pdf.open("wb") as handle:
                w.write(handle)
            reader = PdfReader(pdf)
            catalog = reader.trailer["/Root"]
            filespec = catalog["/Names"]["/EmbeddedFiles"]["/Names"][1]
            catalog[NameObject("/AF")] = ArrayObject([filespec])
            del catalog[NameObject("/Names")]
            w2 = PdfWriter(clone_from=reader)
            with pdf.open("wb") as handle:
                w2.write(handle)
            with self.assertRaisesRegex(ValueError, "interactive/embedded content"):
                pdf_validation.inspect_pdf(pdf)

    """AUD-16: annotation actions (/A /S /Launch) must be rejected."""

    def test_pdf_annotation_launch_action_is_rejected(self):
        from pypdf import PdfWriter
        from pypdf.generic import (ArrayObject, DictionaryObject, NameObject,
                                   TextStringObject, FloatObject)
        import pdf_validation
        with tempfile.TemporaryDirectory() as td:
            pdf = Path(td) / "paper.pdf"
            w = PdfWriter()
            page = w.add_blank_page(width=595, height=842)
            action = DictionaryObject({NameObject("/S"): NameObject("/Launch"),
                                       NameObject("/F"): TextStringObject("calc.exe")})
            annot = DictionaryObject({
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Link"),
                NameObject("/Rect"): ArrayObject([FloatObject(0), FloatObject(0),
                                                  FloatObject(10), FloatObject(10)]),
                NameObject("/A"): action,
            })
            page[NameObject("/Annots")] = ArrayObject([annot])
            with pdf.open("wb") as handle:
                w.write(handle)
            with self.assertRaisesRegex(ValueError, "interactive/embedded content"):
                pdf_validation.inspect_pdf(pdf)

    """AUD-17: an oversized key file must not be fully materialized."""

    def test_oversized_key_is_bounded(self):
        import private_seal as ps
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "rec"
            source.write_bytes(b"synthetic")
            key = b"K" * 32
            rid = "0" * 32
            commitment = ps.commit_file(source, key)
            receipt = base / (rid + ".json")
            receipt.write_text(json.dumps({"schema_version": 1, "record_id": rid,
                                           "algorithm": "HMAC-SHA256", "commitment": commitment}),
                               encoding="utf-8")
            huge = base / "huge.key"
            with huge.open("wb") as handle:
                handle.truncate(ps.MAX_BYTES + 1)
            seen = {}
            real = ps.commit_file
            ps.commit_file = lambda p, k: (seen.setdefault("n", len(k)), commitment)[1]
            try:
                with self.assertRaisesRegex(ValueError, "32 bytes"):
                    ps.verify(source, huge, receipt)
            finally:
                ps.commit_file = real
            self.assertLessEqual(seen.get("n", 0), 33)


if __name__ == "__main__":
    unittest.main()
