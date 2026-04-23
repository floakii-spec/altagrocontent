import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session
from src.models import Base, Profile, Post, ProfileVoice
from api.main import app
from api.deps import get_db
from datetime import datetime, timezone

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
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

def test_get_voice_no_profile():
    response = client.get("/voice")
    assert response.status_code == 404

def test_get_voice_returns_latest():
    with Session(engine) as s:
        p = Profile(handle="myprofile", type="own")
        s.add(p)
        s.flush()
        v = ProfileVoice(
            profile_id=p.id,
            vocabulary={"palavras_frequentes": ["safra"]},
            tone="direto",
            dominant_themes=["soja"],
            competitor_comparison={},
            voice_summary="Tom direto.",
            generated_at=datetime.now(timezone.utc),
        )
        s.add(v)
        s.commit()
    response = client.get("/voice")
    assert response.status_code == 200
    assert response.json()["tone"] == "direto"

def test_analyze_voice():
    with Session(engine) as s:
        p = Profile(handle="myprofile", type="own")
        s.add(p)
        s.flush()
        s.add(Post(
            profile_id=p.id,
            instagram_id="OWN-VOICE",
            image_url="https://example.com/voice.jpg",
            caption="Post do perfil proprio",
            hashtags=[],
            likes=0,
            comments=0,
            post_type="feed",
            published_at=datetime.now(timezone.utc),
        ))
        s.commit()
    mock_voice = MagicMock()
    mock_voice.id = 1
    mock_voice.tone = "confiante"
    mock_voice.dominant_themes = ["tecnologia"]
    mock_voice.vocabulary = {}
    mock_voice.competitor_comparison = {}
    mock_voice.voice_summary = "Confiante."
    mock_voice.generated_at = datetime.now(timezone.utc)
    with patch("api.routers.voice.generate_voice_profile", return_value=mock_voice):
        response = client.post("/voice/analyze")
    assert response.status_code == 200
    assert response.json()["tone"] == "confiante"
