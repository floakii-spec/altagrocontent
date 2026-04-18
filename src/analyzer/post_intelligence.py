import json
import logging

from openai import OpenAI
from sqlalchemy.orm import Session

from src.config import OPENAI_API_KEY
from src.models import Post, PostIntelligence

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

_VISION_PROMPT = """Você está analisando um post de Instagram do agronegócio brasileiro.
Transcreva TODO o conteúdo visível na imagem: textos, números, percentuais, gráficos, tabelas, legendas, marcas e qualquer dado presente no card visual.
Seja completo e literal — não interprete, apenas transcreva o que está escrito/mostrado."""

_SYSTEM_PROMPT = """Você é um analista de conteúdo especialista em agronegócio brasileiro.
Analise o post fornecido com profundidade técnica e retorne APENAS um JSON:
{
  "agro_topic_cluster": "<soja|milho|pecuária|insumos|gestão|tecnologia|crédito|outro>",
  "agro_segment": "<grãos|fibras|pecuária|horticultura|cafeicultura|geral>",
  "technical_depth": "<superficial|intermediário|especialista>",
  "core_argument": "<tese central em uma frase direta>",
  "argument_structure": "<fluxo lógico: ex. dado chocante → causa → solução → prova>",
  "technical_claims": ["<afirmação técnica 1>", "<afirmação técnica 2>"],
  "data_points": [{"value": "<número>", "context": "<contexto>", "source": "<fonte ou null>"}],
  "sources_referenced": ["<Embrapa>", "<MAPA>", "<pesquisa própria>"],
  "knowledge_assumptions": "<o que assume que a audiência já sabe>",
  "content_gaps": "<o que ficou de fora e enriqueceria o conteúdo>",
  "replication_template": "<fórmula replicável: ex. [DADO] + [CAUSA] + [SOLUÇÃO] + [CTA]>"
}"""


def _transcribe_image(image_url: str) -> str:
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": _VISION_PROMPT},
                    {"type": "image_url", "image_url": {"url": image_url, "detail": "high"}},
                ],
            }],
            max_tokens=500,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        logger.warning("Vision transcription failed for %s: %s", image_url, exc)
        return ""


def analyze_post_intelligence(post: Post, session: Session) -> PostIntelligence:
    existing = session.query(PostIntelligence).filter_by(post_id=post.id).first()
    if existing:
        return existing

    caption = post.caption or ""
    hashtags = ", ".join(post.hashtags) if post.hashtags else ""

    visual_transcript = ""
    if post.image_url:
        visual_transcript = _transcribe_image(post.image_url)

    parts = []
    if visual_transcript:
        parts.append(f"Conteúdo visual do card:\n{visual_transcript}")
    parts.append(f"Legenda: {caption}")
    if hashtags:
        parts.append(f"Hashtags: {hashtags}")
    user_content = "\n\n".join(parts)

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        max_tokens=1000,
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
        logger.error("GPT-4o returned invalid JSON for post %s: %s", post.id, exc)
        raise

    intelligence = PostIntelligence(
        post_id=post.id,
        agro_topic_cluster=data.get("agro_topic_cluster"),
        agro_segment=data.get("agro_segment"),
        technical_depth=data.get("technical_depth"),
        core_argument=data.get("core_argument"),
        argument_structure=data.get("argument_structure"),
        technical_claims=data.get("technical_claims", []),
        data_points=data.get("data_points", []),
        sources_referenced=data.get("sources_referenced", []),
        knowledge_assumptions=data.get("knowledge_assumptions"),
        content_gaps=data.get("content_gaps"),
        replication_template=data.get("replication_template"),
    )
    session.add(intelligence)
    session.commit()
    session.refresh(intelligence)

    from src.analyzer.argument_extractor import upsert_arguments
    upsert_arguments(intelligence, post, session)

    logger.info("Post %s intelligence analyzed: depth=%s, claims=%d",
                post.id, intelligence.technical_depth, len(intelligence.technical_claims))
    return intelligence
