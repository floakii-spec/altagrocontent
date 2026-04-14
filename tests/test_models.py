import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, Profile, Post, PostAnalysis, ProfileVoice, WeeklyReport, Carousel


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def test_create_profile(session):
    p = Profile(handle="agro_example", type="competitor", niche="agronegócio", follower_count=5000)
    session.add(p)
    session.commit()
    assert p.id is not None
    assert p.active is True


def test_create_post(session):
    p = Profile(handle="agro_example", type="competitor", niche="agronegócio", follower_count=5000)
    session.add(p)
    session.flush()
    post = Post(
        profile_id=p.id,
        instagram_id="IG123",
        image_url="https://example.com/img.jpg",
        caption="Safra recorde!",
        hashtags=["agro", "safra"],
        likes=200,
        comments=15,
        post_type="feed",
        published_at=datetime.now(timezone.utc),
    )
    session.add(post)
    session.commit()
    assert post.id is not None


def test_create_post_analysis(session):
    p = Profile(handle="h", type="competitor", niche="agro", follower_count=1000)
    session.add(p)
    session.flush()
    post = Post(profile_id=p.id, instagram_id="IG1", image_url="u", caption="c",
                hashtags=[], likes=100, comments=5, post_type="feed",
                published_at=datetime.now(timezone.utc))
    session.add(post)
    session.flush()
    analysis = PostAnalysis(
        post_id=post.id,
        visual_theme="maquinário",
        visual_format="foto real",
        emotional_tone="inspirador",
        trigger="resultado",
        virality_score=0.42,
        raw_analysis={"summary": "ok"},
    )
    session.add(analysis)
    session.commit()
    assert analysis.id is not None


def test_create_weekly_report(session):
    report = WeeklyReport(
        period_start=datetime(2026, 4, 7, tzinfo=timezone.utc),
        period_end=datetime(2026, 4, 13, tzinfo=timezone.utc),
        top_formats={"infográfico": 12},
        top_themes={"maquinário": 8},
        language_patterns={"tom": "direto"},
        top_hashtags=["agro", "colheita"],
        viral_posts=[1, 2, 3],
        report_text="# Relatório\n...",
    )
    session.add(report)
    session.commit()
    assert report.id is not None


def test_create_carousel(session):
    c = Carousel(
        theme="Dicas de plantio de soja",
        slides=[{"slide_number": 1, "title": "Título", "copy": "Texto", "cta": "Salve!"}],
        based_on_reports=[1],
    )
    session.add(c)
    session.commit()
    assert c.id is not None
