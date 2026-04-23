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


def _seed_intelligence(
    session,
    *,
    handle: str = "agro_profile",
    profile_type: str = "competitor",
    instagram_id: str = "intel_post_1",
    analyzed_at: datetime | None = None,
):
    profile = Profile(handle=handle, type=profile_type, follower_count=8000)
    session.add(profile)
    session.flush()
    post = Post(
        profile_id=profile.id,
        instagram_id=instagram_id,
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
        analyzed_at=analyzed_at or datetime.now(timezone.utc),
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
    assert data[0]["profile_type"] == "competitor"
    assert data[0]["agro_topic_cluster"] == "soja"
    assert data[0]["technical_depth"] == "especialista"
    assert data[0]["slides_count"] == 0


def test_list_intelligence_prioritizes_competitors_before_own_profile():
    with Session(engine) as s:
        _seed_intelligence(
            s,
            handle="nathanlimagro",
            profile_type="own",
            instagram_id="own-newer",
            analyzed_at=datetime(2026, 4, 23, 12, tzinfo=timezone.utc),
        )
        _seed_intelligence(
            s,
            handle="concorrente",
            profile_type="competitor",
            instagram_id="competitor-older",
            analyzed_at=datetime(2026, 4, 22, 12, tzinfo=timezone.utc),
        )

    response = client.get("/intelligence/posts")

    assert response.status_code == 200
    data = response.json()
    assert [row["handle"] for row in data] == ["concorrente", "nathanlimagro"]
    assert [row["profile_type"] for row in data] == ["competitor", "own"]


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

    with patch("api.routers.intelligence.intelligence_analysis_workflow", return_value={"processed": 1}):
        response = client.post("/intelligence/analyze")
    assert response.status_code == 200
    assert response.json()["processed"] == 1


def test_trigger_analyze_can_filter_handle_and_force():
    with Session(engine) as s:
        p1 = Profile(handle="leandro.varos", type="competitor", follower_count=3000)
        p2 = Profile(handle="outro.perfil", type="competitor", follower_count=3000)
        s.add_all([p1, p2])
        s.flush()
        s.add_all([
            Post(
                profile_id=p1.id,
                instagram_id="target_post",
                image_url="https://example.com/1.jpg",
                caption="target",
                hashtags=[],
                likes=10,
                comments=1,
                post_type="carousel",
                published_at=datetime.now(timezone.utc),
            ),
            Post(
                profile_id=p2.id,
                instagram_id="other_post",
                image_url="https://example.com/2.jpg",
                caption="other",
                hashtags=[],
                likes=10,
                comments=1,
                post_type="carousel",
                published_at=datetime.now(timezone.utc),
            ),
        ])
        s.commit()

    with patch("api.routers.intelligence.intelligence_analysis_workflow", return_value={"processed": 1}) as mock_workflow:
        response = client.post("/intelligence/analyze?handle=leandro.varos&force=true")
    assert response.status_code == 200
    assert response.json()["processed"] == 1
    assert mock_workflow.call_args.kwargs["handle"] == "leandro.varos"
    assert mock_workflow.call_args.kwargs["force"] is True


def test_start_analysis_job_returns_live_job():
    job = {
        "job_id": "job-123",
        "status": "queued",
        "phase": "queued",
        "handle": "leandro.varos",
        "force": True,
        "sync_before": True,
        "limit": 200,
        "message": "Fila criada",
        "phase_total": 0,
        "phase_completed": 0,
        "total_profiles": 0,
        "completed_profiles": 0,
        "total_posts": 0,
        "completed_posts": 0,
        "successful_posts": 0,
        "failed_posts": 0,
        "current_handle": None,
        "current_post_id": None,
        "errors": [],
        "started_at": None,
        "updated_at": datetime.now(timezone.utc),
        "finished_at": None,
    }

    with patch("api.routers.intelligence.create_analysis_job", return_value=job) as mock_create:
        response = client.post("/intelligence/jobs", json={
            "handle": "leandro.varos",
            "force": True,
            "sync_before": True,
            "limit": 200,
        })

    assert response.status_code == 202
    assert response.json()["job_id"] == "job-123"
    assert mock_create.call_args.kwargs["handle"] == "leandro.varos"


def test_get_analysis_job_status_returns_job():
    job = {
        "job_id": "job-123",
        "status": "running",
        "phase": "intelligence",
        "handle": "leandro.varos",
        "force": True,
        "sync_before": True,
        "limit": 200,
        "message": "Analisando",
        "phase_total": 55,
        "phase_completed": 10,
        "total_profiles": 1,
        "completed_profiles": 1,
        "total_posts": 55,
        "completed_posts": 10,
        "successful_posts": 9,
        "failed_posts": 1,
        "current_handle": "leandro.varos",
        "current_post_id": 101,
        "errors": ["post 99: timeout"],
        "started_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "finished_at": None,
    }

    with patch("api.routers.intelligence.get_analysis_job", return_value=job):
        response = client.get("/intelligence/jobs/job-123")

    assert response.status_code == 200
    assert response.json()["phase"] == "intelligence"
    assert response.json()["completed_posts"] == 10


def test_get_analysis_job_status_404():
    with patch("api.routers.intelligence.get_analysis_job", return_value=None):
        response = client.get("/intelligence/jobs/missing")
    assert response.status_code == 404
