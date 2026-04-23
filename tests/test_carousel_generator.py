import json
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, Profile, WeeklyReport, ProfileVoice, Carousel, Post, PostAnalysis, PostIntelligence
from src.carousel.generator import _build_validated_theme_catalog, generate_carousel


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
    {"slide_number": 1, "slide_type": "CAPA", "title": "Você sabia?", "copy": "A soja brasileira...", "cta": ""},
    {"slide_number": 2, "slide_type": "HOOK", "title": "O erro que derruba produtividade", "copy": "Muitos produtores deixam o manejo reagir tarde demais.", "cta": ""},
    {"slide_number": 3, "slide_type": "DESENVOLVIMENTO", "title": "A solução", "copy": "Na pratica, com manejo correto o produtor decide antes e protege melhor a margem.", "cta": ""},
    {"slide_number": 4, "slide_type": "PROVA", "title": "A prova", "copy": "Um exemplo de ganho real no campo com numero e comparativo claro...", "cta": ""},
    {"slide_number": 5, "slide_type": "CTA", "title": "Resultado", "copy": "Até 30% mais produtividade", "cta": "Salve este post!"},
]


def _with_planning_narrative(slides):
    return {
        "planejamento_narrativo": {
            "tensao_central": "O produtor pode perder resultado por reagir tarde demais no manejo.",
            "angulo_especifico": "Produtividade depende de decisao feita antes do problema aparecer.",
            "camadas": [
                {
                    "numero": index,
                    "tipo_slide": slide["slide_type"],
                    "funcao_narrativa": slide["title"],
                    "pergunta_que_abre": slides[index]["title"] if index < len(slides) else "Qual a acao pratica?",
                    "emocao_alvo": ["espanto", "admiracao", "analise", "revelacao", "sintese"][min(index - 1, 4)],
                }
                for index, slide in enumerate(slides, start=1)
            ],
            "total_slides": len(slides),
            "onde_termina": "Quando o leitor entende o erro, a prova e a acao final.",
        },
        "slides": slides,
    }


def test_generate_carousel_returns_slides(session_with_context):
    session, profile, voice, report = session_with_context
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(_with_planning_narrative(MOCK_SLIDES))
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("src.carousel.generator.openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        carousel = generate_carousel(
            theme="Manejo de soja para alta produtividade",
            session=session,
        )

    context = json.loads(mock_client.chat.completions.create.call_args.kwargs["messages"][1]["content"])
    assert "inteligencia_criativa_agro" in context
    assert context["inteligencia_criativa_agro"]["mandato_criativo"]
    assert len(carousel.slides) == 5
    assert carousel.slides[0]["title"] == "Você sabia?"
    assert carousel.slides[0]["slide_type"] == "CAPA"
    assert carousel.slides[-2]["slide_type"] == "DADO"
    assert carousel.slides[-1]["cta"] == "Salve este post!"
    saved = session.query(Carousel).first()
    assert saved is not None


def test_generate_carousel_retries_when_initial_draft_is_weak(session_with_context):
    session, profile, voice, report = session_with_context
    weak_slides = [
        {"slide_number": 1, "slide_type": "CAPA", "title": "Tema", "copy": "Texto", "cta": ""},
        {"slide_number": 2, "slide_type": "HOOK", "title": "Gancho", "copy": "Texto", "cta": ""},
        {"slide_number": 3, "slide_type": "DESENVOLVIMENTO", "title": "Miolo", "copy": "Texto curto", "cta": ""},
        {"slide_number": 4, "slide_type": "CTA", "title": "Fechamento", "copy": "Texto", "cta": "Salve"},
    ]
    mock_response_weak = MagicMock()
    mock_response_weak.choices = [MagicMock(message=MagicMock(content=json.dumps(weak_slides)))]
    mock_response_strong = MagicMock()
    mock_response_strong.choices = [MagicMock(message=MagicMock(content=json.dumps(_with_planning_narrative(MOCK_SLIDES))))]

    with patch("src.carousel.generator.openai_client") as mock_client:
        mock_client.chat.completions.create.side_effect = [mock_response_weak, mock_response_strong]
        carousel = generate_carousel(
            theme="Manejo de soja para alta produtividade",
            session=session,
        )

    assert mock_client.chat.completions.create.call_count == 2
    assert carousel.slides[-2]["slide_type"] == "DADO"


def test_theme_catalog_includes_visual_transcript(session_with_context):
    session, profile, voice, report = session_with_context
    competitor = Profile(handle="concorrente", type="competitor", follower_count=10000)
    session.add(competitor)
    session.flush()
    post = Post(
        profile_id=competitor.id,
        instagram_id="TRANSCRIPT-1",
        image_url="https://example.com/card.jpg",
        caption="Legenda do concorrente",
        hashtags=["soja"],
        likes=900,
        comments=40,
        post_type="carousel",
        published_at=datetime(2026, 4, 20, tzinfo=timezone.utc),
    )
    session.add(post)
    session.flush()
    session.add_all([
        PostAnalysis(post_id=post.id, virality_score=0.91, raw_analysis={}),
        PostIntelligence(
            post_id=post.id,
            agro_topic_cluster="gestão",
            agro_segment="grãos",
            technical_claims=["12% de margem muda a decisão comercial."],
            data_points=[{"value": "12%", "context": "diferença de margem", "source": "levantamento interno"}],
            sources_referenced=["levantamento interno"],
            visual_transcript="Slide 1: 12% de margem muda o jogo.\nSlide 2: R$ 18/sc no resultado líquido.",
        ),
    ])
    session.commit()

    catalog = _build_validated_theme_catalog("margem na soja", [], [post], report)

    assert catalog["provas_de_posts_virais"][0]["visual_transcript"].startswith("Slide 1: 12%")
