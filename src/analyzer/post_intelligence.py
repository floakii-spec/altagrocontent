import base64
import json
import logging
import re as _re
from types import SimpleNamespace
from typing import Any

import httpx
from openai import OpenAI
from sqlalchemy.orm import Session

from src.config import OPENAI_API_KEY
from src.models import Post, PostIntelligence

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

_VISION_PROMPT = """Você está analisando um post de Instagram do agronegócio brasileiro.
Transcreva TODO o conteúdo visível de cada slide/card: textos, números, percentuais, gráficos, tabelas, legendas, marcas e qualquer dado presente no visual.
Se houver múltiplos slides, mantenha a numeração de cada um claramente separada como "Slide 1", "Slide 2", etc.
Seja completo e literal — não interprete, apenas transcreva o que está escrito/mostrado."""

_SYSTEM_PROMPT = """Você é um analista de conteúdo especialista em agronegócio brasileiro.

O post será fornecido com três seções:
1. "Conteúdo visual do card/carrossel" — transcrição literal do que aparece no visual, com slides numerados quando houver vários cards
2. "Legenda" — texto da publicação no Instagram
3. "Hashtags" — tags usadas

IMPORTANTE: o card visual é a fonte primária de dados técnicos. A legenda geralmente complementa ou contextualiza o que está no card. Priorize números, percentuais, comparativos e afirmações do card visual.
Quando houver carrossel, avalie a progressão de slide a slide, a cadência do roteiro, o nível de contexto, a presença de prova e a densidade de informação.

Analise com profundidade técnica e retorne APENAS um JSON:
{
  "agro_topic_cluster": "<soja|milho|pecuária|insumos|gestão|tecnologia|crédito|outro>",
  "agro_segment": "<grãos|fibras|pecuária|horticultura|cafeicultura|geral>",
  "technical_depth": "<superficial|intermediário|especialista — baseado na densidade de dados e especificidade técnica do card>",
  "core_argument": "<tese central do card em uma frase direta com o dado mais impactante>",
  "argument_structure": "<fluxo lógico do card: ex. dado chocante → comparativo → causa → conclusão>",
  "technical_claims": ["<cada afirmação técnica com número ou dado específico do card>"],
  "data_points": [{"value": "<número/percentual exato do card>", "context": "<o que esse número representa>", "source": "<fonte citada no card ou null>"}],
  "sources_referenced": ["<logos, marcas, institutos, pesquisas visíveis no card ou citados na legenda>"],
  "knowledge_assumptions": "<conhecimento prévio que o produtor precisa ter para entender o card>",
  "content_gaps": "<dados importantes que faltaram no card para tornar o argumento mais sólido>",
  "replication_template": "<fórmula do card: ex. [DADO CHOCANTE] + [COMPARATIVO] + [CAUSA] + [CTA]>",
  "slide_breakdown": [
    {
      "slide_number": "<1..N>",
      "role": "<hook|contexto|dado|prova|explicacao|transicao|objeção|cta|fechamento|outro>",
      "summary": "<o que esse slide entrega e por que ele existe no roteiro>",
      "key_data": ["<dados ou pontos-chave específicos daquele slide>"]
    }
  ],
  "carousel_complexity": {
    "slide_count": "<quantidade de slides efetivamente analisados>",
    "structure_style": "<single_punch|linear_argument|layered_analysis|data_stack|story_case|mixed>",
    "information_density": "<baixa|media|alta>",
    "proof_strength": "<baixa|media|alta>",
    "narrative_cohesion": "<baixa|media|alta>",
    "context_dependency": "<baixa|media|alta>",
    "complexity_score": "<1-5>",
    "why_it_works": "<por que o roteiro funciona ou onde ele perde força>",
    "replication_risk": "<o principal risco ao tentar replicar esse formato sem o mesmo contexto>"
  }
}"""

_EVIDENCE_PROMPT = """Analise o conteúdo do post abaixo e extraia o inventário de evidências.

Retorne APENAS um JSON com esta estrutura:
{
  "mechanisms": ["<termo ou conceito-chave central ao argumento, ex: 'recuperação judicial'>"],
  "causal_steps": ["<passo 1 da cadeia lógica>", "<passo 2>"],
  "definitions": [
    {"term": "<termo técnico>", "definition": "<como o post define em linguagem simples>"}
  ]
}

- "mechanisms": máximo 8 termos curtos (2-4 palavras) que são conceitos centrais do argumento.
- "causal_steps": 3-8 eventos em ordem lógica que constroem o argumento. Lista vazia se não houver cadeia causal.
- "definitions": termos que o post explica explicitamente. Lista vazia se não houver.
Responda APENAS com o JSON."""


