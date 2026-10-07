"""Tests for the local curriculum/textbook loader (no network access)."""

from pathlib import Path

from app.models.schemas import ClassLevel, Subject
from app.services.rag_service import NCERTDataLoader


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_loads_full_book_zip_layout(tmp_path: Path):
    # Complete-book ZIP layout: <class>/<subject>/<book>/pdf/*.txt
    write(tmp_path / "ncert_raw/class_10/science/jesc1/pdf/chapter_01.txt", "photosynthesis")
    write(tmp_path / "ncert_raw/class_10/science/jesc1/pdf/supplement_ps.txt", "prelims")
    loader = NCERTDataLoader(data_dir=str(tmp_path))

    chapters = loader.load_all_chapters(Subject.SCIENCE, ClassLevel.CLASS_10)
    assert set(chapters) == {"chapter_01", "supplement_ps"}

    docs = loader.prepare_rag_documents(Subject.SCIENCE, ClassLevel.CLASS_10)
    assert len(docs) == 2
    assert docs[0]["metadata"]["subject"] == "science"
    assert docs[0]["metadata"]["class_level"] == 10


def test_loads_per_chapter_layout(tmp_path: Path):
    # Per-chapter layout: <class>/<subject>/<book>/*.txt
    write(tmp_path / "ncert_raw/class_9/mathematics/kemh1/chapter_01.txt", "number systems")
    loader = NCERTDataLoader(data_dir=str(tmp_path))
    chapters = loader.load_all_chapters(Subject.MATHEMATICS, ClassLevel.CLASS_9)
    assert chapters == {"chapter_01": "number systems"}


def test_chapter_lookup_strips_directory_components(tmp_path: Path):
    write(tmp_path / "ncert_raw/class_10/science/jesc1/pdf/chapter_02.txt", "acids")
    loader = NCERTDataLoader(data_dir=str(tmp_path))
    assert loader.load_chapter_content(Subject.SCIENCE, ClassLevel.CLASS_10, "chapter_02") == "acids"
    # A traversal-style value must not escape the textbook directory.
    assert loader.load_chapter_content(Subject.SCIENCE, ClassLevel.CLASS_10, "../../etc/passwd") is None


def test_curriculum_map_missing_returns_none(tmp_path: Path):
    loader = NCERTDataLoader(data_dir=str(tmp_path))
    assert loader.load_curriculum_map(Subject.NEPALI, ClassLevel.CLASS_11) is None


def test_curriculum_map_reads_generated_file(tmp_path: Path):
    write(
        tmp_path / "curriculum/science_class_10.json",
        '{"subject": "science", "class": 10, "catalogue_verified": true, "chapters": []}',
    )
    loader = NCERTDataLoader(data_dir=str(tmp_path))
    data = loader.load_curriculum_map(Subject.SCIENCE, ClassLevel.CLASS_10)
    assert data is not None and data["catalogue_verified"] is True


def test_curriculum_falls_back_to_catalogue_index(tmp_path: Path):
    write(
        tmp_path / "curriculum/catalogue_index.json",
        (
            '{"source": "ncert_textbook_catalogue", "catalogue_verified": true, "books": ['
            '{"class_level": 10, "subject": "Science", "subject_slug": "science", "book_code": "jesc1"}'
            "]}"
        ),
    )
    loader = NCERTDataLoader(data_dir=str(tmp_path))
    data = loader.load_curriculum_map(Subject.SCIENCE, ClassLevel.CLASS_10)
    assert data is not None
    assert data["catalogue_verified"] is True
    assert data["books"][0]["book_code"] == "jesc1"
