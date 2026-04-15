import json
import logging
from datetime import datetime
from openai import OpenAI
from sqlalchemy.orm import Session
from src.config import OPENAI_API_KEY
from src.models import Post, PostAnalysis, WeeklyReport

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """Você é um estrategista de conteúdo para agronegócio.
Com base nas análises de posts dos concorrentes, gere um relatório semanal em JSON com:
{
  "top_formats": {"<formato>": <contagem>},
  "top_themes": {"<tema>": <contagem>},
  "language_patterns": {"<padrão>": "<descrição>"},
  "top_hashtags": ["<hashtag>"],
  "viral_posts": [<post_ids com maior virality_score>],
  "report_text": "<relatório completo em markdown com insights acionáveis>"
}
Responda APENAS com o JSON."""


def generate_weekly_report(session: Session, period_start: datetime, period_end: datetime) -> WeeklyReport:
    """Consolida análises da semana em um relatório via GPT-4o."""
    analyses = (
        session.query(PostAnalysis)
        .join(Post)
        .filter(Post.published_at >= period_start, Post.published_at <= period_end)
        .all()
    )

    if not analyses:
        logger.warning("No analyses found for period %s–%s; skipping report generation.", period_start.date(), period_end.date())
        raise ValueError("No analyses available for the requested period.")

    summaries = [
        {
            "post_id": a.post_id,
            "visual_theme": a.visual_theme,
            "visual_format": a.visual_format,
            "emotional_tone": a.emotional_tone,
            "trigger": a.trigger,
            "virality_score": a.virality_score,
            "summary": a.raw_analysis.get("summary", ""),
        }
        for a in analyses
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Análises da semana:\n{json.dumps(summaries, ensure_ascii=False)}"},
        ],
        max_tokens=1500,
    )

    try:
        raw = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError as exc:
        logger.error("GPT-4o returned invalid JSON for weekly report: %s", exc)
        raise

    report = WeeklyReport(
        period_start=period_start,
        period_end=period_end,
        top_formats=raw.get("top_formats", {}),
        top_themes=raw.get("top_themes", {}),
        language_patterns=raw.get("language_patterns", {}),
        top_hashtags=raw.get("top_hashtags", []),
        viral_posts=raw.get("viral_posts", []),
        report_text=raw.get("report_text", ""),
    )
    session.add(report)
    session.commit()
    logger.info("Weekly report generated for %s–%s", period_start.date(), period_end.date())
    return report
