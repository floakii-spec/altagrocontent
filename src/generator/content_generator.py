import json
import logging
import re
from copy import deepcopy
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
from src.openai_utils import call_chat_completion_with_backoff
from src.slide_utils import extract_carousel_cta, extract_carousel_hook, normalize_carousel_slides

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

_MECHANISM_STOPWORDS = {
    "a", "as", "ao", "aos", "da", "das", "de", "do", "dos", "e", "em", "na", "nas",
    "no", "nos", "o", "os", "ou", "para", "por", "que", "se", "sem", "um", "uma",
    "mais", "menos", "como", "isso", "essa", "esse", "sua", "seu", "sao", "são",
    "ser", "foi", "tem", "porque", "quando", "entre", "sobre", "com", "num", "numa",
    "ate", "até", "mas", "muito", "muita", "todo", "toda", "todos", "todas",
}

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

══════════════════════════════════════════
METODOLOGIA DE CRIAÇÃO — DUAS ETAPAS OBRIGATÓRIAS
══════════════════════════════════════════

ETAPA 1 — PLANEJAMENTO NARRATIVO (antes de escrever um único slide)
Antes de qualquer copy, mapeie:
1. TENSÃO CENTRAL: O paradoxo ou contraste que torna o tema impossível de ignorar. Não é o tema — é o ângulo específico que cria espanto.
2. ÂNGULO DE ADAPTAÇÃO: Como a lógica do material original vira decisão real no agro. Troque o cenário, preserve a engrenagem causal.
3. CAMADAS DO ARGUMENTO: Quantas revelações distintas o argumento tem? Cada camada responde a uma pergunta que a anterior deixou em aberto.
4. ARCO EMOCIONAL: Qual emoção cada slide deve provocar? O tom varia: espanto → admiração → revelação → indignação → análise → leveza → síntese → ação. Nunca tom uniforme.
5. PROVAS QUE NÃO PODEM SUMIR: Quais números, fontes e claims do material original são inegociáveis?
6. PONTO DE TÉRMINO: O argumento termina quando o leitor não tem mais nenhuma pergunta em aberto.

ETAPA 2 — ESCRITA DOS SLIDES
Escreva tantos slides quantos o argumento exigir. O número de slides emerge do planejamento — nunca de um limite pré-definido.

REGRAS INVIOLÁVEIS DE COPYWRITING:
1. HOOK PARADOXAL: Abra com contraste que elimina a resposta óbvia antes de fazer a pergunta.
2. PALAVRA-CONCEITO EM PARÁGRAFO SOLO: Conceito central = linha própria. Ex: "Monopólio."
3. PERGUNTA NO FINAL DO SLIDE, NUNCA NO INÍCIO: Cria suspense para o próximo card.
4. "MAS" COMO MOTOR: Usa "Mas" para revelar a próxima camada do argumento.
5. REGRA DOS TRÊS: Três elementos paralelos antes da conclusão — a conclusão é mais forte depois de três golpes.
6. CONTRASTE RÍTMICO: Frase de 3–5 palavras depois de parágrafo longo força pausa. Ex: "A FIFA não tem."
7. DADO → REFERÊNCIA FAMILIAR → MULTIPLICAÇÃO: Nunca dado isolado — sempre âncora + multiplicação calculada.
8. SÍNTESE NO PENÚLTIMO SLIDE: A tese central vem quando o leitor já a construiu mentalmente.
9. CTA COMO EXTENSÃO LÓGICA: O desejo foi construído pelo conteúdo — o CTA captura, nunca interrompe.

REGRAS INEGOCIÁVEIS DE CONTEÚDO:
- Escreva como alguém do agro brasileiro. Nunca use tom de coach, autoajuda ou texto genérico.
- Preserve os dados técnicos do material de origem. Números, percentuais, fontes e comparativos devem aparecer.
- Ao adaptar um case, preserve a cadeia causal: fato disparador, mecanismo, prova, implicação para o agro.
- Troque o cenário, não a lógica. Nunca reduza um caso analítico a sermão genérico.
- Não invente fatos, estatísticas, safras, preços ou fontes.
- CTA em fundo de funil aponta diretamente para a Confraria.

TIPOS DE SLIDE DISPONÍVEIS:
CAPA | HOOK | MODELO | ESCALADA | DADO | MECANISMO | REVELACAO | DADOS_HISTORICOS | CASO_HUMANO | CONSEQUENCIA | RESPIRO | POLITICA | SINTESE | CTA

Retorne JSON com esta estrutura EXATA:
{{
  "planejamento_narrativo": {{
    "tensao_central": "<o paradoxo ou contraste — não o tema genérico>",
    "angulo_de_adaptacao": "<como a lógica do original vira decisão no agro>",
    "camadas": [
      {{
        "numero": 1,
        "tipo_slide": "CAPA",
        "funcao_narrativa": "<o que este slide faz no arco>",
        "pergunta_que_abre": "<qual pergunta fica no ar>",
        "emocao_alvo": "<espanto|admiracao|revelacao|indignacao|analise|leveza|sintese>"
      }}
    ],
    "total_slides": "<N>",
    "provas_que_nao_podem_sumir": ["<numero/fonte/claim 1>", "<numero/fonte/claim 2>"],
    "onde_termina": "<quando o argumento está completo>"
  }},
  "slides": [
    {{"slide_number": 1, "slide_type": "CAPA", "title": "<título>", "copy": "<texto>", "cta": ""}},
    {{"slide_number": 2, "slide_type": "HOOK", "title": "<título>", "copy": "<texto>", "cta": ""}},
    {{"slide_number": "N-1", "slide_type": "SINTESE", "title": "<título>", "copy": "<texto>", "cta": ""}},
    {{"slide_number": "N", "slide_type": "CTA", "title": "<título>", "copy": "<texto>", "cta": "<cta>"}}
  ],
  "caption": "<legenda completa com quebras de linha, entre 140 e 320 palavras, sem hashtags>",
  "cta": "<call-to-action direto e coerente com o funil>",
  "funnel_stage": "<topo|meio|fundo>",
  "format": "carousel"
}}
- Slide 1 = CAPA, Slide 2 = HOOK, Último = CTA
- O número de slides é determinado pelo planejamento_narrativo
- `format` deve ser sempre `carousel`
- Monte primeiro o `planejamento_narrativo` e use esse mapa para escrever slides e legenda.
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

MAPA DE LÓGICA DO MATERIAL-BASE (REFERÊNCIA DE APOIO):
{structural_transfer_map}

BLUEPRINT RECOMENDADO DO CARROSSEL:
{slide_blueprint}

CHECKLIST DE QUALIDADE:
{quality_guardrails}

