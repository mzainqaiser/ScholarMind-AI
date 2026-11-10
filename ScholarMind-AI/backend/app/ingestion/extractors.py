"""Text extraction. Each extractor returns Sections so page/heading metadata survives to citations."""
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

SUPPORTED_TYPES = {"pdf", "docx", "txt", "md"}


class ExtractionError(Exception):
    pass


@dataclass
class Section:
    text: str
    page: Optional[int] = None       # 1-based page number (PDF only)
    heading: Optional[str] = None    # nearest heading (DOCX / Markdown)


def clean_text(text: str) -> str:
    """Normalise whitespace but keep paragraph breaks; rejoin words hyphenated across line breaks."""
    text = text.replace("\x00", "")
    text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", "", text)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def verify_magic(path: Path, file_type: str) -> None:
    """Reject files whose content does not match the claimed extension."""
    head = path.read_bytes()[:8]
    if file_type == "pdf" and not head.startswith(b"%PDF"):
        raise ExtractionError("File content is not a valid PDF.")
    if file_type == "docx" and not (head.startswith(b"PK") and zipfile.is_zipfile(path)):
        raise ExtractionError("File content is not a valid DOCX.")
    if file_type in ("txt", "md") and b"\x00" in path.read_bytes()[:4096]:
        raise ExtractionError("File looks binary, not text.")


def extract_pdf(path: Path):
    import pymupdf
    try:
        doc = pymupdf.open(path)
    except Exception as exc:
        raise ExtractionError(f"Could not open PDF: {exc}") from exc
    sections = []
    for i, page in enumerate(doc, start=1):
        text = clean_text(page.get_text("text"))
        if text:
            sections.append(Section(text=text, page=i))
    return sections, len(doc)


def extract_docx(path: Path):
    import docx
    try:
        d = docx.Document(str(path))
    except Exception as exc:
        raise ExtractionError(f"Could not open DOCX: {exc}") from exc
    sections, heading, buf = [], None, []

    def flush():
        if buf:
            sections.append(Section(text=clean_text("\n".join(buf)), heading=heading))
            buf.clear()

    for p in d.paragraphs:
        if not p.text.strip():
            continue
        if (p.style.name or "").lower().startswith(("heading", "title")):
            flush()
            heading = p.text.strip()
            buf.append(heading)
        else:
            buf.append(p.text)
    flush()
    return [s for s in sections if s.text], None


def extract_text_file(path: Path, markdown: bool):
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    if not markdown:
        return [Section(text=clean_text(text))], None
    sections, heading, buf = [], None, []
    for line in text.splitlines():
        m = re.match(r"^#{1,6}\s+(.*)", line)
        if m:
            if buf:
                sections.append(Section(text=clean_text("\n".join(buf)), heading=heading))
                buf = []
            heading = m.group(1).strip()
        buf.append(line)
    if buf:
        sections.append(Section(text=clean_text("\n".join(buf)), heading=heading))
    return [s for s in sections if s.text], None


def extract(path: Path, file_type: str):
    """Return (sections, page_count). Raises ExtractionError on unreadable or empty documents."""
    if file_type not in SUPPORTED_TYPES:
        raise ExtractionError(f"Unsupported file type: {file_type}")
    verify_magic(path, file_type)
    if file_type == "pdf":
        sections, pages = extract_pdf(path)
    elif file_type == "docx":
        sections, pages = extract_docx(path)
    else:
        sections, pages = extract_text_file(path, markdown=(file_type == "md"))
    if not sections:
        raise ExtractionError("No extractable text found (scanned PDFs need OCR, which is not supported).")
    return sections, pages
