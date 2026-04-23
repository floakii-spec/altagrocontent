import json
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, Profile, Post, PostAnalysis, PostIntelligence, WeeklyReport
from src.reporter.weekly_report import generate_weekly_report


@pytest.fixture
def session_with_analyses():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        profile = Profile(handle="concorrente1", type="competitor", niche="agro", follower_count=8000)
        s.add(profile)
        s.flush()
        for i in range(3):
            post = Post(
                profile_id=profile.id,
                instagram_id=f"IG{i}",
                image_url=f"https://example.com/{i}.jpg",
                caption=f"Post {i}",
                hashtags=["agro"],
                likes=500 + i * 100,
                comments=20 + i,
                post_type="feed",
                published_at=datetime(2026, 4, 10 + i, tzinfo=timezone.utc),
            )
            s.add(post)
            s.flush()
            analysis = PostAnalysis(
                post_id=post.id,
                visual_theme="campo",
                visual_format="foto real",
                emotional_tone="inspirador",
                trigger="resultado",
                virality_score=0.07 + i * 0.01,
                raw_analysis={"summary": f"Post {i} resumo"},
            )
            intelligence = PostIntelligence(
                post_id=post.id,
                agro_topic_cluster="gestão",
                agro_segment="grãos",
                technical_depth="intermediário",
                core_argument=f"Post {i} conecta resultado no campo com gestão.",
                argument_structure="resultado -> contexto -> ação",
                technical_claims=[f"Post {i} usa resultado no campo como prova."],
                data_points=[],
                sources_referenced=[],
                replication_template="[resultado] + [contexto] + [ação]",
                visual_transcript=f"Slide 1: Post {i} resumo visual.",
            )
            s.add_all([analysis, intelligence])
        s.commit()
        yield s


MOCK_REPORT_RESPONSE = {
    "top_formats": {"foto real": 3},
    "top_themes": {"campo": 3},
    "language_patterns": {"tom": "inspirador"},
    "top_hashtags": ["agro"],
    "viral_posts": [],
    "report_text": "# Relatório Semanal\nForma mais viral: foto real com tema campo.",
}


def test_generate_weekly_report_creates_report(session_with_analyses):
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(MOCK_REPORT_RESPONSE)
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    period_start = datetime(2026, 4, 7, tzinfo=timezone.utc)
    period_end = datetime(2026, 4, 13, tzinfo=timezone.utc)

    with patch("src.reporter.weekly_report.openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        report = generate_weekly_report(
            session=session_with_analyses,
            period_start=period_start,
            period_end=period_end,
        )

    assert report.id is not None
    assert report.top_formats == {"foto real": 3}
    assert "Relatório" in report.report_text
    saved = session_with_analyses.query(WeeklyReport).first()
    assert saved is not None
