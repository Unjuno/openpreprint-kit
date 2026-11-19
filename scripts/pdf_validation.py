#!/usr/bin/env python3
"""Bounded PDF publication preflight (structure only, never a malware scan).

Requires pypdf==6.21.4. An accepted PDF is still UNTRUSTED to renderers.
"""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, NameObject

MAX_PDF_BYTES = 25 * 1024 * 1024
MAX_PAGES = 500
MAX_GRAPH_OBJECTS = 50000
MAX_GRAPH_DEPTH = 160
REJECT_KEYS = frozenset({
    "/AA", "/AcroForm", "/OpenAction", "/JS", "/JavaScript", "/Launch",
    "/EmbeddedFiles", "/AF", "/EF", "/Filespec", "/RichMedia", "/XFA",
    "/GoToR", "/SubmitForm", "/ImportData", "/Movie", "/Sound", "/3D",
    "/Rendition",
})
# These appear as the VALUE of /S (action type) or /Subtype (annotation type),
# e.g. an annotation /A << /S /Launch /F ... >>. Key-only checks miss them.
REJECT_NAMES = frozenset({
    "/Launch", "/GoToR", "/SubmitForm", "/ImportData", "/Movie", "/Sound",
    "/3D", "/Rendition", "/RichMedia", "/JavaScript", "/JS", "/EmbeddedFiles",
})


def inspect_pdf(path: Path) -> tuple[int, int]:
    """Return (byte length, page count), or raise ValueError on unsafe/invalid input.

    The check is NOT a conformance certificate, PDF/A validator, or antivirus.
    """
    if path.is_symlink() or not path.is_file():
        raise ValueError("PDF must be a regular non-symlink file")
    size = path.stat().st_size
    if size == 0 or size > MAX_PDF_BYTES:
        raise ValueError("PDF file must be nonempty and at most 25 MiB")
    with path.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise ValueError("PDF signature is missing")
        try:
            reader = PdfReader(stream, strict=True)
            if reader.is_encrypted:
                raise ValueError("encrypted PDFs cannot be published")
            pages = len(reader.pages)
            if pages == 0 or pages > MAX_PAGES:
                raise ValueError("PDF page count must be 1..500")
            # Traverse the COS graph without extracting or executing embedded content.
            # Includes the catalog, pages, annotations and /Names (embedded files).
            stack: list[tuple[object, int]] = [(reader.trailer, 0)]
            seen_indirect: set[tuple[int, int]] = set()
            seen_direct: set[int] = set()
            count = 0
            while stack:
                value, depth = stack.pop()
                count += 1
                if count > MAX_GRAPH_OBJECTS or depth > MAX_GRAPH_DEPTH:
                    raise ValueError("PDF object graph exceeds the safety limit")
                if isinstance(value, IndirectObject):
                    ref = (value.idnum, value.generation)
                    if ref in seen_indirect:
                        continue
                    seen_indirect.add(ref)
                    stack.append((value.get_object(), depth + 1))
                elif isinstance(value, DictionaryObject):
                    if id(value) in seen_direct:
                        continue
                    seen_direct.add(id(value))
                    forbidden = set(REJECT_KEYS.intersection(map(str, value.keys())))
                    for key in (NameObject("/S"), NameObject("/Subtype")):
                        if key in value:
                            item = value.raw_get(key)
                            if isinstance(item, NameObject) and str(item) in REJECT_NAMES:
                                forbidden.add(str(item))
                    if forbidden:
                        raise ValueError("PDF contains interactive/embedded content: " + ", ".join(sorted(forbidden)))
                    # raw_get preserves indirect references and avoids decoding streams.
                    stack.extend((value.raw_get(key), depth + 1) for key in value.keys())
                elif isinstance(value, ArrayObject):
                    if id(value) in seen_direct:
                        continue
                    seen_direct.add(id(value))
                    stack.extend((part, depth + 1) for part in value)
            return size, pages
        except ValueError:
            raise
        except (Exception,) as exc:
            # Strict publication must fail closed for malformed or unsupported PDFs.
            raise ValueError(f"invalid PDF structure: {type(exc).__name__}: {exc}") from None
