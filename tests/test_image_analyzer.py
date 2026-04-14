import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, Profile, Post, PostAnalysis
from src.analyzer.image_analyzer import analyze_post


@pytest.fixture
def session_with_post():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        profile = Profile(handle="agro_h", type="competitor", niche="agro", follower_count=10000)
        s.add(profile)
        s.flush()
        post = Post(
            profile_id=profile.id,
            instagram_id="IG999",
            image_url="https://example.com/img.jpg",
            caption="Colheita da soja bateu recorde!",
            hashtags=["soja", "agro"],
            likes=800,
            comments=40,
            post_type="feed",
            published_at=datetime(2026, 4, 10, tzinfo=timezone.utc),
        )
        s.add(post)
        s.commit()
        yield s, profile, post


MOCK_GPT_RESPONSE = {
    "visual_theme": "campo",
    "visual_format": "foto real",
    "emotional_tone": "inspirador",
    "trigger": "resultado",
    "summary": "Imagem de colheita de soja com linguagem de conquista.",
}


def test_analyze_post_creates_analysis(session_with_post):
    session, profile, post = session_with_post

    mock_choice = MagicMock()
    mock_choice.message.content = str(MOCK_GPT_RESPONSE).replace("'", '"')

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    import json
    mock_choice.message.content = json.dumps(MOCK_GPT_RESPONSE)

    with patch("src.analyzer.image_analyzer.openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        analysis = analyze_post(post=post, session=session)

    assert analysis.visual_theme == "campo"
    assert analysis.visual_format == "foto real"
    assert analysis.emotional_tone == "inspirador"
    assert analysis.trigger == "resultado"
    assert analysis.virality_score == pytest.approx(0.088, abs=0.001)
    saved = session.query(PostAnalysis).filter_by(post_id=post.id).first()
    assert saved is not None


def test_analyze_post_skips_already_analyzed(session_with_post):
    session, profile, post = session_with_post

    existing = PostAnalysis(
        post_id=post.id,
        visual_theme="maquinário",
        visual_format="foto real",
        emotional_tone="técnico",
        trigger="autoridade",
        virality_score=0.05,
        raw_analysis={},
    )
    session.add(existing)
    session.commit()

    with patch("src.analyzer.image_analyzer.openai_client") as mock_client:
        result = analyze_post(post=post, session=session)
        mock_client.chat.completions.create.assert_not_called()

    assert result.id == existing.id
