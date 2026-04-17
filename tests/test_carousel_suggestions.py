import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session
from src.models import Base, CarouselSuggestion, NewsItem, Post, PostAnalysis, Profile


engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(engine)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


def _mock_openai(titles):
    themes = [{"title": t, "rationale": "test"} for t in titles]
    msg = MagicMock()
    msg.content = json.dumps(themes)
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_generate_stores_six_suggestions():
    from src.carousel.theme_suggester import generate_theme_suggestions
    titles = [f"Tema {i}" for i in range(6)]
    with patch("src.carousel.theme_suggester.openai_client.chat.completions.create",
               return_value=_mock_openai(titles)):
        with Session(engine) as s:
            result = generate_theme_suggestions(s)
    assert len(result.themes) == 6
    assert result.themes[0]["title"] == "Tema 0"


def test_generate_persists_to_db():
    from src.carousel.theme_suggester import generate_theme_suggestions
    titles = [f"Tema {i}" for i in range(6)]
    with patch("src.carousel.theme_suggester.openai_client.chat.completions.create",
               return_value=_mock_openai(titles)):
        with Session(engine) as s:
            generate_theme_suggestions(s)
    with Session(engine) as s:
        row = s.query(CarouselSuggestion).order_by(CarouselSuggestion.generated_at.desc()).first()
    assert row is not None
    assert len(row.themes) == 6


def test_generate_fallback_when_db_empty():
    from src.carousel.theme_suggester import generate_theme_suggestions
    titles = [f"Fallback {i}" for i in range(6)]
    with patch("src.carousel.theme_suggester.openai_client.chat.completions.create",
               return_value=_mock_openai(titles)) as mock_create:
        with Session(engine) as s:
            result = generate_theme_suggestions(s)
    assert mock_create.called
    assert len(result.themes) == 6


def test_generate_includes_news_in_prompt():
    from src.carousel.theme_suggester import generate_theme_suggestions
    with Session(engine) as s:
        item = NewsItem(
            source="canal_rural",
            title="Soja em alta no Mato Grosso",
            url="https://example.com/soja",
            published_at=datetime.now(timezone.utc) - timedelta(hours=10),
        )
        s.add(item)
        s.commit()

    titles = [f"Tema {i}" for i in range(6)]
    with patch("src.carousel.theme_suggester.openai_client.chat.completions.create",
               return_value=_mock_openai(titles)) as mock_create:
        with Session(engine) as s:
            generate_theme_suggestions(s)

    call_kwargs = mock_create.call_args
    user_content = call_kwargs[1]["messages"][1]["content"]
    assert "Soja em alta" in user_content
