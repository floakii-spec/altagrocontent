import json
import logging
from openai import OpenAI
from sqlalchemy.orm import Session
from src.config import OPENAI_API_KEY
from src.models import ProfileVoice, WeeklyReport, Carousel, ArgumentBank

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """Você é um copywriter especialista em carrosséis virais para Instagram no agronegócio brasileiro.
Com base no perfil de voz do criador e nos padrões virais dos concorrentes, crie um carrossel sobre o tema fornecido.
Retorne um JSON com a estrutura de slides:
[
  {"slide_number": 1, "title": "<título impactante>", "copy": "<texto do slide>", "cta": ""},
  ...
  {"slide_number": N, "title": "<título>", "copy": "<texto>", "cta": "<chamada para ação>"}
]
- Entre 4 e 7 slides
- Slide 1: gancho que para o scroll
- Slides intermediários: desenvolvimento do tema com linguagem do criador
- Último slide: CTA claro
Responda APENAS com o JSON."""


def generate_carousel(theme: str, session: Session) -> Carousel:
    """Gera carrossel viral com base no tema, voz própria e último relatório semanal."""
    voice = (
        session.query(ProfileVoice)
        .order_by(ProfileVoice.generated_at.desc())
        .first()
    )
    report = (
        session.query(WeeklyReport)
        .order_by(WeeklyReport.generated_at.desc())
        .first()
    )

    if not voice:
        logger.warning("No ProfileVoice found — carousel will use neutral defaults.")
    if not report:
        logger.warning("No WeeklyReport found — carousel will use no competitive data.")

    top_args = (
        session.query(ArgumentBank)
        .filter(ArgumentBank.origin == "extracted")
        .order_by((ArgumentBank.virality_weight * ArgumentBank.quality_score).desc())
        .limit(5)
        .all()
    )
    top_arg_texts = [a.text for a in top_args]

    context = {
        "tema": theme,
        "perfil_de_voz": {
            "tom": voice.tone if voice else "neutro",
            "temas_dominantes": voice.dominant_themes if voice else [],
            "vocabulario": voice.vocabulary if voice else {},
        } if voice else {},
        "padroes_virais_concorrentes": {
            "formatos_top": report.top_formats if report else {},
            "temas_top": report.top_themes if report else {},
            "resumo": report.report_text[:500] if report else "",
        } if report else {},
        "argumentos_de_alto_desempenho": top_arg_texts,
    }

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ],
        max_tokens=1200,
    )

    raw = response.choices[0].message.content or ""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rstrip("`").strip()

    try:
        slides = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("GPT-4o returned invalid JSON for carousel theme '%s': %s", theme, exc)
        raise

    report_ids = [report.id] if report else []

    carousel = Carousel(theme=theme, slides=slides, based_on_reports=report_ids)
    session.add(carousel)
    session.commit()
    logger.info("Carousel generated for theme '%s' with %d slides", theme, len(slides))
    return carousel