_MECHANISM_PATTERNS = [
    "recuperação judicial",
    "capital de giro",
    "patrimônio líquido",
    "patrimônio líquido negativo",
    "direito de voto",
    "acionista majoritário",
    "capital externo",
    "fluxo de caixa",
    "gestão financeira",
    "estrutura financeira",
    "passivos",
    "dívidas",
    "credores",
    "investidores",
    "margem",
    "custos de produção",
    "produtividade",
    "crédito rural",
    "seguro rural",
    "barter",
    "correção do solo",
    "gestão hídrica",
    "sementes adaptadas",
    "fixação biológica",
    "plantio direto",
    "rotação de culturas",
]


def _append_unique(values: list[str], value: str, limit: int | None = None) -> None:
    clean = " ".join(str(value).strip().split())
    if not clean or clean in values:
        return
    if limit is not None and len(values) >= limit:
        return
    values.append(clean)


def _extract_number_fragments(text: str) -> list[str]:
    pattern = (
        r"R\$\s*[\d.,]+(?:\s*(?:bi|mi|mil|bilh[õo]es|milh[õo]es))?"
        r"|\b\d+[.,]?\d*\s*(?:%|bi|mi|mil|bilh[õo]es|milh[õo]es|sacas?|hectares?|ha|"
        r"anos?|meses?|dias?|toneladas?|t/ha|kg/ha)\b"
    )
    return [match.strip() for match in _re.findall(pattern, text, flags=_re.IGNORECASE)]


def _fallback_mechanisms(data: dict, caption: str, visual_transcript: str) -> list[str]:
    haystack_parts = [
        data.get("core_argument") or "",
        data.get("argument_structure") or "",
        caption or "",
        visual_transcript or "",
    ]
    haystack_parts.extend(c for c in (data.get("technical_claims") or []) if isinstance(c, str))
    haystack = "\n".join(haystack_parts).lower()

    mechanisms: list[str] = []
    for pattern in _MECHANISM_PATTERNS:
        if pattern in haystack:
            _append_unique(mechanisms, pattern, limit=8)
    return mechanisms


def _fallback_causal_steps(data: dict) -> list[str]:
    steps: list[str] = []
    structure = str(data.get("argument_structure") or "").strip()
    if structure:
        parts = _re.split(r"\s*(?:→|->|=>|;|\n)\s*", structure)
        for part in parts:
            _append_unique(steps, part, limit=8)

    if len(steps) < 3:
        for slide in data.get("slide_breakdown") or []:
            if not isinstance(slide, dict):
                continue
            summary = slide.get("summary") or ""
            _append_unique(steps, summary, limit=8)

    if len(steps) < 3:
        for claim in data.get("technical_claims") or []:
            if isinstance(claim, str):
                _append_unique(steps, claim, limit=8)

    return steps


def _extract_evidence_inventory(
    visual_transcript: str,
    data: dict,
    caption: str,
    use_gpt: bool = True,
) -> dict:
    # Extract numbers from data_points
    numbers: list[str] = []
    seen_numbers: set[str] = set()
    for point in data.get("data_points") or []:
        if isinstance(point, dict):
            value = str(point.get("value", "")).strip()
            if value and value not in seen_numbers:
                seen_numbers.add(value)
                numbers.append(value)
    for claim in data.get("technical_claims") or []:
        if not isinstance(claim, str):
            continue
        for match in _extract_number_fragments(claim):
            if match not in seen_numbers:
                seen_numbers.add(match)
                numbers.append(match)

    mechanisms = _fallback_mechanisms(data, caption, visual_transcript)
    causal_steps = _fallback_causal_steps(data)
    definitions: list[dict] = []

    content_parts = []
    if visual_transcript:
        content_parts.append(f"Conteúdo visual:\n{visual_transcript}")
    if caption:
        content_parts.append(f"Legenda: {caption}")
    content = "\n\n".join(content_parts)

    if use_gpt and content.strip():
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": _EVIDENCE_PROMPT},
                    {"role": "user", "content": content[:6000]},
                ],
                max_tokens=600,
            )
            raw = (response.choices[0].message.content or "").strip()
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.rstrip("`").strip()
            evidence_data = json.loads(raw)
            for mechanism in evidence_data.get("mechanisms") or []:
                _append_unique(mechanisms, mechanism, limit=8)
            gpt_steps = [str(s).strip() for s in evidence_data.get("causal_steps") or [] if str(s).strip()]
            if gpt_steps:
                causal_steps = []
                for step in gpt_steps:
                    _append_unique(causal_steps, step, limit=8)
            definitions = [
                d for d in (evidence_data.get("definitions") or [])
                if isinstance(d, dict) and d.get("term") and d.get("definition")
            ]
        except Exception as exc:
            logger.warning("Evidence inventory GPT extraction failed for post: %s", exc)

    return {
        "required": {
            "numbers": numbers,
            "mechanisms": mechanisms,
            "causal_steps": causal_steps,
            "definitions": definitions,
        },
        "optional": {
            "claims": [c.strip() for c in (data.get("technical_claims") or []) if isinstance(c, str) and c.strip()],
            "sources": [str(s).strip() for s in (data.get("sources_referenced") or []) if str(s).strip()],
            "context": data.get("core_argument") or "",
        },
    }


