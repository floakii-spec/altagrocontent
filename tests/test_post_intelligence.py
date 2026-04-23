import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

import json
import sys
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session
from src.models import Base, Post, Profile, PostIntelligence

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


def _make_post(session):
    profile = Profile(handle="test_user", type="competitor", follower_count=10000)
    session.add(profile)
    session.flush()
    post = Post(
        profile_id=profile.id,
        instagram_id="post_001",
        image_url="https://example.com/img.jpg",
        caption="Soja transgênica aumenta produtividade em 20% segundo Embrapa 2023.",
        hashtags=["#soja", "#agro"],
        likes=500,
        comments=30,
        post_type="feed",
        published_at=datetime.now(timezone.utc),
    )
    session.add(post)
    session.commit()
    return post


def _mock_gpt(data: dict):
    msg = MagicMock()
    msg.content = json.dumps(data)
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def _mock_text(text: str):
    msg = MagicMock()
    msg.content = text
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


_SAMPLE_RESPONSE = {
    "agro_topic_cluster": "soja",
    "agro_segment": "grãos",
    "technical_depth": "especialista",
    "core_argument": "Soja transgênica reduz custos e aumenta produtividade.",
    "argument_structure": "dado chocante → causa técnica → solução → prova",
    "technical_claims": ["Aumento de 20% na produtividade com soja RR"],
    "data_points": [{"value": "20%", "context": "aumento de produtividade", "source": "Embrapa 2023"}],
    "sources_referenced": ["Embrapa"],
    "knowledge_assumptions": "Produtor já conhece soja convencional",
    "content_gaps": "Não mencionou impacto ambiental",
    "replication_template": "[DADO] + [CAUSA] + [SOLUÇÃO] + [CTA]",
    "slide_breakdown": [
        {"slide_number": 1, "role": "hook", "summary": "Abre com o dado central", "key_data": ["20%"]},
        {"slide_number": 2, "role": "prova", "summary": "Traz a fonte", "key_data": ["Embrapa 2023"]},
    ],
    "carousel_complexity": {
        "slide_count": 2,
        "structure_style": "linear_argument",
        "information_density": "alta",
        "proof_strength": "alta",
        "narrative_cohesion": "alta",
        "context_dependency": "media",
        "complexity_score": 4,
        "why_it_works": "Organiza dado e prova em sequência lógica.",
        "replication_risk": "Sem prova equivalente o formato perde força.",
    },
}


def test_analyze_stores_all_fields():
    from src.analyzer.post_intelligence import analyze_post_intelligence
    with Session(engine) as s:
        post = _make_post(s)
        with patch("src.analyzer.post_intelligence._transcribe_visual_assets",
                   return_value="Slide 1: 20% de aumento segundo Embrapa."), patch(
            "src.analyzer.post_intelligence.openai_client.chat.completions.create",
            return_value=_mock_gpt(_SAMPLE_RESPONSE),
        ):
            mock_extractor = MagicMock()
            sys.modules['src.analyzer.argument_extractor'] = mock_extractor
            try:
                result = analyze_post_intelligence(post, s)
            finally:
                del sys.modules['src.analyzer.argument_extractor']
    assert result.agro_topic_cluster == "soja"
    assert result.agro_segment == "grãos"
    assert result.technical_depth == "especialista"
    assert result.core_argument == "Soja transgênica reduz custos e aumenta produtividade."
    assert result.argument_structure == "dado chocante → causa técnica → solução → prova"
    assert result.technical_claims == ["Aumento de 20% na produtividade com soja RR"]
    assert len(result.data_points) == 1
    assert result.data_points[0]["value"] == "20%"
    assert result.sources_referenced == ["Embrapa"]
    assert result.knowledge_assumptions == "Produtor já conhece soja convencional"
    assert result.content_gaps == "Não mencionou impacto ambiental"
    assert result.replication_template == "[DADO] + [CAUSA] + [SOLUÇÃO] + [CTA]"
    assert result.visual_transcript == "Slide 1: 20% de aumento segundo Embrapa."
    assert result.slide_breakdown[0]["role"] == "hook"
    assert result.carousel_complexity["complexity_score"] == 4


def test_analyze_skips_if_already_done():
    from src.analyzer.post_intelligence import analyze_post_intelligence
    with Session(engine) as s:
        post = _make_post(s)
        existing = PostIntelligence(
            post_id=post.id,
            technical_claims=[],
            data_points=[],
            sources_referenced=[],
            analyzed_at=datetime.now(timezone.utc),
        )
        s.add(existing)
        s.commit()
        with patch("src.analyzer.post_intelligence.openai_client.chat.completions.create") as mock_gpt:
            result = analyze_post_intelligence(post, s)
    mock_gpt.assert_not_called()
    assert result.id == existing.id


def test_analyze_persists_to_db():
    from src.analyzer.post_intelligence import analyze_post_intelligence
    with Session(engine) as s:
        post = _make_post(s)
        with patch("src.analyzer.post_intelligence._transcribe_visual_assets",
                   return_value="Slide 1: 20% de aumento segundo Embrapa."), patch(
            "src.analyzer.post_intelligence.openai_client.chat.completions.create",
            return_value=_mock_gpt(_SAMPLE_RESPONSE),
        ):
            mock_extractor = MagicMock()
            sys.modules['src.analyzer.argument_extractor'] = mock_extractor
            try:
                analyze_post_intelligence(post, s)
            finally:
                del sys.modules['src.analyzer.argument_extractor']
    with Session(engine) as s:
        row = s.query(PostIntelligence).first()
    assert row is not None
    assert row.agro_segment == "grãos"
    assert row.visual_transcript == "Slide 1: 20% de aumento segundo Embrapa."
    assert row.carousel_complexity["structure_style"] == "linear_argument"


def test_force_reanalysis_replaces_old_carousel_intelligence():
    from src.analyzer.post_intelligence import analyze_post_intelligence
    with Session(engine) as s:
        post = _make_post(s)
        post.post_type = "carousel"
        post.slides = ["https://example.com/s1.jpg", "https://example.com/s2.jpg"]
        existing = PostIntelligence(
            post_id=post.id,
            technical_claims=["Velho argumento 10%"],
            data_points=[{"value": "10%", "context": "dado antigo", "source": "Fonte antiga"}],
            sources_referenced=["Fonte antiga"],
            visual_transcript="Slide 1: dado antigo 10%",
            slide_breakdown=[{"slide_number": 1, "role": "hook", "summary": "antigo", "key_data": ["10%"]}],
            carousel_complexity={"complexity_score": 1},
            analyzed_at=datetime.now(timezone.utc),
        )
        s.add(existing)
        s.commit()
        with patch("src.analyzer.post_intelligence._transcribe_visual_assets",
                   return_value="Slide 1: 20% de aumento segundo Embrapa.\nSlide 2: Prova técnica."), patch(
            "src.analyzer.post_intelligence.openai_client.chat.completions.create",
            return_value=_mock_gpt(_SAMPLE_RESPONSE),
        ):
            result = analyze_post_intelligence(post, s, force=True)

    assert result.technical_claims == ["Aumento de 20% na produtividade com soja RR"]
    assert result.visual_transcript == "Slide 1: 20% de aumento segundo Embrapa.\nSlide 2: Prova técnica."
    assert result.carousel_complexity["complexity_score"] == 4
