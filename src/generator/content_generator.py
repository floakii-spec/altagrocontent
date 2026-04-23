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
from src.carousel_quality import (
    CarouselEvidencePack,
    build_slide_blueprint,
    estimate_target_slide_count,
    format_quality_feedback,
    score_carousel_draft,
)
from src.generator.obsidian_context import load_studio_context
from src.generator.creative_intelligence import build_source_creative_brief
from src.slide_utils import extract_carousel_cta, extract_carousel_hook, normalize_carousel_slides

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
- Entregue o conteúdo obrigatoriamente em formato de carrossel, nunca em formato de feed solto.
- A legenda de apoio deve ter 4 a 6 parágrafos curtos, entre 140 e 320 palavras.
- O hook precisa ser específico e forte, sem parecer frase pronta de internet.
- O CTA deve encaixar no estágio do funil escolhido e, em fundo de funil, apontar diretamente para a Confraria.
- Estrutura obrigatória dos slides:
  1. `CAPA` — promessa central ou tese principal
  2. `HOOK` — provocação, dado ou tensão que faz a pessoa continuar
  3. Slides intermediários `DESENVOLVIMENTO` — explicação, dado, implicação prática, objeção ou exemplo
  4. Penúltimo slide `PROVA` — caso real, comparação, evidência, fonte ou demonstração prática
  5. Último slide `CTA` — chamada para ação clara

Crie um carrossel para o Instagram do autor. Use a voz do autor fielmente. O post deve falar para agrônomos e profissionais de vendas no agro, com clareza, substância e contexto.

Retorne JSON:
{{
  "slides": [
    {{"slide_number": 1, "slide_type": "CAPA", "title": "<título curto e forte>", "copy": "<texto do slide>", "cta": ""}},
    {{"slide_number": 2, "slide_type": "HOOK", "title": "<gancho ou dado>", "copy": "<texto do slide>", "cta": ""}},
    {{"slide_number": N-1, "slide_type": "PROVA", "title": "<prova ou exemplo>", "copy": "<texto do slide>", "cta": ""}},
    {{"slide_number": N, "slide_type": "CTA", "title": "<fechamento>", "copy": "<texto do slide>", "cta": "<cta>"}} 
  ],
  "caption": "<legenda completa com quebras de linha, entre 140 e 320 palavras, sem hashtags>",
  "cta": "<call-to-action direto e coerente com o funil>",
  "funnel_stage": "<topo|meio|fundo>",
  "format": "carousel"
}}
- Entre 5 e 8 slides no total
- `format` deve ser sempre `carousel`
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
- Transcrição literal dos cards/slides: {visual_transcript}
- Legenda original: {source_caption}
- Hashtags originais: {hashtags}

REFERÊNCIAS OPCIONAIS DO BANCO DE ARGUMENTOS:
- Use apenas se houver encaixe real com este post.
- Não force reaproveitamento se a melhor linha de raciocínio nascer do próprio material-base.
{top_arguments}

EXEMPLOS ESTRUTURAIS DE POSTS FORTES DO BANCO:
{structural_patterns}

CATÁLOGO DE DADOS VALIDADOS QUE VOCÊ PODE USAR:
{validated_data_catalog}

INTELIGÊNCIA CRIATIVA AGRO:
{creative_brief}

BLUEPRINT RECOMENDADO DO CARROSSEL:
{slide_blueprint}

CHECKLIST DE QUALIDADE:
{quality_guardrails}

