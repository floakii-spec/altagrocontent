import json
import logging
from datetime import datetime, timezone
from typing import List
from openai import OpenAI
from sqlalchemy.orm import Session
from src.config import OPENAI_API_KEY
from src.models import Post, ProfileVoice, GeneratedPost

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

CONFRARIA_CONTEXT = """
SOBRE O AUTOR:
- Engenheiro Agrônomo com 15+ anos em vendas, varejo e cooperativismo no agronegócio brasileiro
- Fundador da Confraria de Vendas no Agro: comunidade para quem quer dominar o comercial no campo
- A Confraria inclui: curso Agroroot completo + encontros ao vivo quinzenais com especialistas do agro
- Público-alvo: agrônomos, consultores e profissionais de vendas no agro que querem crescer na carreira comercial
"""

GENERATION_PROMPT = """Você é um ghostwriter especializado em conteúdo para Instagram no agronegócio brasileiro.

{confraria_context}

ESTILO DE VOZ DO AUTOR:
{voice_summary}

{approved_section}

POST DO CONCORRENTE PARA INSPIRAÇÃO:
- Perfil: @{competitor_handle}
- Hook original: {hook}
- Mensagem central: {main_message}
- Dor abordada: {problem_addressed}
- Estrutura narrativa: {narrative_structure}
- Gatilho usado: {trigger}
- CTA original: {call_to_action}
- Score de viralidade: {virality_score:.0%}

Crie um post para o Instagram do autor adaptando a estrutura e abordagem acima para a sua voz e realidade. Use a voz do autor fielmente. O post deve falar para agrônomos e profissionais de vendas no agro.

Retorne JSON:
{{
  "hook": "<primeira linha que prende — máximo 1 frase impactante>",
  "caption": "<legenda completa com quebras de linha, máximo 300 palavras, sem hashtags>",
  "cta": "<call-to-action direto para a Confraria>"
}}
Responda APENAS com o JSON, sem markdown."""


def _build_approved_section(approved: List[GeneratedPost]) -> str:
    if not approved:
        return ""
    examples = "\n\n".join([
        f"Exemplo aprovado {i+1}:\nHook: {p.hook}\nLegenda: {p.caption[:200]}..."
        for i, p in enumerate(approved)
    ])
    return f"EXEMPLOS DE POSTS QUE O AUTOR APROVOU (replique o estilo):\n{examples}\n"


def generate_post(
    source_post: Post,
    voice: ProfileVoice,
    approved_examples: List[GeneratedPost],
    session: Session,
) -> GeneratedPost:
    """
    Gera um post adaptado com base no post do concorrente, voz do autor e exemplos aprovados.
    """
    raw_analysis = source_post.analysis.raw_analysis if source_post.analysis else {}
    virality = source_post.analysis.virality_score or 0.0 if source_post.analysis else 0.0

    prompt = GENERATION_PROMPT.format(
        confraria_context=CONFRARIA_CONTEXT,
        voice_summary=voice.voice_summary or "Tom direto, experiente, próximo do produtor rural.",
        approved_section=_build_approved_section(approved_examples),
        competitor_handle=source_post.profile.handle,
        hook=raw_analysis.get("hook", "—"),
        main_message=raw_analysis.get("main_message", "—"),
        problem_addressed=raw_analysis.get("problem_addressed", "—"),
        narrative_structure=raw_analysis.get("narrative_structure", "—"),
        trigger=raw_analysis.get("trigger", source_post.analysis.trigger if source_post.analysis else "—"),
        call_to_action=raw_analysis.get("call_to_action", "—"),
        virality_score=virality,
    )

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
    )

    content = response.choices[0].message.content or ""
    content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
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
