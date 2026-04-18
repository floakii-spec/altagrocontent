import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session
from src.models import Base, Post, Profile, PostAnalysis, PostIntelligence, ArgumentBank

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


def _make_post_with_analysis(session, virality=0.6):
    profile = Profile(handle="agro_user", type="competitor", follower_count=5000)
    session.add(profile)
    session.flush()
    post = Post(
        profile_id=profile.id,
        instagram_id="post_abc",
        image_url="https://example.com/img.jpg",
        caption="Test caption",
        hashtags=[],
        likes=300,
        comments=20,
        post_type="feed",
        published_at=datetime.now(timezone.utc),
    )
    session.add(post)
    session.flush()
    analysis = PostAnalysis(
        post_id=post.id,
        virality_score=virality,
        raw_analysis={},
    )
    session.add(analysis)
    session.commit()
    return post


def _make_intelligence(session, post, claims, sources=None):
    intel = PostIntelligence(
        post_id=post.id,
        agro_topic_cluster="soja",
        agro_segment="grãos",
        technical_depth="especialista",
        technical_claims=claims,
        data_points=[],
        sources_referenced=sources or [],
        analyzed_at=datetime.now(timezone.utc),
    )
    session.add(intel)
    session.commit()
    return intel


def test_upsert_inserts_new_arguments():
    from src.analyzer.argument_extractor import upsert_arguments
    with Session(engine) as s:
        post = _make_post_with_analysis(s)
        intel = _make_intelligence(s, post, ["Soja aumenta produtividade em 20%"])
        upsert_arguments(intel, post, s)
        args = s.query(ArgumentBank).all()
    assert len(args) == 1
    assert "soja aumenta produtividade em 20%" in args[0].text


def test_upsert_deduplicates_same_argument():
    from src.analyzer.argument_extractor import upsert_arguments
    with Session(engine) as s:
        post = _make_post_with_analysis(s)
        intel = _make_intelligence(s, post, ["Soja aumenta produtividade em 20%"])
        upsert_arguments(intel, post, s)
        upsert_arguments(intel, post, s)
        args = s.query(ArgumentBank).all()
    assert len(args) == 1
    assert args[0].times_seen == 2


def test_quality_score_with_number_and_source():
    from src.analyzer.argument_extractor import upsert_arguments
    with Session(engine) as s:
        post = _make_post_with_analysis(s)
        intel = _make_intelligence(
            s, post,
            ["Produtividade aumenta 20% com rotação de cultura conforme dados técnicos compilados"],
            sources=["Embrapa"],
        )
        upsert_arguments(intel, post, s)
        arg = s.query(ArgumentBank).first()
    assert arg.quality_score == 1.0


def test_quality_score_no_number_no_source():
    from src.analyzer.argument_extractor import upsert_arguments
    with Session(engine) as s:
        post = _make_post_with_analysis(s)
        intel = _make_intelligence(s, post, ["curto"])
        upsert_arguments(intel, post, s)
        arg = s.query(ArgumentBank).first()
    assert arg.quality_score == 0.0


def test_virality_weight_set_from_post_analysis():
    from src.analyzer.argument_extractor import upsert_arguments
    with Session(engine) as s:
        post = _make_post_with_analysis(s, virality=0.75)
        intel = _make_intelligence(s, post, ["Soja RR aumenta margem em 15 pontos percentuais"])
        upsert_arguments(intel, post, s)
        arg = s.query(ArgumentBank).first()
    assert arg.virality_weight == 0.75