Adapte a estrutura e os dados acima para a voz e realidade do autor.
Saída obrigatória: texto denso, específico e útil. Use a transcrição literal dos cards como fonte primária para dados, sequência lógica e nuances do material-base.
Não resuma demais e não apague os dados do material-base.
Se um dado não estiver no catálogo validado, não use."""

_CAPTION_ISSUE_PREFIXES = (
    "faltou legenda",
    "legenda curta demais",
    "legenda fora da faixa ideal",
)

_BLOCKING_ISSUE_PREFIXES = (
    "faltou hook",
    "faltou cta",
    "faltaram slides",
    "carrossel curto demais",
    "o slide 1 precisa ser capa",
    "o slide 2 precisa ser hook",
    "o carrossel precisa ter espaco para desenvolvimento, prova e cta",
    "o penultimo slide precisa ser prova",
    "o ultimo slide precisa ser cta",
    "faltou legenda",
    "funil ausente ou invalido",
    "formato ausente ou invalido",
    "os dados numericos do post-base sumiram",
    "estrutura obrigatoria incompleta",
    "hook generico ou pouco especifico",
    "faltam slides de desenvolvimento",
    "cta ausente",
)

_FULL_REWRITE_ISSUE_PREFIXES = (
    "faltou hook",
    "faltou cta",
    "faltaram slides",
    "carrossel curto demais",
    "o slide 1 precisa ser capa",
    "o slide 2 precisa ser hook",
    "o carrossel precisa ter espaco para desenvolvimento, prova e cta",
    "o penultimo slide precisa ser prova",
    "o ultimo slide precisa ser cta",
    "funil ausente ou invalido",
    "formato ausente ou invalido",
    "estrutura obrigatoria incompleta",
)

_QUALITY_SCORE_THRESHOLD = 0.78
_MAX_GENERATION_ATTEMPTS = 4


def _build_approved_section(approved: List[GeneratedPost]) -> str:
    if not approved:
        return ""
    examples = "\n\n".join([
        (
            f"Exemplo aprovado {i+1}:\n"
            f"Hook: {p.hook}\n"
            f"Slides: {_format_json(normalize_carousel_slides(getattr(p, 'slides', []) or [])[:4])}\n"
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


def _trim_for_prompt(text: str | None, limit: int = 6000) -> str:
    value = (text or "").strip()
    if not value:
        return "—"
    if len(value) <= limit:
        return value
    return f"{value[:limit].rstrip()}\n...[transcrição truncada para caber no prompt]"


def _select_top_arguments(session: Session, source_post: Post) -> list[ArgumentBank]:
    intel = source_post.intelligence
    score_expr = ArgumentBank.virality_weight * ArgumentBank.quality_score
    filters = []
    if intel.agro_topic_cluster:
        filters.append(ArgumentBank.topic_cluster == intel.agro_topic_cluster)
    if intel.agro_segment:
        filters.append(ArgumentBank.agro_segment == intel.agro_segment)

    targeted: list[ArgumentBank] = []
    if filters:
        targeted = (
            session.query(ArgumentBank)
            .filter(ArgumentBank.origin == "extracted")
            .filter(or_(*filters))
            .order_by(score_expr.desc())
            .limit(5)
            .all()
        )
    return targeted


def _build_validated_data_catalog(source_post: Post, top_args: list[ArgumentBank]) -> dict[str, Any]:
    intel = source_post.intelligence
    data_points = []
    for point in intel.data_points or []:
        if not isinstance(point, dict):
            continue
        value = str(point.get("value", "")).strip()
        context = str(point.get("context", "")).strip()
        source = str(point.get("source", "")).strip()
        if not any([value, context, source]):
            continue
        data_points.append(
            {
                "value": value,
                "context": context,
                "source": source or None,
            }
        )

    technical_claims = [claim for claim in intel.technical_claims or [] if isinstance(claim, str) and claim.strip()]
    source_labels = [str(source).strip() for source in intel.sources_referenced or [] if str(source).strip()]
    optional_bank_references = [arg.text for arg in top_args if arg.text.strip()]

    return {
        "numeros_obrigatoriamente_ancorados_no_material_base": _extract_numeric_fragments(intel),
        "dados_estruturados": data_points,
        "afirmacoes_tecnicas_permitidas": technical_claims,
        "fontes_disponiveis": source_labels,
        "argumento_central": intel.core_argument or "",
        "transcricao_literal_dos_cards": _trim_for_prompt(getattr(intel, "visual_transcript", None), limit=4000),
        "referencias_opcionais_do_banco": optional_bank_references,
        "instrucao": "Nao invente dado fora deste catalogo. Quando usar numero, deixe claro o que ele mede.",
    }


def _load_structural_patterns(source_post: Post, top_args: list[ArgumentBank]) -> list[dict[str, Any]]:
    intel = source_post.intelligence

    patterns = [{
        "core_argument": intel.core_argument or "—",
        "argument_structure": intel.argument_structure or "—",
        "replication_template": intel.replication_template or "—",
        "technical_depth": intel.technical_depth or "—",
        "slide_breakdown": getattr(intel, "slide_breakdown", []) or [],
        "carousel_complexity": getattr(intel, "carousel_complexity", {}) or {},
        "visual_transcript": _trim_for_prompt(getattr(intel, "visual_transcript", None), limit=2500),
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


def _build_evidence_pack(
    source_post: Post,
    top_args: list[ArgumentBank],
    validated_data_catalog: dict[str, Any],
) -> CarouselEvidencePack:
    intel = source_post.intelligence
    allowed_claims = [intel.core_argument or ""] + [claim for claim in intel.technical_claims or [] if isinstance(claim, str)]
    allowed_claims.extend(arg.text for arg in top_args if arg.text.strip())
    return CarouselEvidencePack(
        numeric_fragments=tuple(validated_data_catalog.get("numeros_obrigatoriamente_ancorados_no_material_base") or []),
        source_labels=tuple(validated_data_catalog.get("fontes_disponiveis") or []),
        allowed_claims=tuple(claim for claim in allowed_claims if str(claim).strip()),
        required_terms=(),
    )


def _build_quality_guardrails() -> list[str]:
    return [
    "Cada slide precisa ter uma funcao unica e empurrar a leitura para o proximo card.",
    "Nos slides de desenvolvimento, traduza o dado em implicacao pratica para o agro.",
    "Cada carrossel precisa ter uma tensao criativa clara: erro caro, decisao dificil, contraste tecnico/comercial ou risco de margem.",
    "Use linguagem de situacao real do agro: campo, safra, talhao, revenda, carteira, produtor ou negociacao.",
    "O slide de PROVA precisa ancorar numero, comparativo, caso ou fonte do catalogo.",
    "O CTA final deve ter uma unica acao e combinar com o funil escolhido.",
    "Evite frase vazia, promessa de coach e generalidade sem criterio tecnico.",
    ]


def _normalize_generation_result(result: dict[str, Any]) -> dict[str, Any]:
    slides = normalize_carousel_slides(result.get("slides"))
    hook = (result.get("hook") or "").strip() or extract_carousel_hook(slides) or ""
    cta = (result.get("cta") or "").strip() or extract_carousel_cta(slides) or ""
    format_name = (result.get("format") or "").strip() or ("carousel" if slides else "")

    return {
        **result,
        "slides": slides,
        "hook": hook,
        "cta": cta,
        "format": format_name,
    }


def _evaluate_generation(
    result: dict[str, Any],
    source_post: Post,
    evidence_pack: CarouselEvidencePack,
    target_slide_count: int,
) -> dict[str, Any]:
    problems: list[str] = []
    normalized_result = _normalize_generation_result(result)
    slides = normalized_result["slides"]
    caption = (result.get("caption") or "").strip()
    hook = normalized_result["hook"]
    cta = normalized_result["cta"]
    funnel_stage = (result.get("funnel_stage") or "").strip()
    format_name = normalized_result["format"]

    if not hook:
        problems.append("faltou hook")
    if not cta:
        problems.append("faltou CTA")
    if not slides:
        problems.append("faltaram slides")
    else:
        if len(slides) < 5:
            problems.append(f"carrossel curto demais ({len(slides)} slides)")
        if slides[0]["slide_type"] != "CAPA":
            problems.append("o slide 1 precisa ser CAPA")
        if len(slides) < 2 or slides[1]["slide_type"] != "HOOK":
            problems.append("o slide 2 precisa ser HOOK")
        if len(slides) < 5:
            problems.append("o carrossel precisa ter espaco para desenvolvimento, prova e CTA")
        elif slides[-2]["slide_type"] != "PROVA":
            problems.append("o penultimo slide precisa ser PROVA")
        if slides[-1]["slide_type"] != "CTA":
            problems.append("o ultimo slide precisa ser CTA")
    if not caption:
        problems.append("faltou legenda")
    else:
        words = len(caption.split())
        if words < 140:
            problems.append(f"legenda curta demais ({words} palavras)")

    if funnel_stage not in {"topo", "meio", "fundo"}:
        problems.append("funil ausente ou invalido")
    if format_name != "carousel":
        problems.append("formato ausente ou invalido")

    numeric_fragments = _extract_numeric_fragments(source_post.intelligence)
    combined_text = " ".join(
        [hook, caption, cta] +
        [slide["title"] for slide in slides] +
        [slide["copy"] for slide in slides]
    )
    if numeric_fragments and not any(fragment in combined_text for fragment in numeric_fragments):
        problems.append("os dados numericos do post-base sumiram")

    quality_report = score_carousel_draft(
        slides=slides,
        caption=caption,
        cta=cta,
        funnel_stage=funnel_stage,
        evidence_pack=evidence_pack,
        target_slide_count=target_slide_count,
        min_caption_words=140,
        max_caption_words=320,
    )
    for issue in quality_report["issues"]:
        if issue not in problems:
            problems.append(issue)

    return {
        "normalized_result": normalized_result,
        "problems": problems,
        "quality_report": quality_report,
    }


def _is_caption_issue(issue: str) -> bool:
    normalized = str(issue or "").strip().lower()
    return any(normalized.startswith(prefix) for prefix in _CAPTION_ISSUE_PREFIXES)


def _should_attempt_caption_repair(evaluation: dict[str, Any]) -> bool:
    normalized_result = evaluation["normalized_result"]
    if not normalized_result.get("slides") or normalized_result.get("format") != "carousel":
        return False

    combined_issues = list(
        dict.fromkeys(
            [
                *(evaluation.get("problems") or []),
                *(((evaluation.get("quality_report") or {}).get("issues")) or []),
            ]
        )
    )
    if not combined_issues:
        return False
    return all(_is_caption_issue(issue) for issue in combined_issues)


def _combine_issues(evaluation: dict[str, Any]) -> list[str]:
    return list(
        dict.fromkeys(
            [
                *(evaluation.get("problems") or []),
                *(((evaluation.get("quality_report") or {}).get("issues")) or []),
            ]
        )
    )


def _passes_quality_gate(evaluation: dict[str, Any]) -> bool:
    return not evaluation["problems"] and (evaluation["quality_report"]["score"] >= _QUALITY_SCORE_THRESHOLD)


def _starts_with_any(issue: str, prefixes: tuple[str, ...]) -> bool:
    normalized = str(issue or "").strip().lower()
    return any(normalized.startswith(prefix) for prefix in prefixes)


def _has_blocking_issues(evaluation: dict[str, Any]) -> bool:
    return any(_starts_with_any(issue, _BLOCKING_ISSUE_PREFIXES) for issue in _combine_issues(evaluation))


def _needs_full_rewrite(evaluation: dict[str, Any]) -> bool:
    return any(_starts_with_any(issue, _FULL_REWRITE_ISSUE_PREFIXES) for issue in _combine_issues(evaluation))


def _is_usable_best_effort(evaluation: dict[str, Any]) -> bool:
    normalized_result = evaluation["normalized_result"]
    slides = normalized_result.get("slides") or []
    caption = str(normalized_result.get("caption") or "").strip()
    hook = str(normalized_result.get("hook") or "").strip()
    cta = str(normalized_result.get("cta") or "").strip()

    if normalized_result.get("format") != "carousel":
        return False
    if not slides or len(slides) < 5:
        return False
    if not hook or not cta or not caption:
        return False
    if _has_blocking_issues(evaluation):
        return False
    return True


def _evaluation_sort_key(evaluation: dict[str, Any]) -> tuple[int, int, float, int]:
    return (
        1 if _is_usable_best_effort(evaluation) else 0,
        0 if _has_blocking_issues(evaluation) else 1,
        float((evaluation.get("quality_report") or {}).get("score") or 0.0),
        -len(_combine_issues(evaluation)),
    )


def _pick_better_evaluation(current_best: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    if _evaluation_sort_key(candidate) > _evaluation_sort_key(current_best):
        return candidate
    return current_best


def _build_revision_directives(issues: list[str]) -> list[str]:
    normalized_issues = [str(issue or "").strip().lower() for issue in issues]
    directives: list[str] = []

    if any(_is_caption_issue(issue) for issue in issues):
        directives.append("Expanda a legenda para 150 a 240 palavras, em 4 a 6 paragrafos curtos, sem hashtags.")
    if any("implicacao pratica" in issue for issue in normalized_issues):
        directives.append("Em pelo menos metade do miolo, traduza o dado em impacto pratico para produtor, consultor, revenda ou vendedor.")
    if any("desenvolvimento superficiais" in issue for issue in normalized_issues):
        directives.append("Deixe cada slide de DESENVOLVIMENTO com mais densidade tecnica, evitando frases curtas demais ou genricas.")
    if any("hook generico" in issue for issue in normalized_issues):
        directives.append("Fortaleca o HOOK com numero, contraste, risco concreto ou pergunta especifica do agro.")
    if any("tensao criativa" in issue for issue in normalized_issues):
        directives.append("Construa uma tensao central clara: erro caro, decisao atrasada, risco de margem ou contraste entre achismo e criterio.")
    if any("poucos dados validados" in issue for issue in normalized_issues):
        directives.append("Reincorpore pelo menos dois dados validados do catalogo no texto final e deixe claro o que cada numero mede.")
    if any("slide de prova sem ancora tecnica forte" in issue for issue in normalized_issues):
        directives.append("Reescreva o slide de PROVA com numero, comparativo, caso ou fonte concreta do catalogo validado.")
    if any("slide de prova raso demais" in issue for issue in normalized_issues):
        directives.append("Aprofunde o slide de PROVA para mostrar evidencia aplicada, nao apenas uma frase conclusiva.")
    if any("faltou citar a fonte/origem" in issue for issue in normalized_issues):
        directives.append("Quando houver fonte disponivel no catalogo, cite a origem da evidencia no texto final.")
    if any("cta pouco alinhado" in issue for issue in normalized_issues):
        directives.append("Ajuste o CTA final para combinar melhor com o funil escolhido, mantendo uma unica acao clara.")

    if not directives:
        directives.append("Reforce substancia tecnica, retencao slide a slide e clareza pratica sem inventar dados.")
    return directives


def _build_refinement_prompt(
    base_user_prompt: str,
    evaluation: dict[str, Any],
    validated_data_catalog: dict[str, Any],
    *,
    attempt_number: int,
) -> str:
    issues = _combine_issues(evaluation)
    directives = _build_revision_directives(issues)
    quality_report = evaluation["quality_report"]
    normalized_result = evaluation["normalized_result"]
    preserve_mode = not _needs_full_rewrite(evaluation)
    revision_mode = (
        "Aproveite o rascunho atual como base. Preserve o que ja funciona e refine apenas o necessario."
        if preserve_mode else
        "O rascunho atual falhou em pontos estruturais. Reescreva o carrossel completo do zero."
    )
    return (
        f"{base_user_prompt}\n\n"
        f"TENTATIVA DE REVISAO: {attempt_number}\n\n"
        f"RASCUNHO ATUAL:\n{_format_json(normalized_result)}\n\n"
        f"DIAGNOSTICO DE QUALIDADE:\n{_format_json(quality_report)}\n\n"
        f"LEITURA HUMANA DO DIAGNOSTICO:\n{format_quality_feedback(quality_report)}\n\n"
        f"CATALOGO DE DADOS VALIDADOS:\n{_format_json(validated_data_catalog)}\n\n"
        "PROBLEMAS QUE PRECISAM SER CORRIGIDOS:\n"
        + "\n".join(f"- {issue}" for issue in issues)
        + "\n\n"
        "DIRETRIZES OBJETIVAS DE REVISAO:\n"
        + "\n".join(f"- {directive}" for directive in directives)
        + "\n\n"
        f"{revision_mode}\n"
        "Use o quality gate como feedback de refinamento, nao como motivo para resumir ou amputar o carrossel.\n"
        "Retorne o JSON completo no mesmo formato original."
    )


def _parse_json_response(raw_content: str) -> dict[str, Any]:
    content = (raw_content or "").replace("\ufeff", "").strip()
    if content.startswith("```"):
        content = content.split("```", 2)[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.rstrip("`").strip()
    if not content:
        raise json.JSONDecodeError("Empty content", raw_content or "", 0)

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        start_positions = [idx for idx, char in enumerate(content) if char in "{["]
        for start in start_positions:
            try:
                parsed, _ = decoder.raw_decode(content[start:])
                break
            except json.JSONDecodeError:
                continue
        else:
            raise

    if not isinstance(parsed, dict):
        raise json.JSONDecodeError("Expected a JSON object", content, 0)
    return parsed


def _request_generation(
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 1500,
    max_parse_attempts: int = 3,
) -> dict[str, Any]:
    current_prompt = user_prompt
    last_error: json.JSONDecodeError | None = None

    for attempt in range(1, max_parse_attempts + 1):
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": current_prompt},
            ],
            max_tokens=max_tokens,
        )
        raw_content = response.choices[0].message.content or ""
        try:
            return _parse_json_response(raw_content)
        except json.JSONDecodeError as exc:
            last_error = exc
            logger.warning(
                "Invalid JSON from content generation on parse attempt %s/%s: %s | raw=%r",
                attempt,
                max_parse_attempts,
                exc,
                raw_content[:500],
            )
            if attempt >= max_parse_attempts:
                break
            current_prompt = (
                f"{user_prompt}\n\n"
                "A resposta anterior veio vazia ou em JSON invalido.\n"
                f"RESPOSTA ANTERIOR:\n{raw_content[:1200] or '<vazia>'}\n\n"
                "Reenvie a resposta do zero.\n"
                "Retorne APENAS um JSON valido, sem markdown, sem explicacao, sem texto antes ou depois."
            )

    raise ValueError(
        "O modelo retornou uma resposta vazia ou invalida ao gerar o carrossel do Studio. Tente novamente."
    ) from last_error


def _repair_caption(
    system_prompt: str,
    base_user_prompt: str,
    evaluation: dict[str, Any],
    validated_data_catalog: dict[str, Any],
) -> dict[str, Any]:
    normalized_result = evaluation["normalized_result"]
    quality_report = evaluation["quality_report"]
    repair_prompt = (
        f"{base_user_prompt}\n\n"
        "O carrossel abaixo ja esta estruturalmente aprovado. Nao mexa nos slides, no hook, no CTA, no funil nem no formato.\n"
        "Corrija somente a legenda.\n\n"
        f"RASCUNHO ATUAL:\n{_format_json(normalized_result)}\n\n"
        f"DIAGNOSTICO DE QUALIDADE:\n{_format_json(quality_report)}\n\n"
        f"LEITURA HUMANA DO DIAGNOSTICO:\n{format_quality_feedback(quality_report)}\n\n"
        f"CATALOGO DE DADOS VALIDADOS:\n{_format_json(validated_data_catalog)}\n\n"
        "REESCREVA SOMENTE O CAMPO `caption` obedecendo exatamente estas regras:\n"
        "- entre 150 e 240 palavras\n"
        "- 4 a 6 paragrafos curtos com quebras de linha\n"
        "- reaproveite os mesmos dados validados e a mesma linha tecnica do rascunho\n"
        "- deixe explicita a implicacao pratica para quem vende no agro\n"
        "- mantenha coerencia com o CTA ja existente\n"
        "- sem hashtags\n\n"
        'Retorne APENAS JSON no formato {"caption": "<nova legenda>"}'
    )
    repaired = _request_generation(system_prompt, repair_prompt, max_tokens=900)
    return {
        **normalized_result,
        "caption": (repaired.get("caption") or "").strip(),
    }


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
    validated_data_catalog = _build_validated_data_catalog(source_post, top_args)
    target_slide_count = estimate_target_slide_count(
        intel.technical_depth,
        getattr(intel, "carousel_complexity", {}).get("complexity_score"),
        minimum=6,
    )
    slide_blueprint = build_slide_blueprint(target_slide_count)
    quality_guardrails = _build_quality_guardrails()
    evidence_pack = _build_evidence_pack(source_post, top_args, validated_data_catalog)
    creative_brief = build_source_creative_brief(source_post, top_args, validated_data_catalog)
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
        visual_transcript=_trim_for_prompt(getattr(intel, "visual_transcript", None)),
        source_caption=(source_post.caption or "—")[:1200],
        hashtags=_format_json(source_post.hashtags or []),
        virality_score=virality,
        top_arguments=top_arg_texts,
        structural_patterns=_format_json(_load_structural_patterns(source_post, top_args[:3])),
        validated_data_catalog=_format_json(validated_data_catalog),
        creative_brief=_format_json(creative_brief),
        slide_blueprint=_format_json(slide_blueprint),
        quality_guardrails="\n".join(f"- {item}" for item in quality_guardrails),
    )

    try:
        result = _request_generation(system_prompt, user_prompt)
    except json.JSONDecodeError as exc:
        logger.error("GPT-4o returned invalid JSON for content generation: %s", exc)
        raise

    evaluation = _evaluate_generation(result, source_post, evidence_pack, target_slide_count)
    best_evaluation = evaluation
    attempt_number = 1

    while not _passes_quality_gate(evaluation) and attempt_number < _MAX_GENERATION_ATTEMPTS:
        issues = _combine_issues(evaluation)
        logger.warning(
            "Generated content for post %s failed quality gate on attempt %s: %s",
            source_post.id,
            attempt_number,
            "; ".join(issues) if issues else format_quality_feedback(evaluation["quality_report"]),
        )
        if _should_attempt_caption_repair(evaluation):
            revised_result = _repair_caption(system_prompt, user_prompt, evaluation, validated_data_catalog)
        else:
            refinement_prompt = _build_refinement_prompt(
                user_prompt,
                evaluation,
                validated_data_catalog,
                attempt_number=attempt_number + 1,
            )
            revised_result = _request_generation(system_prompt, refinement_prompt)

        evaluation = _evaluate_generation(revised_result, source_post, evidence_pack, target_slide_count)
        best_evaluation = _pick_better_evaluation(best_evaluation, evaluation)
        attempt_number += 1

    if not _passes_quality_gate(evaluation):
        if _is_usable_best_effort(best_evaluation):
            evaluation = best_evaluation
            logger.warning(
                "Returning best-effort studio carousel for post %s after %s attempts. Remaining issues: %s",
                source_post.id,
                attempt_number,
                "; ".join(_combine_issues(evaluation)),
            )
        else:
            raise ValueError(
                "Geracao de carrossel do studio nao passou no quality gate apos refinamento: "
                + "; ".join(_combine_issues(best_evaluation))
            )

    normalized_result = evaluation["normalized_result"]
    generated = GeneratedPost(
        source_post_id=source_post.id,
        hook=normalized_result.get("hook"),
        caption=normalized_result.get("caption"),
        cta=normalized_result.get("cta"),
        status="generated",
        created_at=datetime.now(timezone.utc),
        funnel_stage=normalized_result.get("funnel_stage"),
        format=normalized_result.get("format"),
        slides=normalized_result.get("slides") or [],
    )
    session.add(generated)
    session.commit()
    logger.info("Generated post from source post %s", source_post.id)
    return generated
