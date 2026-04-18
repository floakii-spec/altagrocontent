import json
import logging
from datetime import datetime
from openai import OpenAI
from sqlalchemy.orm import Session, joinedload
from src.config import OPENAI_API_KEY
from src.models import Post, PostIntelligence, WeeklyReport

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
  "report_text": "<relatório completo em markdown com insights acionáveis sobre estruturas de cards, argumentos técnicos e templates replicáveis>"
}
Responda APENAS com o JSON."""


def generate_weekly_report(session: Session, period_start: datetime, period_end: datetime) -> WeeklyReport:
    posts = (
        session.query(Post)
        .join(Post.intelligence)
        .outerjoin(Post.analysis)
        .options(joinedload(Post.intelligence), joinedload(Post.analysis))
        .filter(Post.published_at >= period_start, Post.published_at <= period_end)
        .all()
    )

    if not posts:
        logger.warning("No posts with intelligence found for period %s–%s; skipping report.", period_start.date(), period_end.date())
        raise ValueError("No intelligence data available for the requested period.")

    summaries = []
    for p in posts:
        intel = p.intelligence
        entry = {
            "post_id": p.id,
            "agro_topic_cluster": intel.agro_topic_cluster,
            "agro_segment": intel.agro_segment,
            "technical_depth": intel.technical_depth,
            "core_argument": intel.core_argument,
            "argument_structure": intel.argument_structure,
            "replication_template": intel.replication_template,
            "technical_claims": (intel.technical_claims or [])[:3],
            "sources_referenced": intel.sources_referenced or [],
        }
        if p.analysis:
            entry["virality_score"] = p.analysis.virality_score
        summaries.append(entry)

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Análises da semana:\n{json.dumps(summaries, ensure_ascii=False)}"},
        ],
        max_tokens=1500,
    )

    raw = response.choices[0].message.content or ""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rstrip("`").strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("GPT-4o returned invalid JSON for weekly report: %s", exc)
        raise

    report = WeeklyReport(
        period_start=period_start,
        period_end=period_end,
        top_formats=data.get("top_formats", {}),
        top_themes=data.get("top_themes", {}),
        language_patterns=data.get("language_patterns", {}),
        top_hashtags=data.get("top_hashtags", []),
        viral_posts=data.get("viral_posts", []),
        report_text=data.get("report_text", ""),
    )
    session.add(report)
    session.commit()
    logger.info("Weekly report generated for %s–%s", period_start.date(), period_end.date())
    return report
