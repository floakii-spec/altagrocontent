import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone
from src.models import Base, Profile, Post, PostAnalysis, PostIntelligence
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


def test_list_competitors_empty():
    response = client.get("/competitors")
    assert response.status_code == 200
    assert response.json() == []


def test_add_competitor():
    response = client.post("/competitors", json={"handle": "agro123", "type": "competitor"})
    assert response.status_code == 200
    data = response.json()
    assert data["handle"] == "agro123"
    assert data["type"] == "competitor"
    assert "id" in data


def test_add_own_profile():
    response = client.post("/competitors", json={"handle": "myprofile", "type": "own"})
    assert response.status_code == 200
    assert response.json()["type"] == "own"


def test_delete_competitor():
    add = client.post("/competitors", json={"handle": "todelete", "type": "competitor"})
    profile_id = add.json()["id"]
    response = client.delete(f"/competitors/{profile_id}")
    assert response.status_code == 200
    listed = client.get("/competitors")
    assert all(p["id"] != profile_id for p in listed.json())


def test_list_competitors_returns_post_count():
    with Session(engine) as s:
        p = Profile(handle="withposts", type="competitor")
        s.add(p)
        s.flush()
        post = Post(
            profile_id=p.id,
            instagram_id="ig1",
            image_url="http://x.com/img.jpg",
            post_type="feed",
            published_at=datetime.now(timezone.utc),
        )
        s.add(post)
        s.commit()
    response = client.get("/competitors")
    profile = next(p for p in response.json() if p["handle"] == "withposts")
    assert profile["post_count"] == 1


def test_list_competitor_library_returns_posts_with_status_and_title():
    with Session(engine) as s:
        competitor = Profile(handle="agro.alpha", type="competitor", follower_count=12345)
        own = Profile(handle="meu.perfil", type="own", follower_count=999)
        s.add_all([competitor, own])
        s.flush()

        older_post = Post(
            profile_id=competitor.id,
            instagram_id="ig-old",
            image_url="http://x.com/old.jpg",
            caption="Legenda mais antiga do concorrente",
            post_type="feed",
            published_at=datetime(2026, 4, 18, tzinfo=timezone.utc),
            collected_at=datetime(2026, 4, 19, tzinfo=timezone.utc),
        )
        newer_post = Post(
            profile_id=competitor.id,
            instagram_id="ig-new",
            image_url="http://x.com/new.jpg",
            caption="Legenda mais recente do concorrente",
            post_type="carousel",
            published_at=datetime(2026, 4, 20, tzinfo=timezone.utc),
            collected_at=datetime(2026, 4, 21, tzinfo=timezone.utc),
        )
        own_post = Post(
            profile_id=own.id,
            instagram_id="ig-own",
            image_url="http://x.com/own.jpg",
            caption="Post do proprio perfil",
            post_type="feed",
            published_at=datetime(2026, 4, 22, tzinfo=timezone.utc),
        )
        s.add_all([older_post, newer_post, own_post])
        s.flush()

        s.add(
            PostAnalysis(
                post_id=newer_post.id,
                raw_analysis={"hook": "Hook do post mais recente"},
                analyzed_at=datetime.now(timezone.utc),
            )
        )
        s.add(
            PostIntelligence(
                post_id=newer_post.id,
                core_argument="Argumento central",
                technical_claims=[],
                data_points=[],
                sources_referenced=[],
                analyzed_at=datetime.now(timezone.utc),
            )
        )
        s.commit()

    response = client.get("/competitors/library")

    assert response.status_code == 200
    library = response.json()
    assert len(library) == 1
    competitor = library[0]
    assert competitor["handle"] == "agro.alpha"
    assert competitor["post_count"] == 2
    assert competitor["analyzed_posts"] == 1
    assert competitor["pending_posts"] == 1
    assert [post["instagram_id"] for post in competitor["posts"]] == ["ig-new", "ig-old"]
    assert competitor["posts"][0]["title"] == "Hook do post mais recente"
    assert competitor["posts"][0]["status"] == "analisado"
    assert competitor["posts"][1]["title"] == "Legenda mais antiga do concorrente"
    assert competitor["posts"][1]["status"] == "nao_analisado"


def test_sync_competitors_can_filter_by_handle():
    with Session(engine) as s:
        s.add_all([
            Profile(handle="leandro.varos", type="competitor"),
            Profile(handle="outro.perfil", type="competitor"),
        ])
        s.commit()

    with patch("src.collector.collector.fetch_posts_apify", return_value=[]) as mock_fetch:
        response = client.post("/competitors/sync?handle=leandro.varos")

    assert response.status_code == 200
    assert response.json()["synced"] == 1
    assert mock_fetch.call_args.kwargs["handle"] == "leandro.varos"
