import pytest
from datetime import datetime, timezone
from src.models import Profile, Post, PostAnalysis
from src.analyzer.gap_analyzer import compute_gaps, _extract_topics


def _make_profile(session, handle, ptype):
    p = Profile(handle=handle, type=ptype, niche="agro", follower_count=1000)
    session.add(p)
    session.flush()
    return p


def _make_post_with_analysis(session, profile, insta_id, themes):
    post = Post(
        profile_id=profile.id,
        instagram_id=insta_id,
        image_url="https://example.com/img.jpg",
        caption="Caption",
        hashtags=[],
        likes=100,
        comments=5,
        post_type="feed",
        published_at=datetime.now(timezone.utc),
    )
    session.add(post)
    session.flush()
    analysis = PostAnalysis(
        post_id=post.id,
        virality_score=0.5,
        raw_analysis={"dominant_themes": themes},
    )
    session.add(analysis)
    session.flush()
    return post


def test_extract_topics_from_raw_analysis():
    raw = {"dominant_themes": ["rentabilidade", "manejo de pragas"]}
    topics = _extract_topics(raw)
    assert "rentabilidade" in topics
    assert "manejo de pragas" in topics


def test_extract_topics_empty():
    topics = _extract_topics({})
    assert topics == []


def test_compute_gaps_returns_list(session):
    competitor = _make_profile(session, "concorrente1", "competitor")
    own = _make_profile(session, "nathanlimagro", "own")

    _make_post_with_analysis(session, competitor, "C1", ["rentabilidade", "venda"])
    _make_post_with_analysis(session, competitor, "C2", ["rentabilidade", "insumos"])
    _make_post_with_analysis(session, own, "N1", ["insumos"])

    session.commit()

    gaps = compute_gaps(session)
    assert isinstance(gaps, list)
    assert len(gaps) > 0


def test_compute_gaps_identifies_uncovered_topic(session):
    competitor = _make_profile(session, "comp2", "competitor")
    own = _make_profile(session, "own2", "own")

    _make_post_with_analysis(session, competitor, "C3", ["rentabilidade"])
    _make_post_with_analysis(session, competitor, "C4", ["rentabilidade"])
    _make_post_with_analysis(session, own, "N2", ["insumos"])

    session.commit()

    gaps = compute_gaps(session)
    topics = [g["topic"] for g in gaps]
    assert "rentabilidade" in topics


def test_compute_gaps_no_competitors_returns_empty(session):
    own = _make_profile(session, "own3", "own")
    _make_post_with_analysis(session, own, "N3", ["venda"])
    session.commit()

    gaps = compute_gaps(session)
    assert gaps == []
