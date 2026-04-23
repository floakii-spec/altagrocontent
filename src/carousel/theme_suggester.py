import json
import logging
from datetime import datetime, timezone, timedelta

from openai import OpenAI
from sqlalchemy.orm import Session, joinedload

from src.config import OPENAI_API_KEY
from src.analyzer.gap_analyzer import compute_gaps
from src.generator.creative_intelligence import build_theme_creative_brief
from src.models import CarouselSuggestion, NewsItem, Post, PostAnalysis, PostIntelligence

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

_SYSTEM_PROMPT = """Você é especialista em marketing de conteúdo para o agronegócio brasileiro no Instagram.
Crie exatamente 6 sugestões de tema para carrosséis com alta chance de viralização.
Use os dados fornecidos (gaps, posts virais com estrutura de cards, notícias) e complemente com seu próprio conhecimento sobre sazonalidade, mercado e tendências agro.
Cada sugestão precisa nascer de uma tensão real do agro: erro caro, margem, risco, decisão atrasada, oportunidade perdida ou contraste técnico/comercial.
Retorne APENAS um JSON array com exatamente 6 objetos:
[{"title": "<tema curto e impactante>", "rationale": "<uma frase explicando o sinal de dados>"}, ...]"""


def generate_theme_suggestions(session: Session) -> CarouselSuggestion:
    gaps = compute_gaps(session)
    top_gaps = [g["topic"] for g in gaps[:5]]

    viral_posts = (
        session.query(Post)
        .join(Post.analysis)
        .join(Post.intelligence)
        .options(joinedload(Post.intelligence), joinedload(Post.analysis))
        .filter(PostAnalysis.virality_score > 0.5)
        .order_by(PostAnalysis.virality_score.desc())
        .limit(5)
        .all()
    )

    viral_structures = [
        {
            "core_argument": p.intelligence.core_argument,
            "replication_template": p.intelligence.replication_template,
            "agro_topic_cluster": p.intelligence.agro_topic_cluster,
            "visual_transcript": (getattr(p.intelligence, "visual_transcript", "") or "")[:1200],
            "virality_score": p.analysis.virality_score,
        }
        for p in viral_posts
    ]

    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    news = (
        session.query(NewsItem)
        .filter(NewsItem.published_at >= cutoff)
        .order_by(NewsItem.published_at.desc())
        .limit(10)
        .all()
    )
    news_titles = [n.title for n in news]

    user_content = json.dumps({
        "gap_topics": top_gaps,
        "viral_post_structures": viral_structures,
        "recent_news": news_titles,
        "inteligencia_criativa_agro": build_theme_creative_brief(
            "sugestoes de temas para carrossel",
            viral_posts,
            [],
            None,
        ),
    }, ensure_ascii=False)

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        max_tokens=800,
    )

    raw = response.choices[0].message.content or ""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rstrip("`").strip()

    try:
        themes = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("GPT-4o returned invalid JSON for theme suggestions. Raw: %r Error: %s", raw, exc)
        raise

    suggestion = CarouselSuggestion(themes=themes)
    session.add(suggestion)
    session.commit()
    session.refresh(suggestion)
    logger.info("Generated %d theme suggestions", len(themes))
    return suggestion
