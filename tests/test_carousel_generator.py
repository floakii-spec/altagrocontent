import json
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, Profile, WeeklyReport, ProfileVoice, Carousel
from src.carousel.generator import generate_carousel


@pytest.fixture
def session_with_context():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        profile = Profile(handle="meu_perfil", type="own", niche="agro", follower_count=3000)
        s.add(profile)
        s.flush()

        voice = ProfileVoice(
            profile_id=profile.id,
            vocabulary={"palavras_frequentes": ["fazenda", "produtividade"]},
            tone="técnico e acessível",
            dominant_themes=["produção"],
            competitor_comparison={},
        )
        report = WeeklyReport(
            period_start=datetime(2026, 4, 7, tzinfo=timezone.utc),
            period_end=datetime(2026, 4, 13, tzinfo=timezone.utc),
            top_formats={"foto real": 5},
            top_themes={"campo": 4},
            language_patterns={"tom": "inspirador"},
            top_hashtags=["agro"],
            viral_posts=[],
            report_text="# Relatório\nFoto real com tema campo converte mais.",
        )
        s.add(voice)
        s.add(report)
        s.commit()
        yield s, profile, voice, report


MOCK_SLIDES = [
    {"slide_number": 1, "title": "Você sabia?", "copy": "A soja brasileira...", "cta": ""},
    {"slide_number": 2, "title": "O problema", "copy": "Muitos produtores...", "cta": ""},
    {"slide_number": 3, "title": "A solução", "copy": "Com manejo correto...", "cta": ""},
    {"slide_number": 4, "title": "Resultado", "copy": "Até 30% mais produtividade", "cta": "Salve este post!"},
]


def test_generate_carousel_returns_slides(session_with_context):
    session, profile, voice, report = session_with_context
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(MOCK_SLIDES)
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("src.carousel.generator.openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        carousel = generate_carousel(
            theme="Manejo de soja para alta produtividade",
            session=session,
        )

    assert len(carousel.slides) == 4
    assert carousel.slides[0]["title"] == "Você sabia?"
    assert carousel.slides[-1]["cta"] == "Salve este post!"
    saved = session.query(Carousel).first()
    assert saved is not None
