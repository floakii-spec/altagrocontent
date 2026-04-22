import json
import logging
from openai import OpenAI
from sqlalchemy.orm import Session, joinedload
from src.config import OPENAI_API_KEY
from src.models import ArgumentBank, Carousel, Post, PostAnalysis, Profile, ProfileVoice, WeeklyReport

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """Você é um copywriter especialista em carrosséis virais para Instagram no agronegócio brasileiro.
Com base no perfil de voz do criador, nos templates e estruturas reais dos cards dos concorrentes de maior viralidade, e nos argumentos de alto desempenho, crie um carrossel sobre o tema fornecido.

Priorize replicar as estruturas de cards que mais performaram — argumento central forte, dado técnico específico, comparativo ou CTA claro.

Retorne um JSON com a estrutura de slides:
[
  {"slide_number": 1, "title": "<título impactante>", "copy": "<texto do slide>", "cta": ""},
  ...
  {"slide_number": N, "title": "<título>", "copy": "<texto>", "cta": "<chamada para ação>"}
]
- Entre 4 e 7 slides
- Slide 1: gancho que para o scroll
- Slides intermediários: desenvolvimento com dados técnicos e linguagem do criador
- Último slide: CTA claro
Responda APENAS com o JSON."""


def generate_carousel(theme: str, session: Session) -> Carousel:
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

    top_args = (
        session.query(ArgumentBank)
        .filter(ArgumentBank.origin == "extracted")
        .order_by((ArgumentBank.virality_weight * ArgumentBank.quality_score).desc())
        .limit(5)
        .all()
    )

    # Top competitor posts with PostIntelligence — structures to replicate
    top_competitor_posts = (
        session.query(Post)
        .join(Profile, Post.profile_id == Profile.id)
        .join(Post.analysis)
        .join(Post.intelligence)
        .options(joinedload(Post.intelligence), joinedload(Post.analysis))
        .filter(Profile.type == "competitor", Profile.active == True)
        .order_by(PostAnalysis.virality_score.desc())
        .limit(8)
        .all()
    )

    competitor_structures = [
        {
            "replication_template": p.intelligence.replication_template,
            "argument_structure": p.intelligence.argument_structure,
            "core_argument": p.intelligence.core_argument,
            "technical_claims": (p.intelligence.technical_claims or [])[:2],
            "slide_breakdown": (getattr(p.intelligence, "slide_breakdown", []) or [])[:6],
            "carousel_complexity": getattr(p.intelligence, "carousel_complexity", {}) or {},
            "virality_score": p.analysis.virality_score,
        }
        for p in top_competitor_posts
        if p.intelligence.replication_template or p.intelligence.argument_structure
    ]

    if not voice:
        logger.warning("No ProfileVoice found — carousel will use neutral defaults.")
    if not report:
        logger.warning("No WeeklyReport found — carousel will use no competitive report data.")
    if not competitor_structures:
        logger.warning("No competitor PostIntelligence found — carousel will lack structural reference.")

    context = {
        "tema": theme,
        "perfil_de_voz": {
            "tom": voice.tone if voice else "neutro",
            "temas_dominantes": voice.dominant_themes if voice else [],
            "vocabulario": voice.vocabulary if voice else {},
            "resumo": voice.voice_summary if voice else "",
        } if voice else {},
        "estruturas_virais_concorrentes": competitor_structures,
        "padroes_semanais": {
            "formatos_top": report.top_formats if report else {},
            "temas_top": report.top_themes if report else {},
            "resumo": report.report_text if report else "",
        } if report else {},
        "argumentos_de_alto_desempenho": [a.text for a in top_args],
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

    carousel = Carousel(theme=theme, slides=slides, based_on_reports=[report.id] if report else [])
    session.add(carousel)
    session.commit()
    logger.info("Carousel generated for theme '%s' with %d slides", theme, len(slides))
    return carousel
