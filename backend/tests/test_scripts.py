"""Unit tests for data-prep scripts (no network access required)."""

import json
import zipfile
from pathlib import Path

import pytest

from scripts import scrape_ncert
from scripts.build_curriculum_maps import DISCLAIMER, build_maps, slugify
from scripts.scrape_ncert import (
    BookRecord,
    _label_and_number,
    extract_zip_safely,
    scrape_book_full,
)


def make_book(**overrides) -> BookRecord:
    values = {
        "class_level": 10,
        "subject": "Science",
        "title": "Science",
        "book_code": "jesc1",
        "first_chapter": 0,
        "last_chapter": 13,
        "catalogue_url": "https://ncert.nic.in/textbook.php?jesc1=0-13",
    }
    values.update(overrides)
    return BookRecord(**values)


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("Social Science", "social_science"),
        ("Creative Writing & Translation", "creative_writing_translation"),
        ("Physical Education and Well Being", "physical_education_and_well_being"),
    ],
)
def test_slugify(label, expected):
    assert slugify(label) == expected


def test_label_and_number_recognises_chapters_and_supplements():
    book = make_book()
    assert _label_and_number("jesc101.pdf", book) == (1, "Chapter 1", "chapter_01")
    assert _label_and_number("jesc113.pdf", book) == (13, "Chapter 13", "chapter_13")
    number, label, stem = _label_and_number("jesc1ps.pdf", book)
    assert number is None and "ps" in label and stem == "supplement_ps"


def test_build_maps_marks_catalogue_verified_and_chapters_unverified(tmp_path: Path):
    books = [
        make_book(),
        make_book(title="Vigyan", book_code="jhsc1"),
        make_book(class_level=11, subject="Nepali", title="Nepali", book_code="knpa1"),
    ]
    written, skipped = build_maps(books, tmp_path, "2026-01-01T00:00:00+00:00")
    assert written == 2 and skipped == 0

    science = json.loads((tmp_path / "science_class_10.json").read_text(encoding="utf-8"))
    assert science["catalogue_verified"] is True
    assert science["chapter_details_verified"] is False
    assert science["chapters"] == []
    assert science["primary_book"]["book_code"] == "jesc1"
    assert science["disclaimer"] == DISCLAIMER
    # The Hindi-medium title should not be selected when "Science" matches exactly.
    assert science["primary_book"]["title"] == "Science"


def test_build_maps_does_not_overwrite_verified_maps(tmp_path: Path):
    verified = {
        "chapter_details_verified": True,
        "chapters": [{"number": 1, "name": "Verified chapter"}],
    }
    (tmp_path / "science_class_10.json").write_text(json.dumps(verified), encoding="utf-8")
    written, skipped = build_maps([make_book()], tmp_path, "2026-01-01T00:00:00+00:00")
    assert (written, skipped) == (0, 1)
    still = json.loads((tmp_path / "science_class_10.json").read_text(encoding="utf-8"))
    assert still["chapters"][0]["name"] == "Verified chapter"


def make_zip(path: Path, names) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        for name in names:
            archive.writestr(name, b"%PDF-1.4 fake")
    return path


def test_extract_zip_safely_extracts_flat_files(tmp_path: Path):
    archive = make_zip(tmp_path / "book.zip", ["jesc101.pdf", "jesc1ps.pdf"])
    out = extract_zip_safely(archive, tmp_path / "out")
    assert sorted(p.name for p in out) == ["jesc101.pdf", "jesc1ps.pdf"]


def test_extract_zip_safely_rejects_path_traversal(tmp_path: Path):
    archive = make_zip(tmp_path / "evil.zip", ["../escape.pdf"])
    with pytest.raises(ValueError, match="unsafe ZIP entry"):
        extract_zip_safely(archive, tmp_path / "out")
    assert not (tmp_path / "escape.pdf").exists()


def test_scrape_book_full_orchestration(tmp_path: Path, monkeypatch):
    """Full-book mode labels chapters/supplements and extracts text without network."""
    fake_zip = make_zip(
        tmp_path / "jesc1dd.zip",
        ["jesc101.pdf", "jesc102.pdf", "jesc1ps.pdf", "jesc1an.pdf"],
    )

    def fake_download(session, book, destination):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(fake_zip.read_bytes())
        return "https://ncert.nic.in/textbook/pdf/jesc1dd.zip"

    monkeypatch.setattr(scrape_ncert, "download_full_book_zip", fake_download)
    monkeypatch.setattr(
        scrape_ncert,
        "extract_pdf_text",
        lambda path: (f"Title of {path.name}", f"text of {path.name}"),
    )

    result = scrape_book_full(None, make_book(), tmp_path / "out", delay=0.0)

    assert result.method == "full_book"
    assert result.failures == []
    labels = {(item.number, item.label) for item in result.items}
    assert (1, "Chapter 1") in labels
    assert (2, "Chapter 2") in labels
    assert any(item.number is None and item.label.startswith("Supplement") for item in result.items)
    assert all(item.text_available for item in result.items)
    # Text files are written next to the extracted PDFs.
    assert (tmp_path / "out/class_10/science/jesc1/pdf/chapter_01.txt").exists()


def test_scrape_book_full_records_zip_download_failure(tmp_path: Path, monkeypatch):
    def failing_download(session, book, destination):
        raise ValueError("NCERT returned a non-ZIP response")

    monkeypatch.setattr(scrape_ncert, "download_full_book_zip", failing_download)
    result = scrape_book_full(None, make_book(), tmp_path / "out", delay=0.0)
    assert result.items == []
    assert result.failures and "zip download" in result.failures[0]
