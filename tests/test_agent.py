from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine

from app.main import app
from app.models import ResearchReport, ResearchRequest, ResearchStatus
from app.research import ResearchService
from app.storage import ResearchStorage


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("RESEARCH_API_KEY", "test-secret")

    with patch("app.main.ResearchStorage") as storage_class:
        storage = ResearchStorage("sqlite://")

        storage.engine.dispose()
        storage.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        storage.sessions.configure(bind=storage.engine)
        storage.initialize()

        storage_class.return_value = storage

        with TestClient(app) as test_client:
            yield test_client

        storage.close()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_authentication(client):
    response = client.get(f"/research/{uuid4()}")
    assert response.status_code == 401


def test_missing_report(client):
    response = client.get(
        f"/research/{uuid4()}",
        headers={"x-api-key": "test-secret"},
    )
    assert response.status_code == 404


def test_research_validation():
    service = ResearchService()
    request = ResearchRequest(question="What is enterprise AI?")

    with pytest.raises(ValueError, match="At least one"):
        service.run(request, [])


def test_research_and_storage(client):
    report = ResearchReport(
        question="What is enterprise AI?",
        status=ResearchStatus.COMPLETED,
        summary="Enterprise AI supports business operations.",
    )

    payload = {
        "question": report.question,
        "urls": ["https://example.com"],
    }

    with patch.object(
        app.state.service, "run", return_value=report
    ):
        response = client.post(
            "/research",
            json=payload,
            headers={"x-api-key": "test-secret"},
        )

    assert response.status_code == 200
    assert response.json()["summary"] == report.summary

    saved = client.get(
        f"/research/{report.research_id}",
        headers={"x-api-key": "test-secret"},
    )

    assert saved.status_code == 200
    assert saved.json()["research_id"] == str(report.research_id)
