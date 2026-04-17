import json
import logging
from datetime import datetime, timezone, timedelta

from openai import OpenAI
from sqlalchemy.orm import Session

from src.config import OPENAI_API_KEY
from src.analyzer.gap_analyzer import compute_gaps
from src.models import CarouselSuggestion, NewsItem, Post, PostAnalysis

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

_SYSTEM_PROMPT = """Você é especialista em marketing de conteúdo para o agronegócio brasileiro no Instagram.
Crie exatamente 6 sugestões de tema para carrosséis com alta chance de viralização.
Use os dados fornecidos (gaps, posts virais, notícias) e complemente com seu próprio conhecimento sobre sazonalidade, mercado e tendências agro.
Retorne APENAS um JSON array com exatamente 6 objetos:
[{"title": "<tema curto e impactante>", "rationale": "<uma frase explicando o sinal de dados>"}, ...]"""


def generate_theme_suggestions(session: Session) -> CarouselSuggestion:
    """Gather DB signals, call GPT-4o, store and return a CarouselSuggestion row."""
    gaps = compute_gaps(session)
    top_gaps = [g["topic"] for g in gaps[:5]]

    viral_posts = (
        session.query(Post)
        .join(Post.analysis)
        .filter(PostAnalysis.virality_score > 0.5)
        .order_by(PostAnalysis.virality_score.desc())
        .limit(5)
        .all()
    )
    viral_captions = [p.caption for p in viral_posts if p.caption]

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
        "viral_captions": viral_captions,
        "recent_news": news_titles,
    }, ensure_ascii=False)

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        max_tokens=800,
    )

    try:
        themes = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError as exc:
        logger.error("GPT-4o returned invalid JSON for theme suggestions: %s", exc)
        raise

    suggestion = CarouselSuggestion(themes=themes)
    session.add(suggestion)
    session.commit()
    session.refresh(suggestion)
    logger.info("Generated %d theme suggestions", len(themes))
    return suggestion
