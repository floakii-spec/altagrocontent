import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session
from src.models import Base, Carousel
from api.main import app
from api.deps import get_db
from datetime import datetime, timezone

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
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


def test_list_carousels_empty():
    response = client.get("/carousel")
    assert response.status_code == 200
    assert response.json() == []


def test_list_carousels_returns_history():
    with Session(engine) as s:
        c = Carousel(theme="soja", slides=[{"slide_number": 1, "title": "T", "copy": "C", "cta": ""}],
                     generated_at=datetime.now(timezone.utc))
        s.add(c)
        s.commit()
    response = client.get("/carousel")
    assert len(response.json()) == 1
    assert response.json()[0]["theme"] == "soja"


def test_generate_carousel():
    mock_carousel = MagicMock()
    mock_carousel.id = 1
    mock_carousel.theme = "gestão de safra"
    mock_carousel.slides = [{"slide_number": 1, "title": "Hook", "copy": "Texto", "cta": ""}]
    mock_carousel.generated_at = datetime.now(timezone.utc)
    with patch("api.routers.carousel.generate_carousel", return_value=mock_carousel):
        response = client.post("/carousel/generate", json={"theme": "gestão de safra"})
    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "gestão de safra"
    assert len(data["slides"]) == 1
