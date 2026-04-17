import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session
from src.models import Base, NewsItem
from api.main import app
from api.deps import get_db
from datetime import datetime, timezone

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

def test_list_news_empty():
    response = client.get("/news")
    assert response.status_code == 200
    assert response.json() == []

def test_list_news_returns_items():
    with Session(engine) as s:
        item = NewsItem(
            source="canal_rural",
            title="Soja bate recorde",
            url="http://example.com/1",
            published_at=datetime.now(timezone.utc),
            tags=["soja"],
        )
        s.add(item)
        s.commit()
    response = client.get("/news")
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Soja bate recorde"

def test_refresh_news():
    with patch("api.routers.news.fetch_all_feeds", return_value=3):
        response = client.post("/news/refresh")
    assert response.status_code == 200
    assert response.json()["new_items"] == 3
