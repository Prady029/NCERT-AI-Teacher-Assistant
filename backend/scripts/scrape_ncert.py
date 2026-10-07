"""Discover official NCERT textbook codes and download/extract chapter PDFs.

Source: https://ncert.nic.in/textbook.php

NCERT's textbook catalogue defines book codes and chapter ranges in the
JavaScript on that official page. This script reads that catalogue instead of
assuming made-up ``?subject=...&class=...`` query parameters. Use downloaded
content only in accordance with NCERT's current copyright/terms notice.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import time
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin

import requests

LOG = logging.getLogger("ncert_scraper")
CATALOG_URL = "https://ncert.nic.in/textbook.php"
PDF_BASE_URL = "https://ncert.nic.in/textbook/pdf/"
USER_AGENT = "NCERT-AI-Teacher-Assistant/0.1 (educational indexing; respectful rate limits)"
# Chapter PDFs are named <book_code><NN>.pdf (e.g. jesc101.pdf). Supplementary
# files use two-letter suffixes instead of a number (jesc1ps.pdf, jesc1an.pdf).
CHAPTER_PDF_RE = re.compile(r"^(?P<code>[a-z0-9]+?)(?P<number>\d{2})(?:\.pdf)?$", re.I)
SUPPLEMENT_PDF_RE = re.compile(r"^(?P<code>[a-z0-9]+?)(?P<suffix>[a-z]{2})(?:\.pdf)?$", re.I)


@dataclass
class BookRecord:
    class_level: int
    subject: str
    title: str
    book_code: str
    first_chapter: int
    last_chapter: int
    catalogue_url: str

    @property
    def chapter_count(self) -> int:
        return max(0, self.last_chapter - self.first_chapter + 1)


@dataclass
class ChapterRecord:
    number: Optional[int]
    label: str
    title: str
    source_url: str
    pdf_path: str
    text_path: str
    text_available: bool = True


@dataclass
class BookResult:
    """Outcome of one book acquisition, including partial failures."""

    book: BookRecord
    method: str
    items: List[ChapterRecord]
    failures: List[str]


def fetch_catalogue(session: requests.Session) -> str:
    response = session.get(CATALOG_URL, timeout=45)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.text


def discover_books(html: str) -> List[BookRecord]:
    """Parse class/subject -> NCERT book code mappings from catalogue JS."""
    # The official page populates the subject book selector in change1(sind).
    # Pair each option index's displayed title with its textbook.php code/range.
    block_re = re.compile(
        r'(?:if|else\s+if)\s*\(\s*\(?document\.test\.tclass\.value\s*==\s*(\d+)'
        r'.*?document\.test\.tsubject\.options\[sind\]\.text\s*==\s*"([^"]+)".*?\)\s*\{'
        r'(.*?)(?=\n\s*\}\s*else\s+if\s*\(\s*\(?document\.test\.tclass\.value|\n\s*\}\s*\n\s*function\s|\Z)',
        flags=re.S,
    )
    option_re = re.compile(
        r'document\.test\.tbook\.options\[(\d+)\]\.text\s*=\s*"([^"]*)"\s*;'
        r'\s*document\.test\.tbook\.options\[\1\]\.value\s*=\s*"textbook\.php\?([a-zA-Z0-9]+)=(\d+)-(\d+)"',
        flags=re.S,
    )
    books: List[BookRecord] = []
    for block in block_re.finditer(html):
        class_level = int(block.group(1))
        subject = block.group(2).strip()
        body = block.group(3)
        for option in option_re.finditer(body):
            title, code = option.group(2).strip(), option.group(3)
            first_chapter, last_chapter = int(option.group(4)), int(option.group(5))
            if title and code:
                books.append(BookRecord(
                    class_level=class_level,
                    subject=subject,
                    title=title,
                    book_code=code,
                    first_chapter=first_chapter,
                    last_chapter=last_chapter,
                    catalogue_url=f"{CATALOG_URL}?{code}={first_chapter}-{last_chapter}",
                ))
    # De-duplicate options which occur in repeated catalogue branches.
    return list({(b.class_level, b.subject, b.title, b.book_code): b for b in books}.values())


def download_chapter_pdf(session: requests.Session, book: BookRecord, number: int, destination: Path) -> str:
    """Download a chapter PDF using NCERT's catalogue naming convention."""
    # NCERT chapter files use book-code + two-digit chapter number, e.g.
    # jesc101.pdf for chapter 1 of book code jesc1.
    url = urljoin(PDF_BASE_URL, f"{book.book_code}{number:02d}.pdf")
    response = session.get(url, timeout=90)
    response.raise_for_status()
    if not response.content.startswith(b"%PDF"):
        raise ValueError(f"NCERT returned a non-PDF response for {url}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response.content)
    return url


def extract_pdf_text(pdf_path: Path) -> tuple[str, str]:
    """Extract searchable text and infer the chapter title from PDF pages.

    Returns ``(title, text)``. ``title`` is inferred from the first lines of the
    PDF and is *not* authoritative textbook metadata; verify it before use.
    """
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install pypdf to extract chapter text: pip install pypdf") from exc

    reader = PdfReader(str(pdf_path))
    pages = [page.extract_text(extraction_mode="layout") or "" for page in reader.pages]
    text = "\n\n".join(page.strip() for page in pages if page.strip())
    first_lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = " — ".join(first_lines[:2])[:240] if first_lines else pdf_path.stem
    return title, text


def download_full_book_zip(session: requests.Session, book: BookRecord, destination: Path) -> str:
    """Download the official complete-book archive (``<code>dd.zip``)."""
    url = urljoin(PDF_BASE_URL, f"{book.book_code}dd.zip")
    response = session.get(url, timeout=300)
    response.raise_for_status()
    if response.content[:2] != b"PK":
        raise ValueError(f"NCERT returned a non-ZIP response for {url}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response.content)
    return url


def extract_zip_safely(zip_path: Path, target_dir: Path) -> List[Path]:
    """Extract a ZIP, rejecting entries that would escape ``target_dir``."""
    target_dir.mkdir(parents=True, exist_ok=True)
    extracted: List[Path] = []
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            member_path = Path(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError(f"Refusing unsafe ZIP entry: {member.filename}")
            destination = target_dir / member_path.name
            with archive.open(member) as source, open(destination, "wb") as out:
                out.write(source.read())
            extracted.append(destination)
    return extracted


def _label_and_number(pdf_name: str, book: BookRecord) -> tuple[Optional[int], str, str]:
    """Map a chapter/supplement PDF filename to ``(number, label, text_stem)``.

    Both acquisition modes produce the same text-file naming (``chapter_01``,
    ``supplement_ps``) so downstream indexing sees a consistent layout.
    """
    stem = Path(pdf_name).stem.lower()
    prefix = book.book_code.lower()
    remainder = stem[len(prefix):] if stem.startswith(prefix) else stem
    if remainder.isdigit():
        number = int(remainder)
        return number, f"Chapter {number}", f"chapter_{number:02d}"
    if remainder:
        return None, f"Supplement '{remainder}'", f"supplement_{remainder}"
    return None, pdf_name, stem


def _extract_records(
    pdfs: List[tuple[Optional[int], str, str, Path, Path]],
) -> tuple[List[ChapterRecord], List[str]]:
    """Extract text for already-downloaded PDFs, collecting per-file failures."""
    records: List[ChapterRecord] = []
    failures: List[str] = []
    for number, label, source_url, pdf_path, text_path in pdfs:
        try:
            title, text = extract_pdf_text(pdf_path)
            text_available = bool(text.strip())
            text_path.write_text(text, encoding="utf-8")
            if not text_available:
                LOG.warning("No extractable text in %s (scanned page or layout issue); retained the PDF", pdf_path)
            records.append(ChapterRecord(number, label, title, source_url, str(pdf_path), str(text_path), text_available))
            LOG.info("Extracted %s — %s (%s)", pdf_path.name, label, title)
        except Exception as exc:  # pypdf can raise many PDF-specific errors
            failures.append(f"{pdf_path.name}: {exc}")
            LOG.warning("Could not extract text from %s: %s", pdf_path.name, exc)
    return records, failures


def book_dir_for(output_dir: Path, book: BookRecord) -> Path:
    return output_dir / f"class_{book.class_level}" / re.sub(r"[^a-z0-9]+", "_", book.subject.lower()) / book.book_code


def scrape_book_chapters(session: requests.Session, book: BookRecord, output_dir: Path, delay: float) -> BookResult:
    """Download and extract each chapter PDF individually."""
    book_dir = book_dir_for(output_dir, book)
    pdfs: List[tuple[Optional[int], str, str, Path, Path]] = []
    failures: List[str] = []
    # first_chapter may be 0 in the catalogue; chapters themselves start at 01.
    for number in range(max(1, book.first_chapter), book.last_chapter + 1):
        pdf_path = book_dir / f"chapter_{number:02d}.pdf"
        text_path = book_dir / f"chapter_{number:02d}.txt"
        try:
            source_url = download_chapter_pdf(session, book, number, pdf_path)
            pdfs.append((number, f"Chapter {number}", source_url, pdf_path, text_path))
        except (requests.RequestException, ValueError) as exc:
            failures.append(f"chapter {number}: {exc}")
            LOG.warning("Could not download %s chapter %d: %s", book.book_code, number, exc)
        time.sleep(delay)
    records, extract_failures = _extract_records(pdfs)
    return BookResult(book, "chapters", records, failures + extract_failures)


def scrape_book_full(session: requests.Session, book: BookRecord, output_dir: Path, delay: float) -> BookResult:
    """Download the complete-book ZIP, extract all PDFs, and extract their text."""
    book_dir = book_dir_for(output_dir, book)
    zip_path = book_dir / f"{book.book_code}dd.zip"
    try:
        zip_url = download_full_book_zip(session, book, zip_path)
    except (requests.RequestException, ValueError) as exc:
        return BookResult(book, "full_book", [], [f"zip download: {exc}"])

    try:
        extracted = extract_zip_safely(zip_path, book_dir / "pdf")
    except (zipfile.BadZipFile, ValueError) as exc:
        return BookResult(book, "full_book", [], [f"zip extraction: {exc}"])

    pdf_dir = book_dir / "pdf"
    pdfs: List[tuple[Optional[int], str, str, Path, Path]] = []
    for pdf_path in sorted(extracted):
        if pdf_path.suffix.lower() != ".pdf":
            continue
        number, label, text_stem = _label_and_number(pdf_path.name, book)
        pdfs.append((number, label, zip_url, pdf_path, pdf_dir / f"{text_stem}.txt"))

    records, extract_failures = _extract_records(pdfs)
    return BookResult(book, "full_book", records, extract_failures)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--class", dest="class_level", type=int, help="NCERT class (1–12)")
    parser.add_argument("--subject", help="Catalogue subject label, e.g. Science")
    parser.add_argument("--book-code", help="Optional exact NCERT book code")
    parser.add_argument("--download", action="store_true", help="Download content and extract text")
    parser.add_argument(
        "--mode",
        choices=["chapters", "full", "both"],
        default="chapters",
        help=(
            "chapters: download each chapter PDF; full: download the complete-book ZIP; "
            "both: try the ZIP first and fall back to per-chapter downloads"
        ),
    )
    parser.add_argument("--output", type=Path, default=Path("data/ncert_raw"))
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between chapter requests in seconds")
    parser.add_argument("--catalogue-json", type=Path, help="Write discovered catalogue as JSON")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    books = discover_books(fetch_catalogue(session))
    LOG.info("Discovered %d book options from NCERT catalogue", len(books))

    if args.catalogue_json:
        args.catalogue_json.parent.mkdir(parents=True, exist_ok=True)
        args.catalogue_json.write_text(
            json.dumps([asdict(book) for book in books], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    selected = [book for book in books if
                (args.class_level is None or book.class_level == args.class_level) and
                (args.subject is None or book.subject.casefold() == args.subject.casefold()) and
                (args.book_code is None or book.book_code == args.book_code)]
    if args.class_level is not None and args.subject and not selected:
        raise SystemExit("No matching book found. First write catalogue JSON and inspect exact NCERT subject/title labels.")

    if not args.download:
        print(json.dumps([asdict(book) for book in selected], ensure_ascii=False, indent=2))
        return
    if not selected:
        raise SystemExit("Select a textbook with --class and --subject before using --download")
    if args.delay < 0.5:
        raise SystemExit("Use a request delay of at least 0.5 seconds to avoid overloading NCERT")

    for book in selected:
        results: List[BookResult] = []
        if args.mode in {"full", "both"}:
            full_result = scrape_book_full(session, book, args.output, args.delay)
            if full_result.items or args.mode == "full":
                results.append(full_result)
        if args.mode in {"chapters", "both"} and not any(r.method == "full_book" and r.items for r in results):
            results.append(scrape_book_chapters(session, book, args.output, args.delay))

        index_path = args.output / f"class_{book.class_level}_{book.book_code}_index.json"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(
            json.dumps(
                {
                    "book": asdict(book),
                    "acquisitions": [asdict(result) for result in results],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        for result in results:
            LOG.info(
                "%s via %s: %d item(s), %d failure(s)",
                book.book_code, result.method, len(result.items), len(result.failures),
            )


if __name__ == "__main__":
    main()
