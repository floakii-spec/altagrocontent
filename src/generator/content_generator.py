import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, List
from openai import OpenAI
from sqlalchemy import or_
from sqlalchemy.orm import Session
from src.config import OPENAI_API_KEY
from src.models import ArgumentBank, Post, ProfileVoice, GeneratedPost
from src.generator.obsidian_context import load_studio_context

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

CONFRARIA_CONTEXT = """SOBRE O AUTOR:
- Engenheiro Agrônomo com 15+ anos em vendas, varejo e cooperativismo no agronegócio brasileiro
- Fundador da Confraria de Vendas no Agro: comunidade para quem quer dominar o comercial no campo
- A Confraria inclui: curso Agroroot completo + encontros ao vivo quinzenais com especialistas do agro
- Público-alvo: agrônomos, consultores e profissionais de vendas no agro que querem crescer na carreira comercial"""

_SYSTEM_PROMPT = """Você é um ghostwriter sênior especializado em conteúdo para Instagram no agronegócio brasileiro.

{confraria_context}

PERFIL DE VOZ DO AUTOR:
- Tom: {tone}
- Temas dominantes: {dominant_themes}
- Vocabulário característico: {vocabulary}
- Resumo de voz: {voice_summary}

{approved_section}

CONTEXTO ESTRATÉGICO DO OBSIDIAN:
- Perfil do Nathan:
{perfil_nathan}

- Estratégia de conteúdo:
{estrategia_conteudo}

- Produto e conversão:
{confraria_note}

- Banco de pautas:
{pautas_note}

REGRAS INEGOCIÁVEIS:
- Escreva como alguém do agro brasileiro. Nunca use tom de coach, autoajuda ou texto genérico.
- Preserve os dados técnicos do material de origem. Se houver números, percentuais, fontes ou comparativos, eles devem aparecer no texto final.
- Não invente fatos, estatísticas, safras, preços ou fontes.
- Explique o impacto prático do dado para agrônomos, consultores, revendas ou vendedores do agro.
- Entregue densidade real: legenda com 4 a 6 parágrafos curtos, entre 180 e 380 palavras.
- O hook precisa ser específico e forte, sem parecer frase pronta de internet.
- O CTA deve encaixar no estágio do funil escolhido e, em fundo de funil, apontar diretamente para a Confraria.

Crie um post para o Instagram do autor. Use a voz do autor fielmente. O post deve falar para agrônomos e profissionais de vendas no agro, com clareza, substância e contexto.

Retorne JSON:
{{
  "hook": "<primeira linha que prende — máximo 1 frase impactante>",
  "caption": "<legenda completa com quebras de linha, entre 180 e 380 palavras, sem hashtags>",
  "cta": "<call-to-action direto e coerente com o funil>",
  "funnel_stage": "<topo|meio|fundo>",
  "format": "<feed|carousel>"
}}
Responda APENAS com o JSON, sem markdown."""

_USER_PROMPT = """POST DO CONCORRENTE PARA INSPIRAÇÃO:
- Perfil: @{competitor_handle}
- Tipo de post: {post_type}
- Publicado em: {published_at}
- Score de viralidade: {virality_score:.0%}
- Hook original: {source_hook}
- Mensagem principal: {main_message}
- Problema atacado: {problem_addressed}
- Solução apresentada: {solution_presented}
- Gatilho dominante: {trigger}
- Público principal dentro do agro: {target_within_agro}
- Pilar de conteúdo: {content_pillar}
- CTA original: {source_cta}
- Argumento central do card: {core_argument}
- Estrutura do argumento: {argument_structure}
- Template replicável: {replication_template}
- Profundidade técnica: {technical_depth}
- Cluster agro: {agro_topic_cluster}
- Segmento agro: {agro_segment}
- Afirmações técnicas com dados: {technical_claims}
- Pontos de dados exatos: {data_points}
- Fontes visíveis/referenciadas: {sources_referenced}
- Conhecimento prévio assumido: {knowledge_assumptions}
- Lacunas do conteúdo original: {content_gaps}
- Breakdown slide a slide: {slide_breakdown}
- Complexidade do carrossel: {carousel_complexity}
- Legenda original: {source_caption}
- Hashtags originais: {hashtags}

ARGUMENTOS DE ALTO DESEMPENHO DO BANCO:
{top_arguments}

EXEMPLOS ESTRUTURAIS DE POSTS FORTES DO BANCO:
{structural_patterns}

Adapte a estrutura e os dados acima para a voz e realidade do autor.
Saída obrigatória: texto denso, específico e útil. Não resuma demais e não apague os dados do material-base."""


