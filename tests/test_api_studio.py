import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session
from src.models import Base, Profile, Post, PostAnalysis, PostIntelligence, ProfileVoice, GeneratedPost
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

def test_list_studio_posts_empty():
    response = client.get("/studio/posts")
    assert response.status_code == 200
    assert response.json() == []

def test_list_studio_posts_returns_competitor_posts():
    with Session(engine) as s:
        p = Profile(handle="competidor1", type="competitor")
        s.add(p)
        s.flush()
        now = datetime.now(timezone.utc)
        post = Post(profile_id=p.id, instagram_id="ig1", image_url="http://x.com/img.jpg",
                    post_type="feed", published_at=now, caption="Post do concorrente")
        s.add(post)
        s.flush()
        analysis = PostAnalysis(post_id=post.id, virality_score=0.85,
                                raw_analysis={"hook": "Hook incrível"}, analyzed_at=now)
        s.add(analysis)
        s.commit()
    response = client.get("/studio/posts")
    assert len(response.json()) == 1
    assert response.json()[0]["handle"] == "competidor1"
    assert response.json()[0]["virality_score"] == pytest.approx(0.85)

def test_generate_studio_post():
    with Session(engine) as s:
        p = Profile(handle="comp", type="competitor")
        s.add(p)
        s.flush()
        now = datetime.now(timezone.utc)
        post = Post(profile_id=p.id, instagram_id="ig2", image_url="http://x.com/img2.jpg",
                    post_type="feed", published_at=now)
        s.add(post)
        s.flush()
        intel = PostIntelligence(
            post_id=post.id,
            technical_claims=[],
            data_points=[],
            sources_referenced=[],
            core_argument="Argumento central",
            analyzed_at=now,
        )
        s.add(intel)
        own = Profile(handle="own_profile", type="own")
        s.add(own)
        s.flush()
        voice = ProfileVoice(
            profile_id=own.id,
            vocabulary={},
            tone="direto",
            dominant_themes=[],
            competitor_comparison={},
            voice_summary="Tom direto.",
            generated_at=now,
        )
        s.add(voice)
        s.flush()
        post_id = post.id
        s.commit()

    mock_generated = MagicMock()
    mock_generated.id = 1
    mock_generated.caption = "Post gerado pelo GPT"
    mock_generated.hook = "Hook gerado"
    mock_generated.cta = "Siga agora"
    mock_generated.created_at = datetime.now(timezone.utc)

    with patch("api.routers.studio.generate_post", return_value=mock_generated):
        response = client.post("/studio/generate", json={"post_id": post_id})
    assert response.status_code == 200
    assert response.json()["caption"] == "Post gerado pelo GPT"
