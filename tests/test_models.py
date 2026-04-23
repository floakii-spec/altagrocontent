import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, Profile, Post, PostAnalysis, ProfileVoice, WeeklyReport, Carousel
from src.models import NewsItem, ContentCalendar, GeneratedPost


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


def test_post_has_slides_column(session):
    p = Profile(handle="h2", type="competitor", niche="agro", follower_count=100)
    session.add(p)
    session.flush()
    post = Post(
        profile_id=p.id,
        instagram_id="IG_SLIDES",
        image_url="https://example.com/cover.jpg",
        caption="Carrossel teste",
        hashtags=[],
        likes=0,
        comments=0,
        post_type="carousel",
        published_at=datetime.now(timezone.utc),
        slides=["https://example.com/s1.jpg", "https://example.com/s2.jpg"],
    )
    session.add(post)
    session.commit()
    assert post.slides == ["https://example.com/s1.jpg", "https://example.com/s2.jpg"]


def test_post_analysis_has_carousel_narrative(session):
    p = Profile(handle="h3", type="competitor", niche="agro", follower_count=100)
    session.add(p)
    session.flush()
    post = Post(profile_id=p.id, instagram_id="IG_NAR", image_url="u", caption="c",
                hashtags=[], likes=0, comments=0, post_type="carousel",
                published_at=datetime.now(timezone.utc))
    session.add(post)
    session.flush()
    analysis = PostAnalysis(
        post_id=post.id,
        virality_score=0.5,
        raw_analysis={},
        carousel_narrative={
            "slide_count": 5,
            "slides": [{"index": 0, "role": "hook", "text": "Você está perdendo dinheiro"}],
            "narrative_arc": "Problema → Causa → Solução → Prova → CTA",
        },
    )
    session.add(analysis)
    session.commit()
    assert analysis.carousel_narrative["slide_count"] == 5


def test_generated_post_strategy_fields(session):
    p = Profile(handle="h4", type="competitor", niche="agro", follower_count=100)
    session.add(p)
    session.flush()
    post = Post(profile_id=p.id, instagram_id="IG_GP", image_url="u", caption="c",
                hashtags=[], likes=0, comments=0, post_type="feed",
                published_at=datetime.now(timezone.utc))
    session.add(post)
    session.flush()
    gp = GeneratedPost(
        source_post_id=post.id,
        hook="Você sabia que 80% dos agrônomos erram nisso?",
        caption="Legenda completa aqui.",
        cta="Entre na Confraria.",
        funnel_stage="topo",
        format="carousel",
        slides=[
            {"slide_number": 1, "slide_type": "CAPA", "title": "Capa", "copy": "Texto", "cta": ""},
            {"slide_number": 2, "slide_type": "HOOK", "title": "Hook", "copy": "Texto", "cta": ""},
            {"slide_number": 3, "slide_type": "CTA", "title": "CTA", "copy": "Texto", "cta": "Entre na Confraria."},
        ],
        planning_narrative={
            "tensao_central": "A produtividade nao garante margem.",
            "angulo_de_adaptacao": "Traduzir dado em decisao comercial no agro.",
            "camadas": [
                {"numero": 1, "tipo_slide": "CAPA"},
                {"numero": 2, "tipo_slide": "HOOK"},
                {"numero": 3, "tipo_slide": "CTA"},
            ],
            "total_slides": 3,
            "provas_que_nao_podem_sumir": ["12%", "R$ 18/sc"],
            "onde_termina": "Quando o leitor entende a decisao pratica.",
        },
        hook_variations={
            "provocacao": "80% dos agrônomos erram nisso.",
            "dado": "Pesquisa aponta: produtores que usam esse método ganham 30% mais.",
            "pergunta": "Você já calculou quanto perde por não fazer isso?",
        },
        news_item_ids=[1, 2],
    )
    session.add(gp)
    session.commit()
    assert gp.funnel_stage == "topo"
    assert gp.slides[0]["slide_type"] == "CAPA"
    assert gp.planning_narrative["tensao_central"] == "A produtividade nao garante margem."
    assert gp.hook_variations["provocacao"].startswith("80%")


def test_news_item_create(session):
    from datetime import datetime, timezone
    item = NewsItem(
        source="canal_rural",
        title="Soja atinge recorde de exportação",
        summary="Exportações de soja batem recorde histórico no primeiro trimestre.",
        url="https://canalrural.com.br/noticia/soja-recorde",
        published_at=datetime.now(timezone.utc),
        tags=["soja", "exportação", "mercado"],
    )
    session.add(item)
    session.commit()
    assert item.id is not None
    assert "soja" in item.tags


def test_content_calendar_create(session):
    from datetime import datetime, timezone
    cal = ContentCalendar(
        week_start=datetime(2026, 4, 21, tzinfo=timezone.utc),
        entries=[
            {"day": "segunda", "funnel_stage": "topo", "format": "carousel",
             "topic": "Rentabilidade da soja", "angle": "Dado de mercado surpresa",
             "hook": "Você sabia que o custo médio por hectare subiu 18% em 2025?"},
            {"day": "quarta", "funnel_stage": "meio", "format": "feed",
             "topic": "Técnica de negociação com revendedor", "angle": "Prático",
             "hook": "3 erros que todo agrônomo comete na hora de negociar insumos"},
        ],
    )
    session.add(cal)
    session.commit()
    assert len(cal.entries) == 2