def _build_approved_section(approved: List[GeneratedPost]) -> str:
    if not approved:
        return ""
    examples = "\n\n".join([
        (
            f"Exemplo aprovado {i+1}:\n"
            f"Hook: {p.hook}\n"
            f"Legenda: {(p.caption or '')[:500]}...\n"
            f"CTA: {p.cta or '—'}\n"
            f"Funil: {p.funnel_stage or '—'}\n"
            f"Formato: {p.format or '—'}"
        )
        for i, p in enumerate(approved)
    ])
    return f"EXEMPLOS DE POSTS QUE O AUTOR APROVOU (replique o estilo):\n{examples}\n"


def _format_note(text: str) -> str:
    return text if text.strip() else "Nota indisponível."


def _format_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _select_top_arguments(session: Session, source_post: Post) -> list[ArgumentBank]:
    intel = source_post.intelligence
    score_expr = ArgumentBank.virality_weight * ArgumentBank.quality_score
    filters = []
    if intel.agro_topic_cluster:
        filters.append(ArgumentBank.topic_cluster == intel.agro_topic_cluster)
    if intel.agro_segment:
        filters.append(ArgumentBank.agro_segment == intel.agro_segment)

    targeted = []
    if filters:
        targeted = (
            session.query(ArgumentBank)
            .filter(ArgumentBank.origin == "extracted")
            .filter(or_(*filters))
            .order_by(score_expr.desc())
            .limit(5)
            .all()
        )
    if targeted:
        return targeted

    return (
        session.query(ArgumentBank)
        .filter(ArgumentBank.origin == "extracted")
        .order_by(score_expr.desc())
        .limit(5)
        .all()
    )


def _load_structural_patterns(source_post: Post, top_args: list[ArgumentBank]) -> list[dict[str, Any]]:
    intel = source_post.intelligence

    patterns = [{
        "core_argument": intel.core_argument or "—",
        "argument_structure": intel.argument_structure or "—",
        "replication_template": intel.replication_template or "—",
        "technical_depth": intel.technical_depth or "—",
        "slide_breakdown": getattr(intel, "slide_breakdown", []) or [],
        "carousel_complexity": getattr(intel, "carousel_complexity", {}) or {},
    }]

    for arg in top_args:
        patterns.append({
            "argumento": arg.text,
            "quality_score": arg.quality_score,
            "virality_weight": arg.virality_weight,
            "times_seen": arg.times_seen,
        })

    return patterns


def _extract_numeric_fragments(intel: Any) -> list[str]:
    fragments: list[str] = []
    for data_point in intel.data_points or []:
        if isinstance(data_point, dict):
            value = str(data_point.get("value", "")).strip()
            if value:
                fragments.append(value)
    for claim in intel.technical_claims or []:
        if not isinstance(claim, str):
            continue
        fragments.extend(re.findall(r"\d+[.,]?\d*%?", claim))
    deduped: list[str] = []
    for fragment in fragments:
        if fragment and fragment not in deduped:
            deduped.append(fragment)
    return deduped


def _validate_generation(result: dict[str, Any], source_post: Post) -> list[str]:
    problems: list[str] = []
    caption = (result.get("caption") or "").strip()
    hook = (result.get("hook") or "").strip()
    cta = (result.get("cta") or "").strip()
    funnel_stage = (result.get("funnel_stage") or "").strip()
    format_name = (result.get("format") or "").strip()

    if not hook:
        problems.append("faltou hook")
    if not cta:
        problems.append("faltou CTA")
    if not caption:
        problems.append("faltou legenda")
    else:
        words = len(caption.split())
        if words < 180:
            problems.append(f"legenda curta demais ({words} palavras)")

    if funnel_stage not in {"topo", "meio", "fundo"}:
        problems.append("funil ausente ou invalido")
    if format_name not in {"feed", "carousel"}:
        problems.append("formato ausente ou invalido")

    numeric_fragments = _extract_numeric_fragments(source_post.intelligence)
    combined_text = " ".join([hook, caption, cta])
    if numeric_fragments and not any(fragment in combined_text for fragment in numeric_fragments):
        problems.append("os dados numericos do post-base sumiram")

    return problems