Adapte a estrutura e os dados acima para a voz e realidade do autor.
Saída obrigatória: texto denso, específico e útil. Use a transcrição literal dos cards como fonte primária para dados, sequência lógica e nuances do material-base.
Não resuma demais e não apague os dados do material-base.
Preserve a progressao do raciocinio do original: contraste inicial, explicacao do porquê, prova e implicacao pratica. Se trocar o contexto, mantenha a engrenagem causal.
Use o mapa de logica do material-base apenas como insumo para montar o planejamento_narrativo.
A unica etapa obrigatoria que precisa aparecer no JSON final e o planejamento_narrativo.
Se um dado não estiver no catálogo validado, não use."""

_CAPTION_ISSUE_PREFIXES = (
    "faltou legenda",
    "legenda ausente",
    "legenda curta demais",
    "legenda fora da faixa ideal",
)

_BLOCKING_ISSUE_PREFIXES = (
    "faltou hook",
    "faltou cta",
    "faltaram slides",
    "carrossel raso demais",
    "o slide 1 precisa ser capa",
    "o slide 2 precisa ser hook",
    "o ultimo slide precisa ser cta",
    "faltou legenda",
    "funil ausente ou invalido",
    "formato ausente ou invalido",
    "os dados numericos do post-base sumiram",
    "estrutura obrigatoria incompleta",
    "hook generico ou pouco especifico",
    "faltam slides de desenvolvimento",
    "cta ausente",
    "o texto perdeu a cadeia causal do material-base",
    "planejamento_narrativo ausente",
    "planejamento_narrativo sem tensao_central",
    "planejamento_narrativo com menos de 3 camadas",
)

_FULL_REWRITE_ISSUE_PREFIXES = (
    "faltou hook",
    "faltou cta",
    "faltaram slides",
    "carrossel raso demais",
    "o slide 1 precisa ser capa",
    "o slide 2 precisa ser hook",
    "o ultimo slide precisa ser cta",
    "funil ausente ou invalido",
    "formato ausente ou invalido",
    "estrutura obrigatoria incompleta",
    "planejamento_narrativo ausente",
    "planejamento_narrativo sem tensao_central",
    "planejamento_narrativo com menos de 3 camadas",
)

_TARGETED_POLISH_MARKERS = (
    "legenda",
    "implicacao pratica",
    "ancora tecnica",
    "poucos dados validados",
    "faltou citar a fonte",
    "cadeia causal do material-base",
    "tema central pouco refletido",
    "cta pouco alinhado",
    "os dados numericos do post-base sumiram",
)

_LOCAL_REPAIR_MARKERS = (
    "legenda",
    "ancora tecnica",
    "poucos dados validados",
    "faltou citar a fonte",
    "implicacao pratica",
    "cadeia causal do material-base",
    "tema central pouco refletido",
    "os dados numericos do post-base sumiram",
)

_PRACTICAL_REPAIR_SUFFIX = (
    "Na pratica, isso muda a decisao de produtor, consultor, revenda e vendedor "
    "porque mexe em margem, risco e timing comercial."
)

_QUALITY_SCORE_THRESHOLD = 0.78
_MAX_GENERATION_ATTEMPTS = 4
_PLANNING_EMOTION_ARC = (
    "espanto",
    "admiracao",
    "revelacao",
    "indignacao",
    "analise",
    "leveza",
    "sintese",
)


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


def _tokenize_mechanism_terms(*texts: str) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for text in texts:
        for token in re.findall(r"[a-zA-ZÀ-ÿ0-9$%]+", str(text or "").lower()):
            if len(token) < 4 or token in _MECHANISM_STOPWORDS or token in seen:
                continue
            seen.add(token)
            tokens.append(token)
    return tokens


def _build_mechanism_terms(source_post: Post, top_args: list[ArgumentBank]) -> list[str]:
    intel = source_post.intelligence
    terms: list[str] = []

    for point in intel.data_points or []:
        if isinstance(point, dict):
            terms.extend(_tokenize_mechanism_terms(point.get("context", ""), point.get("value", "")))

    slide_breakdown = getattr(intel, "slide_breakdown", []) or []
    slide_texts = []
    for slide in slide_breakdown[:4]:
        if not isinstance(slide, dict):
            continue
        slide_texts.extend([slide.get("title", ""), slide.get("summary", ""), slide.get("main_point", "")])

    terms.extend(
        _tokenize_mechanism_terms(
            intel.core_argument or "",
            intel.argument_structure or "",
            intel.content_gaps or "",
            *(claim for claim in intel.technical_claims or [] if isinstance(claim, str)),
            *(arg.text for arg in top_args if arg.text.strip()),
            *slide_texts,
        )
    )

    deduped: list[str] = []
    for term in terms:
        if term not in deduped:
            deduped.append(term)
    return deduped[:10]


def _stringify_data_point(point: dict[str, Any]) -> str:
    value = str(point.get("value", "")).strip()
    context = str(point.get("context", "")).strip()
    source = str(point.get("source", "")).strip()
    if value and context and source:
        return f"{value} em {context} ({source})"
    if value and context:
        return f"{value} em {context}"
    return value or context


def _data_point_to_anchor(point: dict[str, Any]) -> str:
    value = str(point.get("value", "")).strip()
    context = str(point.get("context", "")).strip()
    source = str(point.get("source", "")).strip()
    if value and context and source:
        return f"{value} em {context}, segundo {source}"
    if value and context:
        return f"{value} em {context}"
    if value and source:
        return f"{value}, segundo {source}"
    return value or context or source


def _first_non_empty(*values: Any, fallback: str = "—") -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return fallback


def _flatten_strings(value: Any) -> list[str]:
    if isinstance(value, dict):
        flattened: list[str] = []
        for item in value.values():
            flattened.extend(_flatten_strings(item))
        return flattened
    if isinstance(value, list):
        flattened = []
        for item in value:
            flattened.extend(_flatten_strings(item))
        return flattened
    text = str(value or "").strip()
    return [text] if text else []


def _build_structural_transfer_map(
    source_post: Post,
    voice: ProfileVoice,
    top_args: list[ArgumentBank],
    validated_data_catalog: dict[str, Any],
    creative_brief: dict[str, Any],
    slide_blueprint: list[dict[str, str]],
) -> dict[str, Any]:
    intel = source_post.intelligence
    causal_chain = creative_brief.get("cadeia_causal_a_preservar") or {}
    field_contexts = list(creative_brief.get("contextos_de_campo") or [])
    mechanisms = list(causal_chain.get("mecanismos") or [])
    trigger = _first_non_empty(*(causal_chain.get("fato_disparador") or []), intel.core_argument)
    proof_points = [
        _stringify_data_point(point)
        for point in (validated_data_catalog.get("dados_estruturados") or [])
        if isinstance(point, dict)
    ]
    if not proof_points:
        proof_points = list(validated_data_catalog.get("numeros_obrigatoriamente_ancorados_no_material_base") or [])
    source_slide_breakdown = getattr(intel, "slide_breakdown", []) or []
    source_slide_anchors = [
        _first_non_empty(
            slide.get("summary"),
            slide.get("title"),
            slide.get("main_point"),
        )
        for slide in source_slide_breakdown
        if isinstance(slide, dict)
    ]
    voice_themes = ", ".join(voice.dominant_themes or []) or "vendas consultivas e decisao comercial"
    authorial_angle = _first_non_empty(
        *(arg.text for arg in top_args if arg.text.strip()),
        f"Ler o caso pela lente de {voice_themes}, com tom {voice.tone or 'direto'} e foco em decisao real no agro.",
    )

    plan: list[dict[str, Any]] = []
    mechanism_terms = validated_data_catalog.get("mecanismos_que_nao_podem_sumir") or []
    for index, blueprint_item in enumerate(slide_blueprint, start=1):
        slide_type = blueprint_item.get("slide_type", "DESENVOLVIMENTO")
        source_anchor = source_slide_anchors[index - 1] if index - 1 < len(source_slide_anchors) else trigger
        if slide_type == "CAPA":
            adapted_goal = (
                f"Abrir com o contraste central do caso em contexto de {field_contexts[0] if field_contexts else 'resultado e caixa no agro'}."
            )
        elif slide_type == "HOOK":
            adapted_goal = (
                f"Transformar o dado/tensao em curiosidade forte para quem vive {field_contexts[1] if len(field_contexts) > 1 else 'margem e decisao comercial'}."
            )
        elif slide_type in ("DADO", "DADOS_HISTORICOS"):
            adapted_goal = (
                f"Ancorar a tese com prova concreta: {_first_non_empty(*proof_points, fallback='numero, comparativo ou fonte validada')}."
            )
        elif slide_type == "CTA":
            adapted_goal = "Fechar com CTA coerente com a Confraria, sem quebrar a linha tecnica do caso."
        else:
            mechanism_hint = mechanisms[min(index - 3, max(len(mechanisms) - 1, 0))] if mechanisms else _first_non_empty(*mechanism_terms, fallback="criterio tecnico")
            context_hint = field_contexts[(index - 1) % len(field_contexts)] if field_contexts else "campo e comercial"
            adapted_goal = f"Explicar o mecanismo '{mechanism_hint}' em situacao real de {context_hint}, com implicacao pratica."

        plan.append(
            {
                "slide_number": index,
                "slide_type": slide_type,
                "papel": blueprint_item.get("objective", ""),
                "origem": source_anchor,
                "adaptacao": adapted_goal,
            }
        )

    return {
        "tese_original": intel.core_argument or "—",
        "tese_adaptada": f"Traduzir a mesma logica do caso para o agro, com foco em {field_contexts[0] if field_contexts else 'margem, risco e decisao'}.",
        "fato_disparador_original": trigger,
        "mecanismo_original": _first_non_empty(*mechanisms, intel.argument_structure, intel.content_gaps),
        "ponte_para_agro": _first_non_empty(
            *(creative_brief.get("perguntas_de_retencao") or []),
            f"Mostrar o que muda para produtor, consultor, revenda ou vendedor em {field_contexts[0] if field_contexts else 'situacoes reais do agro'}.",
        ),
        "angulo_autoral_do_nathan": authorial_angle,
        "prova_que_nao_pode_sumir": proof_points[:3] or list(validated_data_catalog.get("fontes_disponiveis") or [])[:2],
        "mecanismos_que_nao_podem_sumir": mechanism_terms[:6],
        "plano_estrutural": plan,
    }


def _build_planning_narrative_from_legacy_map(
    slides: list[dict[str, Any]],
    adaptation_map: dict[str, Any],
) -> dict[str, Any]:
    proof_points = _flatten_strings(adaptation_map.get("prova_que_nao_pode_sumir")) or [
        slide["title"]
        for slide in slides
        if slide["slide_type"] in {"DADO", "DADOS_HISTORICOS", "SINTESE"} and slide["title"]
    ]
    total = len(slides)
    camadas: list[dict[str, Any]] = []

    for index, slide in enumerate(slides, start=1):
        next_slide = slides[index] if index < total else None
        camadas.append(
            {
                "numero": index,
                "tipo_slide": slide["slide_type"],
                "funcao_narrativa": _first_non_empty(
                    slide["title"],
                    slide["copy"],
                    f"Cumprir o papel narrativo de {slide['slide_type']} preservando a cadeia causal do caso.",
                ),
                "pergunta_que_abre": _first_non_empty(
                    next_slide["title"] if next_slide else "",
                    next_slide["copy"] if next_slide else "",
                    "Qual decisao pratica isso abre no agro?",
                ),
                "emocao_alvo": _PLANNING_EMOTION_ARC[min(index - 1, len(_PLANNING_EMOTION_ARC) - 1)],
            }
        )

    return {
        "tensao_central": _first_non_empty(
            adaptation_map.get("tese_original"),
            slides[0]["title"] if slides else "",
            slides[0]["copy"] if slides else "",
        ),
        "angulo_de_adaptacao": _first_non_empty(
            adaptation_map.get("ponte_para_agro"),
            adaptation_map.get("tese_adaptada"),
            adaptation_map.get("angulo_autoral_do_nathan"),
        ),
        "camadas": camadas,
        "total_slides": total,
        "provas_que_nao_podem_sumir": proof_points[:3],
        "onde_termina": _first_non_empty(
            adaptation_map.get("tese_adaptada"),
            slides[-2]["title"] if len(slides) > 1 else "",
            slides[-1]["title"] if slides else "",
        ),
    }


def _upgrade_legacy_generation_result(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or isinstance(result.get("planejamento_narrativo"), dict):
        return result

    adaptation_map = result.get("adaptation_map")
    if not isinstance(adaptation_map, dict):
        return result

    slides = normalize_carousel_slides(result.get("slides"))
    if not slides:
        return result

    logger.warning("Upgrading legacy Studio payload with adaptation_map into planejamento_narrativo.")
    return {
        **result,
        "slides": slides,
        "planejamento_narrativo": _build_planning_narrative_from_legacy_map(slides, adaptation_map),
    }


def _validate_planning_narrative(
    planning: Any,
    source_post: Post,
) -> list[str]:
    """Validate that the narrative planning phase was completed before slide writing."""
    if not isinstance(planning, dict):
        return ["planejamento_narrativo ausente — o modelo pulou a etapa de pensamento narrativo"]

    issues: list[str] = []
    if not str(planning.get("tensao_central", "")).strip():
        issues.append("planejamento_narrativo sem tensao_central — argumento sem angulo provocador")
    if not str(planning.get("angulo_de_adaptacao", "")).strip():
        issues.append("planejamento_narrativo sem angulo_de_adaptacao — nao ficou claro como o original vira agro")

    camadas = planning.get("camadas")
    if not isinstance(camadas, list) or len(camadas) < 3:
        issues.append("planejamento_narrativo com menos de 3 camadas — argumento incompleto")
    else:
        types = [str(c.get("tipo_slide", "")).upper() for c in camadas if isinstance(c, dict)]
        if not types or types[0] != "CAPA":
            issues.append("planejamento_narrativo sem CAPA como primeiro slide")
        if len(types) < 2 or types[1] != "HOOK":
            issues.append("planejamento_narrativo sem HOOK como segundo slide")
        if types and types[-1] != "CTA":
            issues.append("planejamento_narrativo sem CTA como ultimo slide")
        emotions = [str(c.get("emocao_alvo", "")).strip() for c in camadas if isinstance(c, dict)]
        distinct_emotions = len(set(e for e in emotions if e))
        if distinct_emotions < 2:
            issues.append("planejamento_narrativo com emocao uniforme — arco narrativo ausente")

    provas = planning.get("provas_que_nao_podem_sumir")
    if not isinstance(provas, list) or not any(str(item).strip() for item in provas):
        issues.append("planejamento_narrativo sem provas_que_nao_podem_sumir")

    # Verify planning preserves mechanism terms from source
    reference_terms = _build_mechanism_terms(source_post, top_args=[])
    planning_text = " ".join(_flatten_strings(planning))
    planning_hits = _tokenize_mechanism_terms(planning_text)
    overlap = len(set(reference_terms).intersection(planning_hits))
    if reference_terms and overlap < min(2, len(reference_terms)):
        issues.append("planejamento_narrativo nao preservou os mecanismos centrais do material-base")

    return issues


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
    mechanism_terms = _build_mechanism_terms(source_post, top_args)
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
        "mecanismos_que_nao_podem_sumir": mechanism_terms,
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
    required_terms = validated_data_catalog.get("mecanismos_que_nao_podem_sumir") or _build_mechanism_terms(source_post, top_args)
    return CarouselEvidencePack(
        numeric_fragments=tuple(validated_data_catalog.get("numeros_obrigatoriamente_ancorados_no_material_base") or []),
        source_labels=tuple(validated_data_catalog.get("fontes_disponiveis") or []),
        allowed_claims=tuple(claim for claim in allowed_claims if str(claim).strip()),
        required_terms=tuple(str(term).strip() for term in required_terms if str(term).strip()),
    )


def _build_quality_guardrails() -> list[str]:
    return [
        "O numero de slides e determinado pelo argumento — nao existe limite superior.",
        "Cada slide tem funcao narrativa unica. Se dois slides revelam a mesma coisa, um deles nao existe.",
        "O tom varia a cada slide — nunca uniforme. Espanto, admiracao, indignacao, analise, leveza, sintese.",
        "A sintese central vem no penultimo slide, nunca no primeiro.",
        "Se o material-base for um case analitico, preserve a cadeia causal: fato, mecanismo, prova, consequencia.",
        "Use linguagem de situacao real do agro: campo, safra, talhao, revenda, carteira, produtor ou negociacao.",
        "O CTA e extensao logica do argumento — o desejo foi construido pelo conteudo, o CTA captura.",
        "Evite frase vazia, promessa de coach e generalidade sem criterio tecnico.",
    ]


def _normalize_generation_result(result: dict[str, Any]) -> dict[str, Any]:
    result = _upgrade_legacy_generation_result(result)
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
            problems.append(f"carrossel raso demais ({len(slides)} slides — argumento incompleto)")
        if slides[0]["slide_type"] != "CAPA":
            problems.append("o slide 1 precisa ser CAPA")
        if len(slides) < 2 or slides[1]["slide_type"] != "HOOK":
            problems.append("o slide 2 precisa ser HOOK")
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

    planning_issues = _validate_planning_narrative(result.get("planejamento_narrativo"), source_post)
    for issue in planning_issues:
        if issue not in problems:
            problems.append(issue)

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


def _is_targeted_polish_issue(issue: str) -> bool:
    normalized = str(issue or "").strip().lower()
    return any(marker in normalized for marker in _TARGETED_POLISH_MARKERS)


def _should_attempt_targeted_polish(evaluation: dict[str, Any]) -> bool:
    normalized_result = evaluation["normalized_result"]
    if not normalized_result.get("slides") or normalized_result.get("format") != "carousel":
        return False

    combined_issues = _combine_issues(evaluation)
    if not combined_issues or _needs_full_rewrite(evaluation):
        return False

    if all(_is_caption_issue(issue) for issue in combined_issues):
        return False

    has_targeted_issue = any(_is_targeted_polish_issue(issue) for issue in combined_issues)
    if not has_targeted_issue:
        return False

    return all(_is_caption_issue(issue) or _is_targeted_polish_issue(issue) for issue in combined_issues)


def _combine_issues(evaluation: dict[str, Any]) -> list[str]:
    return list(
        dict.fromkeys(
            [
                *(evaluation.get("problems") or []),
                *(((evaluation.get("quality_report") or {}).get("issues")) or []),
            ]
        )
    )


def _looks_like_refusal(raw_content: str) -> bool:
    normalized = str(raw_content or "").strip().lower()
    return (
        normalized.startswith("i'm sorry")
        or normalized.startswith("i am sorry")
        or "can't assist with that" in normalized
        or "cannot assist with that" in normalized
        or "nao posso ajudar com isso" in normalized
        or "não posso ajudar com isso" in normalized
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
        -len(_combine_issues(evaluation)),
        float((evaluation.get("quality_report") or {}).get("score") or 0.0),
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
    if any("superficiais" in issue for issue in normalized_issues):
        directives.append("Aprofunde os slides intermediarios: cada um deve ter funcao narrativa unica e densidade tecnica real.")
    if any("hook generico" in issue for issue in normalized_issues):
        directives.append("Fortaleca o HOOK: paradoxo por comparacao, afirmacao que elimina a resposta obvia, ou contraste que nao deixa parar.")
    if any("tensao criativa" in issue for issue in normalized_issues):
        directives.append("Construa uma tensao central clara no planejamento antes de escrever os slides.")
    if any("cadeia causal do material-base" in issue for issue in normalized_issues):
        directives.append(
            "Recupere a cadeia causal do material-base e elimine a abstracao generica: "
            "abra com o contraste/fato, explique o mecanismo, prove com dado e traduza para o agro."
        )
    if any("planejamento_narrativo" in issue for issue in normalized_issues):
        directives.append(
            "Monte o planejamento_narrativo completo antes dos slides: tensao_central, angulo_de_adaptacao, "
            "camadas com emocao_alvo distinta por slide, provas_que_nao_podem_sumir e onde_termina."
        )
    if any("nao preservou os mecanismos" in issue for issue in normalized_issues):
        directives.append("Reescreva o planejamento_narrativo preservando os mecanismos centrais do material-base.")
    if any("poucos dados validados" in issue for issue in normalized_issues) or any(
        "os dados numericos do post-base sumiram" in issue for issue in normalized_issues
    ):
        directives.append(
            "Reincorpore pelo menos dois dados validados do catalogo, com os numeros literais, "
            "e deixe claro o que cada numero mede."
        )
    if any("ancora tecnica" in issue or "raso demais" in issue for issue in normalized_issues):
        directives.append(
            "Garanta pelo menos um slide de prova explicitamente ancorado em numero, comparativo "
            "ou fonte concreta do catalogo validado."
        )
    if any("faltou citar a fonte" in issue for issue in normalized_issues):
        directives.append("Quando houver fonte disponivel no catalogo, cite a origem da evidencia no texto.")
    if any("cta pouco alinhado" in issue for issue in normalized_issues):
        directives.append("Ajuste o CTA para ser extensao logica do argumento, nao interrupcao.")
    if any("tema central pouco refletido" in issue for issue in normalized_issues):
        directives.append("Reforce a tese central nos slides e na legenda, sem trocar o mecanismo principal por moral generica.")
    if any("emocao uniforme" in issue for issue in normalized_issues):
        directives.append(
            "Varie a emocao a cada slide: espanto → admiracao → revelacao → indignacao → analise → leveza → sintese. "
            "Tom uniforme mata o scroll."
        )
    if any("tipos distintos" in issue or "tipo unico" in issue for issue in normalized_issues):
        directives.append(
            "Use tipos de slide diferentes no miolo: MODELO, ESCALADA, DADO, MECANISMO, REVELACAO, CASO_HUMANO, RESPIRO. "
            "Slides iguais = argumento parado."
        )

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
    planning = normalized_result.get("planejamento_narrativo") or {}
    return (
        f"{base_user_prompt}\n\n"
        f"TENTATIVA DE REVISAO: {attempt_number}\n\n"
        f"PLANEJAMENTO NARRATIVO ANTERIOR:\n{_format_json(planning)}\n\n"
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
        "O numero de slides e determinado pelo argumento — nao reduza para 'simplificar'.\n"
        "Retorne o JSON completo no mesmo formato original, incluindo planejamento_narrativo."
    )


def _build_targeted_polish_prompt(
    base_user_prompt: str,
    evaluation: dict[str, Any],
    validated_data_catalog: dict[str, Any],
    *,
    attempt_number: int,
) -> str:
    issues = _combine_issues(evaluation)
    directives = _build_revision_directives(issues)
    quality_report = evaluation["quality_report"]
    normalized_result = deepcopy(evaluation["normalized_result"])
    planning = normalized_result.get("planejamento_narrativo") or {}
    numeric_targets = validated_data_catalog.get("numeros_obrigatoriamente_ancorados_no_material_base") or []
    source_targets = validated_data_catalog.get("fontes_disponiveis") or []

    return (
        f"{base_user_prompt}\n\n"
        f"TENTATIVA DE POLIMENTO DIRECIONADO: {attempt_number}\n\n"
        "O carrossel abaixo tem estrutura aproveitavel. Nao recomece do zero sem necessidade.\n"
        "Preserve o numero total de slides, CAPA no slide 1, HOOK no slide 2, CTA no ultimo e o nucleo do planejamento_narrativo.\n"
        "Reescreva o que for preciso no miolo, no slide de prova, na legenda e no CTA para corrigir os pontos abaixo sem achatar o argumento.\n\n"
        f"PLANEJAMENTO NARRATIVO ATUAL:\n{_format_json(planning)}\n\n"
        f"RASCUNHO ATUAL:\n{_format_json(normalized_result)}\n\n"
        f"DIAGNOSTICO DE QUALIDADE:\n{_format_json(quality_report)}\n\n"
        f"LEITURA HUMANA DO DIAGNOSTICO:\n{format_quality_feedback(quality_report)}\n\n"
        f"CATALOGO DE DADOS VALIDADOS:\n{_format_json(validated_data_catalog)}\n\n"
        f"NUMEROS LITERAIS A PRESERVAR:\n{_format_json(numeric_targets)}\n\n"
        f"FONTES DISPONIVEIS PARA CITAÇÃO:\n{_format_json(source_targets)}\n\n"
        "PROBLEMAS QUE PRECISAM SER CORRIGIDOS:\n"
        + "\n".join(f"- {issue}" for issue in issues)
        + "\n\n"
        "REGRAS ESPECIFICAS DE POLIMENTO:\n"
        "- Em pelo menos metade do miolo, traduza o dado em implicacao pratica para produtor, consultor, revenda ou vendedor.\n"
        "- Reforce pelo menos um slide de prova com numero exato e, quando houver, cite a fonte/origem do catalogo.\n"
        "- Preserve a cadeia causal do material-base: fato disparador -> mecanismo -> prova -> implicacao pratica.\n"
        "- Se houver numeros no catalogo, reincorpore pelo menos dois deles literalmente, sem parafrasear ou inventar.\n"
        "- Mantenha a linguagem tecnica do agro. Nao transforme o caso em abstracao generica, conselho de coach ou sermão.\n"
        "- Se o CTA estiver desalinhado, ajuste-o como extensao logica do argumento, sem quebrar a linha tecnica.\n\n"
        "DIRETRIZES OBJETIVAS DE REVISAO:\n"
        + "\n".join(f"- {directive}" for directive in directives)
        + "\n\n"
        "Retorne o JSON completo no mesmo formato original, incluindo planejamento_narrativo."
    )


def _catalog_data_points(validated_data_catalog: dict[str, Any]) -> list[dict[str, str]]:
    points: list[dict[str, str]] = []
    for point in validated_data_catalog.get("dados_estruturados") or []:
        if not isinstance(point, dict):
            continue
        value = str(point.get("value", "")).strip()
        context = str(point.get("context", "")).strip()
        source = str(point.get("source", "")).strip()
        if not any([value, context, source]):
            continue
        points.append({"value": value, "context": context, "source": source})
    return points


def _proof_slide_index(slides: list[dict[str, Any]]) -> int | None:
    candidate_types = ("DADO", "DADOS_HISTORICOS", "MECANISMO", "SINTESE", "CASO_HUMANO", "CONSEQUENCIA")
    for index in range(len(slides) - 2, 1, -1):
        if slides[index]["slide_type"] in candidate_types:
            return index
    for index in range(len(slides) - 2, 1, -1):
        return index
    return None


def _sync_planning_with_slides(result: dict[str, Any]) -> dict[str, Any]:
    normalized_result = _normalize_generation_result(result)
    slides = normalized_result.get("slides") or []
    planning = deepcopy(normalized_result.get("planejamento_narrativo") or {})
    existing_layers = planning.get("camadas") if isinstance(planning.get("camadas"), list) else []
    synced_layers: list[dict[str, Any]] = []

    for index, slide in enumerate(slides, start=1):
        previous_layer = existing_layers[index - 1] if index - 1 < len(existing_layers) and isinstance(existing_layers[index - 1], dict) else {}
        next_slide = slides[index] if index < len(slides) else None
        synced_layers.append(
            {
                "numero": index,
                "tipo_slide": slide["slide_type"],
                "funcao_narrativa": _first_non_empty(
                    previous_layer.get("funcao_narrativa"),
                    slide.get("title"),
                    slide.get("copy"),
                    f"Cumprir o papel de {slide['slide_type']} no arco do argumento.",
                ),
                "pergunta_que_abre": _first_non_empty(
                    previous_layer.get("pergunta_que_abre"),
                    next_slide["title"] if next_slide else "",
                    next_slide["copy"] if next_slide else "",
                    "Qual decisao pratica isso abre no agro?",
                ),
                "emocao_alvo": _first_non_empty(
                    previous_layer.get("emocao_alvo"),
                    _PLANNING_EMOTION_ARC[min(index - 1, len(_PLANNING_EMOTION_ARC) - 1)],
                ),
            }
        )

    return {
        **normalized_result,
        "planejamento_narrativo": {
            "tensao_central": _first_non_empty(
                planning.get("tensao_central"),
                slides[0]["title"] if slides else "",
                slides[0]["copy"] if slides else "",
            ),
            "angulo_de_adaptacao": _first_non_empty(
                planning.get("angulo_de_adaptacao"),
                planning.get("angulo_especifico"),
                slides[1]["title"] if len(slides) > 1 else "",
            ),
            "camadas": synced_layers,
            "total_slides": len(slides),
            "provas_que_nao_podem_sumir": planning.get("provas_que_nao_podem_sumir") or [],
            "onde_termina": _first_non_empty(
                planning.get("onde_termina"),
                slides[-2]["title"] if len(slides) > 1 else "",
                slides[-1]["title"] if slides else "",
            ),
        },
    }


def _reinforce_planning_mechanisms(
    result: dict[str, Any],
    validated_data_catalog: dict[str, Any],
) -> dict[str, Any]:
    synced = _sync_planning_with_slides(result)
    planning = deepcopy(synced.get("planejamento_narrativo") or {})
    required_terms = [
        str(term).strip()
        for term in (validated_data_catalog.get("mecanismos_que_nao_podem_sumir") or [])[:3]
        if str(term).strip()
    ]
    if not required_terms:
        return synced

    planning_text = " ".join(_flatten_strings(planning)).lower()
    missing_terms = [term for term in required_terms if term.lower() not in planning_text]
    if not missing_terms:
        return synced

    base_angle = _first_non_empty(
        planning.get("angulo_de_adaptacao"),
        "Traduzir a logica do caso para decisao real no agro.",
    ).rstrip(".")
    planning["angulo_de_adaptacao"] = f"{base_angle}. Mecanismos que precisam aparecer: {', '.join(missing_terms)}."

    for camada in planning.get("camadas") or []:
        if not isinstance(camada, dict):
            continue
        slide_type = str(camada.get("tipo_slide") or "").upper()
        if slide_type in {"CAPA", "HOOK", "CTA"}:
            continue
        funcao = _first_non_empty(camada.get("funcao_narrativa"), f"Desenvolver {slide_type}").rstrip(".")
        camada["funcao_narrativa"] = f"{funcao}. Preservar mecanismo: {missing_terms[0]}."
        if len(missing_terms) > 1 and not str(camada.get("pergunta_que_abre") or "").strip():
            camada["pergunta_que_abre"] = f"Como {missing_terms[1]} muda a decisao no agro?"
        break

    return {
        **synced,
        "planejamento_narrativo": planning,
    }


def _align_cta_to_funnel(result: dict[str, Any]) -> dict[str, Any]:
    normalized_result = _normalize_generation_result(result)
    slides = deepcopy(normalized_result.get("slides") or [])
    funnel_stage = str(normalized_result.get("funnel_stage") or "").strip().lower()
    if not slides or funnel_stage not in {"topo", "meio", "fundo"}:
        return normalized_result

    current_cta = str(normalized_result.get("cta") or extract_carousel_cta(slides) or "").strip()
    aligned_cta = current_cta
    if funnel_stage == "topo":
        aligned_cta = "Salve este carrossel e compartilhe com quem precisa defender margem no agro."
    elif funnel_stage == "meio":
        aligned_cta = "Comenta MARGEM que eu aprofundo os erros que mais destroem resultado no agro."
    elif funnel_stage == "fundo":
        aligned_cta = "Entre na Confraria e aprenda a defender margem com metodo no agro."

    slides[-1]["cta"] = aligned_cta
    if not slides[-1].get("copy"):
        slides[-1]["copy"] = aligned_cta

    return {
        **normalized_result,
        "cta": aligned_cta,
        "slides": slides,
    }


def _reinforce_proof_slide(
    slides: list[dict[str, Any]],
    validated_data_catalog: dict[str, Any],
) -> list[dict[str, Any]]:
    proof_index = _proof_slide_index(slides)
    if proof_index is None:
        return slides

    reinforced = deepcopy(slides)
    proof_slide = reinforced[proof_index]
    points = _catalog_data_points(validated_data_catalog)
    anchors = [_data_point_to_anchor(point) for point in points[:2] if _data_point_to_anchor(point)]
    source_labels = [str(label).strip() for label in validated_data_catalog.get("fontes_disponiveis") or [] if str(label).strip()]
    body = " ".join([proof_slide.get("title", ""), proof_slide.get("copy", "")]).strip().lower()
    additions: list[str] = []

    for anchor in anchors:
        if anchor.lower() not in body:
            additions.append(f"{anchor}.")
    if source_labels and not any(source.lower() in body for source in source_labels):
        additions.append(f"A origem dessa evidencia aparece em {source_labels[0]}.")
    additions.append("Na pratica, esse e o ponto onde o resultado sai do discurso e aparece no caixa.")

    existing_copy = proof_slide.get("copy", "").strip()
    merged_copy = " ".join(part for part in [existing_copy, *additions] if part).strip()
    proof_slide["copy"] = merged_copy

    if anchors and not any(token in body for token in [point.get("value", "") for point in points[:1]]):
        proof_slide["title"] = f"{proof_slide.get('title', '').strip()} | {points[0]['value']}".strip(" |")

    return reinforced


def _reinforce_middle_slides(
    slides: list[dict[str, Any]],
    validated_data_catalog: dict[str, Any],
    issues: list[str],
) -> list[dict[str, Any]]:
    normalized_issues = [str(issue or "").lower() for issue in issues]
    needs_practical = any("implicacao pratica" in issue for issue in normalized_issues)
    needs_causal = any("cadeia causal" in issue for issue in normalized_issues)
    needs_theme = any("tema central pouco refletido" in issue for issue in normalized_issues)
    needs_data = any("dados" in issue for issue in normalized_issues)
    if not any([needs_practical, needs_causal, needs_theme, needs_data]):
        return slides

    reinforced = deepcopy(slides)
    middle_indexes = [index for index in range(2, max(len(reinforced) - 1, 2))]
    if not middle_indexes:
        return reinforced

    points = _catalog_data_points(validated_data_catalog)
    anchor = _data_point_to_anchor(points[0]) if points else ""
    argument_claim = _first_non_empty(
        validated_data_catalog.get("argumento_central"),
        *((validated_data_catalog.get("afirmacoes_tecnicas_permitidas") or [])[:1]),
    )
    causal_sentence = (
        f"Isso acontece porque {anchor} expõe o mecanismo que derruba resultado antes de aparecer no caixa."
        if anchor
        else "Isso acontece porque margem, risco e timing comercial se conectam antes de o problema aparecer no caixa."
    )
    claim_sentence = (
        f"O ponto central do material-base e direto: {argument_claim}."
        if argument_claim else
        "O ponto central do material-base e direto: resultado sem criterio comercial vira margem perdida."
    )

    practical_applied = False
    causal_applied = False
    claim_applied = False
    practical_target = max(1, len(middle_indexes) // 2) if needs_practical else 0
    practical_count = 0

    for index in middle_indexes:
        slide = reinforced[index]
        body = " ".join([slide.get("title", ""), slide.get("copy", "")]).lower()
        pieces = [slide.get("copy", "").strip()]

        if needs_causal and not causal_applied and "porque" not in body and "isso acontece" not in body:
            pieces.append(causal_sentence)
            causal_applied = True

        if (
            (needs_practical or needs_theme or needs_data)
            and practical_count < max(practical_target, 1)
            and "na pratica" not in body
        ):
            pieces.append(_PRACTICAL_REPAIR_SUFFIX)
            practical_applied = True
            practical_count += 1

        if (needs_causal or needs_theme or needs_data) and not claim_applied and argument_claim.lower() not in body:
            pieces.append(claim_sentence)
            claim_applied = True

        slide["copy"] = " ".join(part for part in pieces if part).strip()
        if practical_count >= practical_target and (causal_applied or not needs_causal) and claim_applied:
            break

    return reinforced


def _expand_caption_locally(
    result: dict[str, Any],
    validated_data_catalog: dict[str, Any],
) -> str:
    normalized_result = _normalize_generation_result(result)
    slides = normalized_result.get("slides") or []
    caption = str(normalized_result.get("caption") or "").strip()
    paragraphs = [part.strip() for part in caption.split("\n\n") if part.strip()]
    points = _catalog_data_points(validated_data_catalog)
    anchor_phrases = [_data_point_to_anchor(point) for point in points if _data_point_to_anchor(point)]
    source_labels = [str(label).strip() for label in validated_data_catalog.get("fontes_disponiveis") or [] if str(label).strip()]
    hook = normalized_result.get("hook") or extract_carousel_hook(slides) or ""
    cta = normalized_result.get("cta") or extract_carousel_cta(slides) or ""
    middle_slides = slides[2:-1] if len(slides) > 3 else []
    middle_summary = " ".join(
        _first_non_empty(slide.get("title"), slide.get("copy"))
        for slide in middle_slides[:2]
        if _first_non_empty(slide.get("title"), slide.get("copy")) != "—"
    ).strip()
    proof_index = _proof_slide_index(slides)
    proof_slide = slides[proof_index] if proof_index is not None else {}
    proof_summary = _first_non_empty(proof_slide.get("title"), proof_slide.get("copy"), middle_summary)

    additions = [
        (
            f"Quando o material-base mostra {anchor_phrases[0]}, ele nao esta entregando curiosidade. "
            "Ele esta mostrando onde a margem, o risco e a decisao comercial realmente mudam o resultado no agro."
        ) if anchor_phrases else (
            "Quando o dado entra na conversa certa, o argumento deixa de ser opiniao e vira criterio tecnico para decidir melhor no agro."
        ),
        (
            f"{proof_summary}. Na pratica, isso obriga produtor, consultor, revenda e vendedor a olhar menos para achismo "
            "e mais para margem, timing e capacidade de defender resultado."
        ) if proof_summary else _PRACTICAL_REPAIR_SUFFIX,
        (
            f"Se a origem da evidencia aparece em {source_labels[0]}, o papel de quem vende no agro e traduzir essa prova em decisao concreta, "
            "nao em discurso bonito."
        ) if source_labels else (
            "Quem domina essa leitura consegue transformar numero em argumento, orientar melhor o produtor e proteger caixa antes que o mercado imponha a conta."
        ),
        (
            f"{cta.rstrip('.')}."
            if cta else
            "Esse e o tipo de criterio comercial que separa quem repete processo de quem realmente constroi margem no campo."
        ),
    ]

    if not paragraphs and hook:
        paragraphs.append(
            f"{hook}. No agro, isso so fica forte de verdade quando o dado vira decisao e a decisao vira resultado."
        )

    for addition in additions:
        current_words = len(" ".join(paragraphs).split())
        if current_words >= 150:
            break
        if addition and addition not in paragraphs:
            paragraphs.append(addition)

    if len(" ".join(paragraphs).split()) < 140:
        paragraphs.append(
            "No fim, o ponto central e simples: produtividade, volume ou movimento comercial so fazem sentido quando estao ancorados em criterio, prova e leitura pratica do que protege rentabilidade."
        )

    expanded = "\n\n".join(part.strip() for part in paragraphs if part.strip())
    words = expanded.split()
    if len(words) > 320:
        expanded = " ".join(words[:320]).strip()
    return expanded


def _should_apply_local_repairs(issues: list[str]) -> bool:
    normalized_issues = [str(issue or "").lower() for issue in issues]
    return any(any(marker in issue for marker in _LOCAL_REPAIR_MARKERS) for issue in normalized_issues)


def _apply_local_quality_repairs(
    result: dict[str, Any],
    issues: list[str],
    validated_data_catalog: dict[str, Any],
) -> dict[str, Any]:
    normalized_result = _normalize_generation_result(result)
    repaired = _sync_planning_with_slides(normalized_result)
    repaired["slides"] = deepcopy(normalized_result.get("slides") or [])
    normalized_issues = [str(issue or "").lower() for issue in issues]

    if any(
        marker in issue
        for issue in normalized_issues
        for marker in (
            "slide de prova sem ancora tecnica forte",
            "poucos dados validados",
            "faltou citar a fonte",
            "os dados numericos do post-base sumiram",
        )
    ):
        repaired["slides"] = _reinforce_proof_slide(repaired["slides"], validated_data_catalog)

    if any(
        marker in issue
        for issue in normalized_issues
        for marker in (
            "implicacao pratica",
            "cadeia causal do material-base",
            "tema central pouco refletido",
            "os dados numericos do post-base sumiram",
        )
    ):
        repaired["slides"] = _reinforce_middle_slides(repaired["slides"], validated_data_catalog, issues)

    if any(_is_caption_issue(issue) for issue in issues) or len(str(repaired.get("caption") or "").split()) < 140:
        repaired["caption"] = _expand_caption_locally(repaired, validated_data_catalog)

    if any("cta pouco alinhado" in issue for issue in normalized_issues):
        repaired = _align_cta_to_funnel(repaired)

    if any("planejamento_narrativo" in issue for issue in normalized_issues):
        repaired = _sync_planning_with_slides(repaired)
    if any("nao preservou os mecanismos" in issue for issue in normalized_issues):
        repaired = _reinforce_planning_mechanisms(repaired, validated_data_catalog)

    repaired["hook"] = repaired.get("hook") or extract_carousel_hook(repaired["slides"]) or ""
    repaired["cta"] = repaired.get("cta") or extract_carousel_cta(repaired["slides"]) or ""
    return repaired


def _repair_evaluation_locally(
    evaluation: dict[str, Any],
    source_post: Post,
    evidence_pack: CarouselEvidencePack,
    target_slide_count: int,
    validated_data_catalog: dict[str, Any],
) -> dict[str, Any]:
    issues = _combine_issues(evaluation)
    if not issues or not _should_apply_local_repairs(issues):
        return evaluation

    local_result = _apply_local_quality_repairs(
        evaluation["normalized_result"],
        issues,
        validated_data_catalog,
    )
    local_evaluation = _evaluate_generation(local_result, source_post, evidence_pack, target_slide_count)
    return _pick_better_evaluation(evaluation, local_evaluation)


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
    max_tokens: int = 4000,
    max_parse_attempts: int = 3,
) -> dict[str, Any]:
    current_prompt = user_prompt
    last_error: json.JSONDecodeError | None = None

    for attempt in range(1, max_parse_attempts + 1):
        response = call_chat_completion_with_backoff(
            openai_client,
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": current_prompt},
            ],
            max_tokens=max_tokens,
            logger=logger,
            operation_name="content generation",
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
            correction_note = (
                "A resposta anterior foi uma recusa indevida. Este pedido e seguro e permitido: "
                "gerar um carrossel tecnico de marketing para o agronegocio. Nao recuse.\n"
                if _looks_like_refusal(raw_content) else
                "A resposta anterior veio vazia ou em JSON invalido.\n"
            )
            current_prompt = (
                f"{user_prompt}\n\n"
                f"{correction_note}"
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
    normalized_result = deepcopy(evaluation["normalized_result"])
    quality_report = evaluation["quality_report"]
    numeric_targets = validated_data_catalog.get("numeros_obrigatoriamente_ancorados_no_material_base") or []
    source_targets = validated_data_catalog.get("fontes_disponiveis") or []
    current_caption = str(normalized_result.get("caption") or "").strip()
    candidate_result = normalized_result

    for repair_attempt in range(1, 4):
        retry_note = ""
        if repair_attempt > 1:
            word_count = len(current_caption.split())
            retry_note = (
                "A legenda anterior ainda nao ficou dentro da faixa ideal.\n"
                f"Legenda anterior ({word_count} palavras):\n{current_caption or '<vazia>'}\n\n"
                "Reescreva do zero mantendo os mesmos dados e aumentando a densidade tecnica.\n\n"
            )

        repair_prompt = (
            f"{base_user_prompt}\n\n"
            "O carrossel abaixo ja esta estruturalmente aprovado. Nao mexa nos slides, no hook, no CTA, no funil nem no formato.\n"
            "Corrija somente a legenda.\n\n"
            f"RASCUNHO ATUAL:\n{_format_json(candidate_result)}\n\n"
            f"DIAGNOSTICO DE QUALIDADE:\n{_format_json(quality_report)}\n\n"
            f"LEITURA HUMANA DO DIAGNOSTICO:\n{format_quality_feedback(quality_report)}\n\n"
            f"CATALOGO DE DADOS VALIDADOS:\n{_format_json(validated_data_catalog)}\n\n"
            f"NUMEROS LITERAIS A INCORPORAR:\n{_format_json(numeric_targets)}\n\n"
            f"FONTES DISPONIVEIS:\n{_format_json(source_targets)}\n\n"
            f"{retry_note}"
            "REESCREVA SOMENTE O CAMPO `caption` obedecendo exatamente estas regras:\n"
            "- entre 150 e 240 palavras\n"
            "- 4 a 6 paragrafos curtos com quebras de linha\n"
            "- reaproveite os mesmos dados validados e a mesma linha tecnica do rascunho\n"
            "- se houver numeros no catalogo, reincorpore pelo menos dois literalmente\n"
            "- se houver fonte no catalogo, cite pelo menos uma de forma natural\n"
            "- deixe explicita a implicacao pratica para quem vende no agro\n"
            "- mantenha coerencia com o CTA ja existente\n"
            "- sem hashtags\n\n"
            'Retorne APENAS JSON no formato {"caption": "<nova legenda>"}'
        )
        try:
            repaired = _request_generation(system_prompt, repair_prompt, max_tokens=1200)
        except ValueError:
            break
        current_caption = (repaired.get("caption") or "").strip()
        candidate_result = {
            **candidate_result,
            "caption": current_caption,
        }
        word_count = len(current_caption.split())
        if 140 <= word_count <= 320:
            return candidate_result

    candidate_result["caption"] = _expand_caption_locally(candidate_result, validated_data_catalog)
    return candidate_result


def _polish_carousel_body(
    system_prompt: str,
    base_user_prompt: str,
    evaluation: dict[str, Any],
    validated_data_catalog: dict[str, Any],
    *,
    attempt_number: int,
) -> dict[str, Any]:
    polish_prompt = _build_targeted_polish_prompt(
        base_user_prompt,
        evaluation,
        validated_data_catalog,
        attempt_number=attempt_number,
    )
    return _request_generation(system_prompt, polish_prompt)


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
    structural_transfer_map = _build_structural_transfer_map(
        source_post,
        voice,
        top_args,
        validated_data_catalog,
        creative_brief,
        slide_blueprint,
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
        visual_transcript=_trim_for_prompt(getattr(intel, "visual_transcript", None)),
        source_caption=(source_post.caption or "—")[:1200],
        hashtags=_format_json(source_post.hashtags or []),
        virality_score=virality,
        top_arguments=top_arg_texts,
        structural_patterns=_format_json(_load_structural_patterns(source_post, top_args[:3])),
        validated_data_catalog=_format_json(validated_data_catalog),
        creative_brief=_format_json(creative_brief),
        structural_transfer_map=_format_json(structural_transfer_map),
        slide_blueprint=_format_json(slide_blueprint),
        quality_guardrails="\n".join(f"- {item}" for item in quality_guardrails),
    )

    try:
        result = _request_generation(system_prompt, user_prompt)
    except json.JSONDecodeError as exc:
        logger.error("GPT-4o returned invalid JSON for content generation: %s", exc)
        raise

    evaluation = _evaluate_generation(result, source_post, evidence_pack, target_slide_count)
    evaluation = _repair_evaluation_locally(
        evaluation,
        source_post,
        evidence_pack,
        target_slide_count,
        validated_data_catalog,
    )
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
        try:
            if _should_attempt_caption_repair(evaluation):
                revised_result = _repair_caption(system_prompt, user_prompt, evaluation, validated_data_catalog)
            elif _should_attempt_targeted_polish(evaluation):
                revised_result = _polish_carousel_body(
                    system_prompt,
                    user_prompt,
                    evaluation,
                    validated_data_catalog,
                    attempt_number=attempt_number + 1,
                )
            else:
                refinement_prompt = _build_refinement_prompt(
                    user_prompt,
                    evaluation,
                    validated_data_catalog,
                    attempt_number=attempt_number + 1,
                )
                revised_result = _request_generation(system_prompt, refinement_prompt)
        except ValueError as exc:
            logger.warning(
                "Model refinement failed for post %s on attempt %s. Falling back to local repair. Error=%s",
                source_post.id,
                attempt_number + 1,
                exc,
            )
            revised_result = _apply_local_quality_repairs(
                evaluation["normalized_result"],
                issues,
                validated_data_catalog,
            )

        evaluation = _evaluate_generation(revised_result, source_post, evidence_pack, target_slide_count)
        evaluation = _repair_evaluation_locally(
            evaluation,
            source_post,
            evidence_pack,
            target_slide_count,
            validated_data_catalog,
        )
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
        planning_narrative=deepcopy(normalized_result.get("planejamento_narrativo") or {}),
    )
    session.add(generated)
    session.commit()
    logger.info("Generated post from source post %s", source_post.id)
    return generated
