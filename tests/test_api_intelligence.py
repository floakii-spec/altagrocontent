import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from src.models import Base, Post, Profile, PostAnalysis, PostIntelligence, ArgumentBank
from api.main import app
from api.deps import get_db

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


def _seed_intelligence(session):
    profile = Profile(handle="agro_profile", type="competitor", follower_count=8000)
    session.add(profile)
    session.flush()
    post = Post(
        profile_id=profile.id,
        instagram_id="intel_post_1",
        image_url="https://example.com/img.jpg",
        caption="Soja transgênica",
        hashtags=[],
        likes=400,
        comments=25,
        post_type="feed",
        published_at=datetime.now(timezone.utc),
    )
    session.add(post)
    session.flush()
    intel = PostIntelligence(
        post_id=post.id,
        agro_topic_cluster="soja",
        agro_segment="grãos",
        technical_depth="especialista",
        core_argument="Soja RR é mais rentável.",
        argument_structure="dado → causa → solução",
        technical_claims=["20% mais produtivo"],
        data_points=[],
        sources_referenced=["Embrapa"],
        knowledge_assumptions="Conhece soja convencional",
        content_gaps="Sem menção ao custo de licença",
        replication_template="[DADO] + [CAUSA] + [CTA]",
        analyzed_at=datetime.now(timezone.utc),
    )
    session.add(intel)
    session.commit()
    return post, intel


def test_list_intelligence_empty():
    response = client.get("/intelligence/posts")
    assert response.status_code == 200
    assert response.json() == []


def test_list_intelligence_returns_data():
    with Session(engine) as s:
        _seed_intelligence(s)
    response = client.get("/intelligence/posts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["agro_topic_cluster"] == "soja"
    assert data[0]["technical_depth"] == "especialista"


def test_get_intelligence_by_post_id():
    with Session(engine) as s:
        post, _ = _seed_intelligence(s)
        post_id = post.id
    response = client.get(f"/intelligence/posts/{post_id}")
    assert response.status_code == 200
    assert response.json()["core_argument"] == "Soja RR é mais rentável."


def test_get_intelligence_not_found():
    response = client.get("/intelligence/posts/9999")
    assert response.status_code == 404


def test_list_arguments_empty():
    response = client.get("/intelligence/arguments")
    assert response.status_code == 200
    assert response.json() == []


def test_list_arguments_with_filter():
    with Session(engine) as s:
        s.add(ArgumentBank(
            text="soja rr aumenta produtividade 20%",
            topic_cluster="soja",
            agro_segment="grãos",
            quality_score=0.7,
            virality_weight=0.6,
            source_post_ids=[1],
            times_seen=1,
            origin="extracted",
            created_at=datetime.now(timezone.utc),
        ))
        s.add(ArgumentBank(
            text="milho híbrido reduz custo por saca",
            topic_cluster="milho",
            agro_segment="grãos",
            quality_score=0.4,
            virality_weight=0.3,
            source_post_ids=[2],
            times_seen=1,
            origin="extracted",
            created_at=datetime.now(timezone.utc),
        ))
        s.commit()
    response = client.get("/intelligence/arguments?topic_cluster=soja")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["topic_cluster"] == "soja"


def test_trigger_analyze_returns_count():
    with Session(engine) as s:
        profile = Profile(handle="new_profile", type="competitor", follower_count=3000)
        s.add(profile)
        s.flush()
        post = Post(
            profile_id=profile.id,
            instagram_id="unanalyzed_post",
            image_url="https://example.com/img.jpg",
            caption="Pecuária em alta no cerrado brasileiro",
            hashtags=[],
            likes=100,
            comments=5,
            post_type="feed",
            published_at=datetime.now(timezone.utc),
        )
        s.add(post)
        s.commit()

    mock_intel = MagicMock()
    with patch("api.routers.intelligence.analyze_post_intelligence", return_value=mock_intel):
        response = client.post("/intelligence/analyze")
    assert response.status_code == 200
    assert response.json()["processed"] == 1
