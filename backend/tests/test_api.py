"""Smoke tests for API routes that do not require an LLM provider."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_reports_unconfigured_services():
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "llm" in response.json()["services"]


def test_curriculum_rejects_unknown_subject():
    with TestClient(app) as client:
        response = client.get("/api/v1/curriculum/not-a-subject/10")
    assert response.status_code == 404


def test_curriculum_returns_catalogue_verified_book():
    with TestClient(app) as client:
        response = client.get("/api/v1/curriculum/science/10")
    assert response.status_code == 200
    body = response.json()
    assert body["subject"] == "science"
    assert body["class"] == 10
    assert body["catalogue_verified"] is True
    assert body["chapter_details_verified"] is False
    # Book code and range come from the official NCERT catalogue.
    assert body["primary_book"]["book_code"] == "jesc1"
    assert body["primary_book"]["last_chapter"] == 13


def test_curriculum_404_for_uncovered_combination():
    # Valid enum values, but no catalogue book for this pairing.
    with TestClient(app) as client:
        response = client.get("/api/v1/curriculum/nepali/11")
    assert response.status_code == 404
