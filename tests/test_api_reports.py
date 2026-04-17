import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session
from src.models import Base, WeeklyReport
from api.main import app
from api.deps import get_db
from datetime import datetime, timezone, timedelta

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)

def override_db():
    with Session(engine) as s:
        yield s

app.dependency_overrides[get_db] = override_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield

def test_list_reports_empty():
    response = client.get("/reports")
    assert response.status_code == 200
    assert response.json() == []

def test_list_reports_returns_data():
    now = datetime.now(timezone.utc)
    with Session(engine) as s:
        r = WeeklyReport(
            period_start=now - timedelta(days=7),
            period_end=now,
            top_formats={"carrossel": 5},
            top_themes={"soja": 10},
            top_hashtags=["soja"],
            language_patterns={},
            report_text="Relatório de teste.",
            generated_at=now,
        )
        s.add(r)
        s.commit()
    response = client.get("/reports")
    assert len(response.json()) == 1
    assert response.json()[0]["report_text"] == "Relatório de teste."

def test_generate_report():
    now = datetime.now(timezone.utc)
    mock_report = MagicMock()
    mock_report.id = 1
    mock_report.period_start = now - timedelta(days=7)
    mock_report.period_end = now
    mock_report.top_formats = {}
    mock_report.top_themes = {}
    mock_report.top_hashtags = []
    mock_report.language_patterns = {}
    mock_report.report_text = "GPT report"
    mock_report.generated_at = now
    with patch("api.routers.reports.generate_weekly_report", return_value=mock_report):
        response = client.post("/reports/generate")
    assert response.status_code == 200
    assert response.json()["report_text"] == "GPT report"
