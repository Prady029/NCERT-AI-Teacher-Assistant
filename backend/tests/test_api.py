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


def test_curriculum_returns_seed_metadata():
    with TestClient(app) as client:
        response = client.get("/api/v1/curriculum/science/10")
    assert response.status_code == 200
    assert response.json()["subject"] == "science"
    assert response.json()["class"] == 10
    assert response.json()["chapters"]
