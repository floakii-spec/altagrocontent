import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from src.models import Base, Profile, Post
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

app.dependency_overrides[get_db] = override_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


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
        from datetime import datetime, timezone
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
