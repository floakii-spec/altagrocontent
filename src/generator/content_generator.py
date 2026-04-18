import json
import logging
from datetime import datetime, timezone
from typing import List
from openai import OpenAI
from sqlalchemy.orm import Session
from src.config import OPENAI_API_KEY
from src.models import ArgumentBank, Post, ProfileVoice, GeneratedPost

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

CONFRARIA_CONTEXT = """SOBRE O AUTOR:
- Engenheiro Agrônomo com 15+ anos em vendas, varejo e cooperativismo no agronegócio brasileiro
- Fundador da Confraria de Vendas no Agro: comunidade para quem quer dominar o comercial no campo
- A Confraria inclui: curso Agroroot completo + encontros ao vivo quinzenais com especialistas do agro
- Público-alvo: agrônomos, consultores e profissionais de vendas no agro que querem crescer na carreira comercial"""

_SYSTEM_PROMPT = """Você é um ghostwriter especializado em conteúdo para Instagram no agronegócio brasileiro.

{confraria_context}

PERFIL DE VOZ DO AUTOR:
- Tom: {tone}
- Temas dominantes: {dominant_themes}
- Vocabulário característico: {vocabulary}
- Resumo de voz: {voice_summary}

{approved_section}

Crie um post para o Instagram do autor. Use a voz do autor fielmente. O post deve falar para agrônomos e profissionais de vendas no agro.

Retorne JSON:
{{
  "hook": "<primeira linha que prende — máximo 1 frase impactante>",
  "caption": "<legenda completa com quebras de linha, máximo 300 palavras, sem hashtags>",
  "cta": "<call-to-action direto para a Confraria>"
}}
Responda APENAS com o JSON, sem markdown."""

_USER_PROMPT = """POST DO CONCORRENTE PARA INSPIRAÇÃO:
- Perfil: @{competitor_handle}
- Argumento central do card: {core_argument}
- Estrutura do argumento: {argument_structure}
- Template replicável: {replication_template}
- Afirmações técnicas com dados: {technical_claims}
- Score de viralidade: {virality_score:.0%}

ARGUMENTOS DE ALTO DESEMPENHO DO BANCO:
{top_arguments}

Adapte a estrutura e os dados acima para a voz e realidade do autor."""


def _build_approved_section(approved: List[GeneratedPost]) -> str:
    if not approved:
        return ""
    examples = "\n\n".join([
        f"Exemplo aprovado {i+1}:\nHook: {p.hook}\nLegenda: {(p.caption or '')[:400]}..."
        for i, p in enumerate(approved)
    ])
    return f"EXEMPLOS DE POSTS QUE O AUTOR APROVOU (replique o estilo):\n{examples}\n"


def generate_post(
    source_post: Post,
    voice: ProfileVoice,
    approved_examples: List[GeneratedPost],
    session: Session,
) -> GeneratedPost:
    intel = source_post.intelligence
    virality = source_post.analysis.virality_score or 0.0 if source_post.analysis else 0.0

    if not intel:
        raise ValueError(f"Post {source_post.id} não tem análise de inteligência. Execute a análise de posts primeiro.")

    top_args = (
        session.query(ArgumentBank)
        .filter(ArgumentBank.origin == "extracted")
        .order_by((ArgumentBank.virality_weight * ArgumentBank.quality_score).desc())
        .limit(5)
        .all()
    )
    top_arg_texts = "\n".join(f"• {a.text}" for a in top_args) if top_args else "—"

    technical_claims_text = json.dumps(intel.technical_claims or [], ensure_ascii=False)

    system_prompt = _SYSTEM_PROMPT.format(
        confraria_context=CONFRARIA_CONTEXT,
        tone=voice.tone or "direto, técnico, próximo do produtor",
        dominant_themes=", ".join(voice.dominant_themes) if voice.dominant_themes else "—",
        vocabulary=json.dumps(voice.vocabulary, ensure_ascii=False),
        voice_summary=voice.voice_summary or "—",
        approved_section=_build_approved_section(approved_examples),
    )

    user_prompt = _USER_PROMPT.format(
        competitor_handle=source_post.profile.handle,
        core_argument=intel.core_argument or "—",
        argument_structure=intel.argument_structure or "—",
        replication_template=intel.replication_template or "—",
        technical_claims=technical_claims_text,
        virality_score=virality,
        top_arguments=top_arg_texts,
    )

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=800,
    )

    content = response.choices[0].message.content or ""
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```", 2)[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.rstrip("`").strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.error("GPT-4o returned invalid JSON for content generation: %s — raw: %r", exc, content)
        raise

    generated = GeneratedPost(
        source_post_id=source_post.id,
        hook=result.get("hook"),
        caption=result.get("caption"),
        cta=result.get("cta"),
        status="generated",
        created_at=datetime.now(timezone.utc),
    )
    session.add(generated)
    session.commit()
    logger.info("Generated post from source post %s", source_post.id)
    return generated
