import json
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, Profile, Post, ProfileVoice
from src.reporter.voice_profiler import generate_voice_profile


@pytest.fixture
def session_with_own_profile():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        profile = Profile(handle="meu_perfil", type="own", niche="agro", follower_count=3000)
        s.add(profile)
        s.flush()
        for i in range(3):
            post = Post(
                profile_id=profile.id,
                instagram_id=f"OWN{i}",
                image_url=f"https://example.com/{i}.jpg",
                caption=f"Nossa fazenda produz {i+1} toneladas por hectare",
                hashtags=["agro", "produtividade"],
                likes=300,
                comments=15,
                post_type="feed",
                published_at=datetime(2026, 4, 10, tzinfo=timezone.utc),
            )
            s.add(post)
        s.commit()
        yield s, profile


MOCK_VOICE = {
    "vocabulary": {"palavras_frequentes": ["fazenda", "toneladas", "produtividade"]},
    "tone": "técnico e acessível",
    "dominant_themes": ["produção", "resultados"],
    "competitor_comparison": {"diferencial": "foco em números concretos"},
}


def test_generate_voice_profile_creates_profile(session_with_own_profile):
    session, profile = session_with_own_profile
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(MOCK_VOICE)
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("src.reporter.voice_profiler.openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        voice = generate_voice_profile(profile=profile, session=session)

    assert voice.tone == "técnico e acessível"
    assert "produção" in voice.dominant_themes
    saved = session.query(ProfileVoice).filter_by(profile_id=profile.id).first()
    assert saved is not None
