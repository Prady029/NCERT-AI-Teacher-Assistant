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
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List
from urllib.parse import urljoin

import requests

LOG = logging.getLogger("ncert_scraper")
CATALOG_URL = "https://ncert.nic.in/textbook.php"
PDF_BASE_URL = "https://ncert.nic.in/textbook/pdf/"
USER_AGENT = "NCERT-AI-Teacher-Assistant/0.1 (educational indexing; respectful rate limits)"


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
    number: int
    title: str
    source_url: str
    pdf_path: str
    text_path: str


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
    """Extract searchable text and infer the chapter title from PDF pages."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install pypdf to extract chapter text: pip install pypdf") from exc

    reader = PdfReader(str(pdf_path))
    pages = [page.extract_text(extraction_mode="layout") or "" for page in reader.pages]
    text = "\n\n".join(page.strip() for page in pages if page.strip())
    # The first non-empty lines usually include chapter number/title. Keep this
    # as an inferred title, not authoritative metadata, for teacher verification.
    first_lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = " — ".join(first_lines[:2])[:240] if first_lines else pdf_path.stem
    return title, text


def scrape_book(session: requests.Session, book: BookRecord, output_dir: Path, delay: float) -> List[ChapterRecord]:
    records: List[ChapterRecord] = []
    book_dir = output_dir / f"class_{book.class_level}" / re.sub(r"[^a-z0-9]+", "_", book.subject.lower()) / book.book_code
    for number in range(max(1, book.first_chapter), book.last_chapter + 1):
        pdf_path = book_dir / f"chapter_{number:02d}.pdf"
        text_path = book_dir / f"chapter_{number:02d}.txt"
        try:
            source_url = download_chapter_pdf(session, book, number, pdf_path)
            title, text = extract_pdf_text(pdf_path)
            if not text.strip():
                LOG.warning("No extractable text in %s; retained the PDF", pdf_path)
            text_path.write_text(text, encoding="utf-8")
            records.append(ChapterRecord(number, title, source_url, str(pdf_path), str(text_path)))
            LOG.info("Downloaded %s — chapter %d (%s)", book.title, number, title)
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            LOG.warning("Could not download/extract %s chapter %d: %s", book.book_code, number, exc)
        time.sleep(delay)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--class", dest="class_level", type=int, help="NCERT class (1–12)")
    parser.add_argument("--subject", help="Catalogue subject label, e.g. Science")
    parser.add_argument("--book-code", help="Optional exact NCERT book code")
    parser.add_argument("--download", action="store_true", help="Download chapter PDFs and extract text")
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
        chapters = scrape_book(session, book, args.output, args.delay)
        index_path = args.output / f"class_{book.class_level}_{book.book_code}_index.json"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(json.dumps({"book": asdict(book), "chapters": [asdict(c) for c in chapters]}, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
