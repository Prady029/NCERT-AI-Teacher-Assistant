"""Build curriculum map JSON files from the official NCERT textbook catalogue.

This script is deliberately conservative about accuracy:

* Book codes, textbook titles, and chapter ranges are copied from the official
  catalogue page (https://ncert.nic.in/textbook.php) and marked catalogue-verified.
* Chapter names, learning outcomes, and exam blueprints are **not** invented. The
  generated maps leave ``chapters`` empty and set ``chapter_details_verified`` to
  false until a contributor verifies them against the current textbook/syllabus.

Regenerate from the project's backend environment:

    uv run python scripts/build_curriculum_maps.py

``data/curriculum/*.json`` files that already contain verified chapter detail are
never overwritten: the script refuses and tells you to move them to
``data/curriculum/verified/`` first.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import requests

try:  # imported as a module (tests) or executed as a script (direct invocation)
    from scripts.scrape_ncert import (
        CATALOG_URL,
        USER_AGENT,
        BookRecord,
        discover_books,
        fetch_catalogue,
    )
except ImportError:  # pragma: no cover - script execution path
    from scrape_ncert import (  # type: ignore[no-redef]
        CATALOG_URL,
        USER_AGENT,
        BookRecord,
        discover_books,
        fetch_catalogue,
    )

LOG = logging.getLogger("curriculum_builder")

DISCLAIMER = (
    "Book code and chapter range come from the official NCERT textbook catalogue. "
    "Chapter titles, learning outcomes, and assessment blueprints are intentionally "
    "omitted because they were not verified. Verify against the current NCERT textbook "
    "and CBSE syllabus for the academic year before classroom use, and check NCERT's "
    "current copyright/terms notice before retaining or redistributing textbook content."
)


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def load_existing_curated(curriculum_dir: Path) -> set[str]:
    """Return slugs of existing maps that appear to contain verified chapter detail."""
    curated: set[str] = set()
    for path in curriculum_dir.glob("*.json"):
        if path.name == "catalogue_index.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("chapter_details_verified") and data.get("chapters"):
            curated.add(path.name)
    return curated


def select_primary_book(books: List[BookRecord]) -> BookRecord:
    """Pick the book whose displayed title equals the catalogue subject label.

    Localised titles (for example "Vigyan" for Hindi-medium Science) do not equal
    the subject label, so the exact-title match tends to select the English book.
    Falls back to the first catalogue option and records the uncertainty.
    """
    for book in books:
        if book.title.strip().casefold() == book.subject.strip().casefold():
            return book
    return books[0]


def book_to_dict(book: BookRecord) -> Dict[str, object]:
    return {
        "title": book.title,
        "book_code": book.book_code,
        "first_chapter": book.first_chapter,
        "last_chapter": book.last_chapter,
        "catalogue_url": book.catalogue_url,
    }


def build_maps(books: List[BookRecord], curriculum_dir: Path, retrieved_at: str) -> Tuple[int, int]:
    grouped: Dict[Tuple[int, str], List[BookRecord]] = defaultdict(list)
    for book in books:
        grouped[(book.class_level, book.subject)].append(book)

    curriculum_dir.mkdir(parents=True, exist_ok=True)
    curated = load_existing_curated(curriculum_dir)

    written = 0
    skipped = 0
    for (class_level, subject), options in sorted(grouped.items()):
        filename = f"{slugify(subject)}_class_{class_level}.json"
        if filename in curated:
            LOG.warning("Skipping %s: contains verified chapter detail; move it to verified/ first", filename)
            skipped += 1
            continue

        primary = select_primary_book(options)
        payload = {
            "subject": slugify(subject),
            "subject_label": subject,
            "class": class_level,
            "source": "ncert_textbook_catalogue",
            "source_url": CATALOG_URL,
            "catalogue_verified": True,
            "chapter_details_verified": False,
            "catalogue_retrieved_at": retrieved_at,
            "primary_book": book_to_dict(primary),
            "primary_book_selection": (
                "exact subject-title match"
                if primary.title.strip().casefold() == subject.strip().casefold()
                else "first catalogue option; verify language/edition"
            ),
            "books": [book_to_dict(book) for book in options],
            "chapters": [],
            "disclaimer": DISCLAIMER,
        }
        (curriculum_dir / filename).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        written += 1

    return written, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--curriculum-dir", type=Path, default=Path("../data/curriculum"))
    parser.add_argument("--written-at", default=None, help="Override retrieval timestamp (testing)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    books = discover_books(fetch_catalogue(session))
    LOG.info("Discovered %d book options from the NCERT catalogue", len(books))

    retrieved_at = args.written_at or datetime.now(timezone.utc).isoformat(timespec="seconds")

    curriculum_dir = args.curriculum_dir
    catalogue_index = curriculum_dir / "catalogue_index.json"
    curriculum_dir.mkdir(parents=True, exist_ok=True)
    catalogue_index.write_text(
        json.dumps(
            {
                "source": "ncert_textbook_catalogue",
                "source_url": CATALOG_URL,
                "catalogue_verified": True,
                "catalogue_retrieved_at": retrieved_at,
                "book_count": len(books),
                "books": [
                    book_to_dict(book)
                    | {
                        "class_level": book.class_level,
                        "subject": book.subject,
                        "subject_slug": slugify(book.subject),
                    }
                    for book in books
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    LOG.info("Wrote %s (%d books)", catalogue_index, len(books))

    written, skipped = build_maps(books, curriculum_dir, retrieved_at)
    LOG.info("Wrote %d curriculum map(s); skipped %d verified map(s)", written, skipped)


if __name__ == "__main__":
    main()
