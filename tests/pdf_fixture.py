"""Test-only PDF fixtures. These are not scholarly papers."""
from pathlib import Path
from pypdf import PdfWriter


def write_pdf(path: Path, *, pages: int = 1, javascript: bool = False,
              encrypted: bool = False, attachment: bool = False) -> None:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=595, height=842)
    if javascript:
        writer.add_js("app.alert('test-only, never execute')")
    if encrypted:
        writer.encrypt("test-password")
    if attachment:
        writer.add_attachment("test.txt", b"not for release")
    with path.open("wb") as stream:
        writer.write(stream)
