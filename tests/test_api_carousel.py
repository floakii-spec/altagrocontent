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

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    app.dependency_overrides[get_db] = override_db
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    app.dependency_overrides.pop(get_db, None)


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


from src.models import CarouselSuggestion


def test_get_suggestions_empty():
    response = client.get("/carousel/suggestions")
    assert response.status_code == 204


def test_get_suggestions_returns_latest():
    with Session(engine) as s:
        s.add(CarouselSuggestion(
            themes=[{"title": "Soja alta", "rationale": "gap"}],
            generated_at=datetime.now(timezone.utc),
        ))
        s.add(CarouselSuggestion(
            themes=[{"title": "Milho baixo", "rationale": "viral"}],
            generated_at=datetime.now(timezone.utc),
        ))
        s.commit()
    response = client.get("/carousel/suggestions")
    assert response.status_code == 200
    data = response.json()
    assert data["themes"][0]["title"] == "Milho baixo"


def test_refresh_suggestions():
    from unittest.mock import patch, MagicMock
    mock_suggestion = MagicMock()
    mock_suggestion.id = 1
    mock_suggestion.themes = [{"title": "T", "rationale": "R"}]
    mock_suggestion.generated_at = datetime.now(timezone.utc)
    with patch("api.routers.carousel.generate_theme_suggestions", return_value=mock_suggestion):
        response = client.post("/carousel/suggestions/refresh")
    assert response.status_code == 200
    assert response.json()["themes"][0]["title"] == "T"