def _to_data_url(image_url: str) -> str:
    img_response = httpx.get(image_url, timeout=20, follow_redirects=True)
    img_response.raise_for_status()
    b64 = base64.b64encode(img_response.content).decode("utf-8")
    media_type = img_response.headers.get("content-type", "image/jpeg").split(";")[0]
    return f"data:{media_type};base64,{b64}"


def _coerce_slide_urls(post: Post) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for raw in post.slides or []:
        if isinstance(raw, str):
            value = raw
        elif isinstance(raw, dict):
            value = raw.get("image_url") or raw.get("display_url") or raw.get("url")
        else:
            value = None
        if not value or value in seen:
            continue
        seen.add(value)
        urls.append(value)

    if not urls and post.image_url:
        urls.append(post.image_url)
    return urls


def _transcribe_visual_assets(post: Post) -> str:
    try:
        urls = _coerce_slide_urls(post)
        if not urls:
            return ""

        content: list[dict[str, Any]] = [{"type": "text", "text": _VISION_PROMPT}]
        for index, image_url in enumerate(urls, start=1):
            content.extend([
                {"type": "text", "text": f"Slide {index}"},
                {"type": "image_url", "image_url": {"url": _to_data_url(image_url), "detail": "high"}},
            ])

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": content,
            }],
            max_tokens=3200,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        logger.warning("Vision transcription failed for post %s: %s", post.id, exc)
        return ""


def _snapshot_intelligence(intelligence: PostIntelligence) -> SimpleNamespace:
    return SimpleNamespace(
        technical_claims=list(intelligence.technical_claims or []),
        data_points=list(intelligence.data_points or []),
        sources_referenced=list(intelligence.sources_referenced or []),
    )


def analyze_post_intelligence(post: Post, session: Session, force: bool = False) -> PostIntelligence:
    existing = session.query(PostIntelligence).filter_by(post_id=post.id).first()
    if existing and not force:
        return existing

    caption = post.caption or ""
    hashtags = ", ".join(post.hashtags) if post.hashtags else ""

    visual_transcript = _transcribe_visual_assets(post)

    if not visual_transcript and not caption.strip():
        logger.warning("Post %s has no visual content and no caption — skipping intelligence.", post.id)
        raise ValueError(f"Post {post.id} sem conteúdo visual nem legenda.")

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

    old_intelligence = _snapshot_intelligence(existing) if existing else None
    intelligence = existing or PostIntelligence(post_id=post.id)
    intelligence.agro_topic_cluster = data.get("agro_topic_cluster")
    intelligence.agro_segment = data.get("agro_segment")
    intelligence.technical_depth = data.get("technical_depth")
    intelligence.core_argument = data.get("core_argument")
    intelligence.argument_structure = data.get("argument_structure")
    intelligence.technical_claims = data.get("technical_claims", [])
    intelligence.data_points = data.get("data_points", [])
    intelligence.sources_referenced = data.get("sources_referenced", [])
    intelligence.knowledge_assumptions = data.get("knowledge_assumptions")
    intelligence.content_gaps = data.get("content_gaps")
    intelligence.replication_template = data.get("replication_template")
    intelligence.visual_transcript = visual_transcript.strip() or None
    intelligence.slide_breakdown = data.get("slide_breakdown", [])
    intelligence.carousel_complexity = data.get("carousel_complexity", {})
    intelligence.evidence_inventory = _extract_evidence_inventory(
        visual_transcript or "",
        data,
        caption,
    )
    session.add(intelligence)

    from src.analyzer.argument_extractor import upsert_arguments
    from src.analyzer.argument_extractor import remove_arguments_for_post

    if force and old_intelligence:
        remove_arguments_for_post(old_intelligence, post, session, commit=False)
    upsert_arguments(intelligence, post, session, commit=False)
    session.commit()
    session.refresh(intelligence)

    logger.info(
        "Post %s intelligence analyzed: depth=%s, claims=%d, slides=%d",
        post.id,
        intelligence.technical_depth,
        len(intelligence.technical_claims),
        len(intelligence.slide_breakdown or []),
    )
    return intelligence