def _parse_json_response(raw_content: str) -> dict[str, Any]:
    content = (raw_content or "").strip()
    if content.startswith("```"):
        content = content.split("```", 2)[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.rstrip("`").strip()
    return json.loads(content)


def _request_generation(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1100,
    )
    return _parse_json_response(response.choices[0].message.content or "")


def generate_post(
    source_post: Post,
    voice: ProfileVoice,
    approved_examples: List[GeneratedPost],
    session: Session,
) -> GeneratedPost:
    intel = source_post.intelligence
    virality = source_post.analysis.virality_score or 0.0 if source_post.analysis else 0.0
    analysis = source_post.analysis.raw_analysis if source_post.analysis else {}

    if not intel:
        raise ValueError(f"Post {source_post.id} não tem análise de inteligência. Execute a análise de posts primeiro.")

    top_args = _select_top_arguments(session, source_post)
    top_arg_texts = (
        "\n".join(
            f"• {a.text} (score={a.quality_score:.2f}, viralidade={a.virality_weight:.2f}, repeticoes={a.times_seen})"
            for a in top_args
        )
        if top_args else "—"
    )
    vault_context = load_studio_context()

    system_prompt = _SYSTEM_PROMPT.format(
        confraria_context=CONFRARIA_CONTEXT,
        tone=voice.tone or "direto, técnico, próximo do produtor",
        dominant_themes=", ".join(voice.dominant_themes) if voice.dominant_themes else "—",
        vocabulary=_format_json(voice.vocabulary),
        voice_summary=voice.voice_summary or "—",
        approved_section=_build_approved_section(approved_examples),
        perfil_nathan=_format_note(vault_context.get("perfil_nathan", "")),
        estrategia_conteudo=_format_note(vault_context.get("estrategia_conteudo", "")),
        confraria_note=_format_note(vault_context.get("confraria", "")),
        pautas_note=_format_note(vault_context.get("pautas", "")),
    )

    user_prompt = _USER_PROMPT.format(
        competitor_handle=source_post.profile.handle,
        post_type=source_post.post_type or "—",
        published_at=source_post.published_at.isoformat() if source_post.published_at else "—",
        source_hook=analysis.get("hook", "—"),
        main_message=analysis.get("main_message", "—"),
        problem_addressed=analysis.get("problem_addressed", "—"),
        solution_presented=analysis.get("solution_presented", "—"),
        trigger=analysis.get("trigger", source_post.analysis.trigger if source_post.analysis else "—"),
        target_within_agro=analysis.get("target_within_agro", "—"),
        content_pillar=analysis.get("content_pillar", "—"),
        source_cta=analysis.get("call_to_action", "—"),
        core_argument=intel.core_argument or "—",
        argument_structure=intel.argument_structure or "—",
        replication_template=intel.replication_template or "—",
        technical_depth=intel.technical_depth or "—",
        agro_topic_cluster=intel.agro_topic_cluster or "—",
        agro_segment=intel.agro_segment or "—",
        technical_claims=_format_json(intel.technical_claims or []),
        data_points=_format_json(intel.data_points or []),
        sources_referenced=_format_json(intel.sources_referenced or []),
        knowledge_assumptions=intel.knowledge_assumptions or "—",
        content_gaps=intel.content_gaps or "—",
        slide_breakdown=_format_json(getattr(intel, "slide_breakdown", []) or []),
        carousel_complexity=_format_json(getattr(intel, "carousel_complexity", {}) or {}),
        source_caption=(source_post.caption or "—")[:1200],
        hashtags=_format_json(source_post.hashtags or []),
        virality_score=virality,
        top_arguments=top_arg_texts,
        structural_patterns=_format_json(_load_structural_patterns(source_post, top_args[:3])),
    )

    try:
        result = _request_generation(system_prompt, user_prompt)
    except json.JSONDecodeError as exc:
        logger.error("GPT-4o returned invalid JSON for content generation: %s", exc)
        raise

    problems = _validate_generation(result, source_post)
    if problems:
        logger.warning("Generated content for post %s failed validation: %s", source_post.id, "; ".join(problems))
        retry_prompt = (
            f"{user_prompt}\n\n"
            f"O rascunho anterior falhou nestes pontos: {', '.join(problems)}.\n"
            "Reescreva do zero, preservando os dados do post-base e aumentando a densidade do conteúdo."
        )
        result = _request_generation(system_prompt, retry_prompt)

    generated = GeneratedPost(
        source_post_id=source_post.id,
        hook=result.get("hook"),
        caption=result.get("caption"),
        cta=result.get("cta"),
        status="generated",
        created_at=datetime.now(timezone.utc),
        funnel_stage=result.get("funnel_stage"),
        format=result.get("format"),
    )
    session.add(generated)
    session.commit()
    logger.info("Generated post from source post %s", source_post.id)
    return generated
