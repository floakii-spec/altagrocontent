import json
import logging
import re
from openai import OpenAI
from sqlalchemy.orm import Session, joinedload
from src.carousel_quality import (
    CarouselEvidencePack,
    build_slide_blueprint,
    estimate_target_slide_count,
    format_quality_feedback,
    score_carousel_draft,
)
from src.config import OPENAI_API_KEY
from src.generator.creative_intelligence import build_theme_creative_brief
from src.models import ArgumentBank, Carousel, Post, PostAnalysis, Profile, ProfileVoice, WeeklyReport
from src.openai_utils import call_chat_completion_with_backoff
from src.slide_utils import normalize_carousel_slides

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)
_PLANNING_EMOTION_ARC = (
    "espanto",
    "admiracao",
    "revelacao",
    "indignacao",
    "analise",
    "leveza",
    "sintese",
)

_STOPWORDS = {
    "a", "as", "o", "os", "de", "da", "do", "das", "dos", "e", "em", "no", "na", "nos",
    "nas", "para", "por", "com", "sem", "um", "uma", "sobre",
}

SYSTEM_PROMPT = """Você é um arquiteto de narrativas para Instagram no agronegócio brasileiro.

Seu trabalho tem duas etapas obrigatórias, nesta ordem:

══════════════════════════════════════════
ETAPA 1 — PLANEJAMENTO NARRATIVO
══════════════════════════════════════════
Antes de escrever um único slide, mapeie:

1. TENSÃO CENTRAL: Qual é o paradoxo, contraste ou provocação que torna este tema impossível de ignorar? Não é o tema — é o ângulo específico que cria espanto ou desconforto no leitor.

2. ÂNGULO ESPECÍFICO: Qual a entrada mais forte? (Não "agro e produtividade" — mas "o Brasil produz mais que os EUA e fica com menos margem".)

3. CAMADAS DO ARGUMENTO: Quantas revelações distintas este argumento tem? Cada camada responde uma pergunta que a anterior deixou em aberto. Se duas camadas revelam a mesma coisa, uma delas não existe.

4. ARCO EMOCIONAL: Para cada slide, qual emoção ele deve provocar? O tom varia a cada slide: espanto → admiração → revelação → indignação → análise fria → leveza → síntese → ação. Nunca tom uniforme.

5. PONTO DE TÉRMINO: O argumento termina quando o leitor não tem mais nenhuma pergunta em aberto. O número de slides é uma consequência do argumento — nunca uma restrição.

══════════════════════════════════════════
ETAPA 2 — ESCRITA DOS SLIDES
══════════════════════════════════════════
Escreva tantos slides quantos o argumento exigir.

REGRAS INVIOLÁVEIS DE COPYWRITING (derivadas de análise de posts com alta performance):

1. HOOK PARADOXAL: Abra com contraste que elimina a resposta óbvia antes de fazer a pergunta. O leitor fica sem saída cognitiva e precisa continuar.

2. PALAVRA-CONCEITO EM PARÁGRAFO SOLO: Quando introduzir um conceito central, coloque-o sozinho em sua própria linha. Ex: "Monopólio." — depois explique.

3. PERGUNTA NO FINAL DO SLIDE, NUNCA NO INÍCIO: A pergunta cria suspense para o próximo card. Abrir com pergunta entrega o gancho antes do golpe.

4. "MAS" COMO MOTOR: Use "Mas" para criar contraste, aprofundar ou revelar a camada seguinte. É a palavra que empurra o scroll.

5. REGRA DOS TRÊS: Três elementos paralelos antes de uma conclusão. A conclusão é mais forte depois de três golpes. Ex: "Não paga jogador. Não constrói estádio. Não opera time. É um modelo onde os custos são terceirizados e a receita é toda sua."

6. CONTRASTE RÍTMICO: Frase de 3–5 palavras depois de parágrafo longo força pausa cognitiva. Ex: "A FIFA não tem."

7. DADO → REFERÊNCIA FAMILIAR → MULTIPLICAÇÃO: Nunca dado isolado. Sempre âncora de comparação que o leitor conhece + multiplicação que o autor já calculou.

8. SÍNTESE NO FINAL, NUNCA NO INÍCIO: O leitor constrói a tese mentalmente. A síntese confirma o que já intuía — a satisfação é de reconhecimento, não de aprendizado.

9. CTA COMO EXTENSÃO LÓGICA: O desejo foi construído pelo conteúdo. O CTA captura — nunca interrompe o raciocínio.

TIPOS DE SLIDE DISPONÍVEIS:
- CAPA — tensão central que torna o tema impossível de ignorar
- HOOK — lacuna cognitiva com pergunta ou contraste no FINAL
- MODELO — mecanismo básico com três elementos paralelos
- ESCALADA — sinaliza nível mais profundo ("só que fica ainda melhor")
- DADO — número com âncora familiar + consequência imediata
- MECANISMO — engrenagem causal em profundidade
- REVELACAO — contradiz o que o leitor assumia (emoção antes da explicação)
- DADOS_HISTORICOS — curva temporal que o leitor vê e projeta
- CASO_HUMANO — protagonista específico, nome, números reais, culpa removida
- CONSEQUENCIA — impacto fisicamente visualizável
- RESPIRO — comparação inesperada para aliviar tensão entre blocos pesados
- POLITICA — camada oculta: quem se beneficia, ciclo que se fecha
- SINTESE — tese central entregue quando o leitor já a construiu mentalmente
- CTA — ação que é extensão natural do argumento

Retorne um JSON com esta estrutura EXATA:
{
  "planejamento_narrativo": {
    "tensao_central": "<o paradoxo ou contraste — não o tema genérico>",
    "angulo_especifico": "<a entrada provocadora exata>",
    "camadas": [
      {
        "numero": 1,
        "tipo_slide": "CAPA",
        "funcao_narrativa": "<o que este slide faz no arco>",
        "pergunta_que_abre": "<qual pergunta fica no ar depois deste slide>",
        "emocao_alvo": "<espanto|admiracao|revelacao|indignacao|analise|leveza|sintese>"
      }
    ],
    "total_slides": <N>,
    "onde_termina": "<quando o argumento está completo>"
  },
  "slides": [
    {"slide_number": 1, "slide_type": "CAPA", "title": "<título>", "copy": "<texto>", "cta": ""},
    {"slide_number": 2, "slide_type": "HOOK", "title": "<título>", "copy": "<texto>", "cta": ""},
    ...,
    {"slide_number": N-1, "slide_type": "SINTESE", "title": "<título>", "copy": "<texto>", "cta": ""},
    {"slide_number": N, "slide_type": "CTA", "title": "<título>", "copy": "<texto>", "cta": "<chamada para ação>"}
  ]
}

REGRAS DO JSON:
- Slide 1 deve ser CAPA
- Slide 2 deve ser HOOK
- Último slide deve ser CTA
- O número de slides é determinado pelo planejamento_narrativo — sem limite superior
- Responda APENAS com o JSON, sem markdown"""


def _tokenize_theme(text: str) -> set[str]:
    tokens = {
        token
        for token in re.findall(r"[a-zA-ZÀ-ÿ0-9]+", (text or "").lower())
        if len(token) > 2 and token not in _STOPWORDS
    }
    return tokens


def _select_theme_arguments(session: Session, theme: str) -> list[ArgumentBank]:
    theme_tokens = _tokenize_theme(theme)
    if not theme_tokens:
        return []

    candidates = (
        session.query(ArgumentBank)
        .filter(ArgumentBank.origin == "extracted")
        .order_by((ArgumentBank.virality_weight * ArgumentBank.quality_score).desc())
        .limit(30)
        .all()
    )

    ranked: list[tuple[int, ArgumentBank]] = []
    for arg in candidates:
        haystack = " ".join(
            part for part in [arg.text, arg.topic_cluster or "", arg.agro_segment or ""] if part
        )
        overlap = len(theme_tokens.intersection(_tokenize_theme(haystack)))
        if overlap > 0:
            ranked.append((overlap, arg))

    ranked.sort(key=lambda item: (item[0], item[1].virality_weight * item[1].quality_score), reverse=True)
    return [arg for _, arg in ranked[:5]]


def _trim_for_prompt(text: str | None, limit: int = 2500) -> str:
    value = (text or "").strip()
    if not value:
        return ""
    if len(value) <= limit:
        return value
    return f"{value[:limit].rstrip()}\n...[transcrição truncada para caber no prompt]"


def _extract_numeric_fragments(posts: list[Post]) -> list[str]:
    fragments: list[str] = []
    for post in posts:
        intel = post.intelligence
        for point in getattr(intel, "data_points", []) or []:
            if not isinstance(point, dict):
                continue
            value = str(point.get("value", "")).strip()
            if value and value not in fragments:
                fragments.append(value)
        for claim in getattr(intel, "technical_claims", []) or []:
            if not isinstance(claim, str):
                continue
            for fragment in re.findall(r"\d+[.,]?\d*%?", claim):
                if fragment not in fragments:
                    fragments.append(fragment)
    return fragments


def _estimate_theme_slide_count(posts: list[Post]) -> int:
    complexity_scores: list[int] = []
    for post in posts:
        raw_score = getattr(post.intelligence, "carousel_complexity", {}).get("complexity_score")
        try:
            complexity_scores.append(int(raw_score))
        except (TypeError, ValueError):
            continue
    average_complexity = round(sum(complexity_scores) / len(complexity_scores)) if complexity_scores else 3
    return estimate_target_slide_count("intermediario", average_complexity, minimum=6)


def _extract_theme_mechanism_terms(theme: str, top_args: list[ArgumentBank], posts: list[Post]) -> list[str]:
    candidates = [theme]
    candidates.extend(arg.text for arg in top_args if arg.text.strip())
    for post in posts:
        intel = post.intelligence
        candidates.extend(
            [
                intel.core_argument or "",
                intel.argument_structure or "",
                *(claim for claim in intel.technical_claims or [] if isinstance(claim, str)),
                *(point.get("context", "") for point in intel.data_points or [] if isinstance(point, dict)),
            ]
        )

    deduped: list[str] = []
    for token in _tokenize_theme(" ".join(candidates)):
        if token not in deduped:
            deduped.append(token)
    return deduped[:10]


def _build_theme_evidence_pack(theme: str, top_args: list[ArgumentBank], posts: list[Post]) -> CarouselEvidencePack:
    source_labels: list[str] = []
    allowed_claims: list[str] = []
    for post in posts:
        intel = post.intelligence
        source_labels.extend(str(source).strip() for source in getattr(intel, "sources_referenced", []) or [] if str(source).strip())
        allowed_claims.extend(
            claim for claim in [intel.core_argument or "", *(intel.technical_claims or [])] if str(claim).strip()
        )

    required_terms = _extract_theme_mechanism_terms(theme, top_args, posts)
    return CarouselEvidencePack(
        numeric_fragments=tuple(_extract_numeric_fragments(posts)),
        source_labels=tuple(dict.fromkeys(source_labels)),
        allowed_claims=tuple(dict.fromkeys([arg.text for arg in top_args if arg.text.strip()] + allowed_claims)),
        required_terms=tuple(required_terms),
    )


def _build_validated_theme_catalog(
    theme: str,
    top_args: list[ArgumentBank],
    posts: list[Post],
    report: WeeklyReport | None,
) -> dict[str, object]:
    proof_points: list[dict[str, object]] = []
    for post in posts[:6]:
        intel = post.intelligence
        proof_points.append(
            {
                "core_argument": intel.core_argument or "",
                "technical_claims": (intel.technical_claims or [])[:2],
                "data_points": (intel.data_points or [])[:3],
                "sources_referenced": intel.sources_referenced or [],
                "visual_transcript": _trim_for_prompt(getattr(intel, "visual_transcript", None), limit=1800),
                "virality_score": post.analysis.virality_score if post.analysis else None,
            }
        )

    return {
        "tema_solicitado": theme,
        "numeros_disponiveis": _extract_numeric_fragments(posts),
        "fontes_disponiveis": list(
            dict.fromkeys(
                source
                for post in posts
                for source in (post.intelligence.sources_referenced or [])
                if str(source).strip()
            )
        ),
        "afirmacoes_tecnicas_permitidas": list(
            dict.fromkeys(
                [arg.text for arg in top_args if arg.text.strip()]
                + [
                    claim
                    for post in posts
                    for claim in ([post.intelligence.core_argument or ""] + (post.intelligence.technical_claims or []))
                    if str(claim).strip()
                ]
            )
        )[:12],
        "provas_de_posts_virais": proof_points,
        "padroes_do_relatorio_semanal": {
            "top_formats": report.top_formats if report else {},
            "top_themes": report.top_themes if report else {},
            "language_patterns": report.language_patterns if report else {},
        },
    }


def _build_quality_guardrails() -> list[str]:
    return [
        "O numero de slides e determinado pelo argumento — nao existe limite superior.",
        "Cada slide tem uma funcao narrativa unica. Se dois slides revelam a mesma coisa, um deles nao existe.",
        "O tom varia a cada slide — nunca uniforme. Espanto, admiracao, indignacao, analise, leveza, sintese.",
        "A sintese central vem no penultimo slide, nunca no primeiro.",
        "O CTA e extensao logica do argumento — o desejo foi construido pelo conteudo.",
        "Cada dado precisa de ancora de referencia familiar e multiplicacao calculada.",
        "Nunca reduza um caso analitico a conselho generico de gestao.",
        "Use 'Mas' como motor de transicao entre camadas do argumento.",
    ]


def _request_carousel(context: dict[str, object]) -> dict[str, object]:
    response = call_chat_completion_with_backoff(
        openai_client,
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ],
        max_tokens=4000,
        logger=logger,
        operation_name="theme carousel generation",
    )

    raw = response.choices[0].message.content or ""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rstrip("`").strip()
    return json.loads(raw)


def _build_legacy_theme_planning(slides: list[dict[str, object]]) -> dict[str, object]:
    total = len(slides)
    camadas: list[dict[str, object]] = []
    for index, slide in enumerate(slides, start=1):
        next_slide = slides[index] if index < total else None
        camadas.append(
            {
                "numero": index,
                "tipo_slide": slide["slide_type"],
                "funcao_narrativa": str(slide.get("title") or slide.get("copy") or f"Desenvolver {slide['slide_type']}").strip(),
                "pergunta_que_abre": str(
                    (next_slide.get("title") if next_slide else "")
                    or (next_slide.get("copy") if next_slide else "")
                    or "Qual o proximo passo desse argumento?"
                ).strip(),
                "emocao_alvo": _PLANNING_EMOTION_ARC[min(index - 1, len(_PLANNING_EMOTION_ARC) - 1)],
            }
        )

    return {
        "tensao_central": str(slides[0].get("title") or slides[0].get("copy") or "Tensao central inferida do rascunho legado.").strip(),
        "angulo_especifico": str(
            (slides[1].get("title") if len(slides) > 1 else "")
            or (slides[1].get("copy") if len(slides) > 1 else "")
            or (slides[0].get("copy") if slides else "")
        ).strip(),
        "camadas": camadas,
        "total_slides": total,
        "onde_termina": str(
            (slides[-2].get("title") if len(slides) > 1 else "")
            or (slides[-1].get("title") if slides else "")
            or "Quando a tese central estiver clara."
        ).strip(),
    }


def _upgrade_legacy_theme_payload(
    payload: dict[str, object] | list[dict[str, object]],
) -> dict[str, object]:
    raw = payload if isinstance(payload, dict) else {"slides": payload}
    if not isinstance(raw, dict):
        return {"slides": []}

    slides = normalize_carousel_slides(raw.get("slides"))
    if not slides:
        return {**raw, "slides": []}

    if isinstance(raw.get("planejamento_narrativo"), dict):
        return {**raw, "slides": slides}

    logger.warning("Upgrading legacy theme carousel payload without planejamento_narrativo.")
    return {
        **raw,
        "slides": slides,
        "planejamento_narrativo": _build_legacy_theme_planning(slides),
    }


def _validate_planning(payload: dict) -> list[str]:
    """Validate that the narrative planning phase was completed."""
    planning = payload.get("planejamento_narrativo")
    if not isinstance(planning, dict):
        return ["planejamento_narrativo ausente — o modelo pulou a etapa de pensamento"]
    issues = []
    if not str(planning.get("tensao_central", "")).strip():
        issues.append("planejamento_narrativo sem tensao_central")
    if not str(planning.get("angulo_especifico", "")).strip():
        issues.append("planejamento_narrativo sem angulo_especifico")
    camadas = planning.get("camadas")
    if not isinstance(camadas, list) or len(camadas) < 3:
        issues.append("planejamento_narrativo com menos de 3 camadas — argumento incompleto")
    return issues


def _evaluate_theme_carousel(
    payload: dict[str, object] | list[dict[str, object]],
    evidence_pack: CarouselEvidencePack,
    target_slide_count: int,
) -> tuple[list[dict[str, str]], dict[str, object]]:
    raw = _upgrade_legacy_theme_payload(payload)
    slides = normalize_carousel_slides(raw.get("slides"))
    if not slides:
        raise ValueError("o modelo nao retornou slides")

    problems: list[str] = []

    # Validate planning phase
    planning_issues = _validate_planning(raw)
    problems.extend(planning_issues)

    # Structural anchors: CAPA[0], HOOK[1], CTA[-1]
    if slides[0]["slide_type"] != "CAPA":
        problems.append("o slide 1 precisa ser CAPA")
    if len(slides) < 2 or slides[1]["slide_type"] != "HOOK":
        problems.append("o slide 2 precisa ser HOOK")
    if len(slides) < 5:
        problems.append("o carrossel precisa ter pelo menos 5 slides")
    if slides[-1]["slide_type"] != "CTA":
        problems.append("o ultimo slide precisa ser CTA")

    quality_report = score_carousel_draft(
        slides=slides,
        caption="",
        cta=slides[-1]["cta"] if slides else "",
        funnel_stage=None,
        evidence_pack=evidence_pack,
        target_slide_count=target_slide_count,
        min_caption_words=None,
        max_caption_words=None,
    )
    for issue in quality_report["issues"]:
        if issue not in problems:
            problems.append(issue)
    return slides, {"problems": problems, "quality_report": quality_report}


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

    top_args = _select_theme_arguments(session, theme)

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
            "visual_transcript": _trim_for_prompt(getattr(p.intelligence, "visual_transcript", None)),
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

    target_slide_count = _estimate_theme_slide_count(top_competitor_posts)
    evidence_pack = _build_theme_evidence_pack(theme, top_args, top_competitor_posts)
    validated_catalog = _build_validated_theme_catalog(theme, top_args, top_competitor_posts, report)
    creative_brief = build_theme_creative_brief(theme, top_competitor_posts, top_args, report)
    slide_blueprint = build_slide_blueprint(target_slide_count)
    quality_guardrails = _build_quality_guardrails()

    context = {
        "tema": theme,
        "instrucao_de_profundidade": (
            f"O argumento sobre '{theme}' deve ser desenvolvido até o fim. "
            f"O blueprint sugere {target_slide_count} slides como ponto de partida — "
            f"use mais se o argumento tiver mais camadas."
        ),
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
        "referencias_opcionais_do_banco": [a.text for a in top_args],
        "catalogo_de_dados_validados": validated_catalog,
        "inteligencia_criativa_agro": creative_brief,
        "blueprint_sugerido": slide_blueprint,
        "metas_de_qualidade": quality_guardrails,
    }

    try:
        payload = _request_carousel(context)
    except json.JSONDecodeError as exc:
        logger.error("GPT-4o returned invalid JSON for carousel theme '%s': %s", theme, exc)
        raise

    slides, evaluation = _evaluate_theme_carousel(payload, evidence_pack, target_slide_count)
    if evaluation["problems"] or evaluation["quality_report"]["score"] < 0.72:
        logger.warning(
            "Carousel for theme '%s' failed quality gate: %s",
            theme,
            "; ".join(evaluation["problems"]) if evaluation["problems"] else format_quality_feedback(evaluation["quality_report"]),
        )
        retry_context = {
            **context,
            "rascunho_anterior": slides,
            "planejamento_anterior": payload.get("planejamento_narrativo") if isinstance(payload, dict) else None,
            "diagnostico_de_qualidade": evaluation["quality_report"],
            "instrucao_de_revisao": format_quality_feedback(evaluation["quality_report"]),
        }
        payload = _request_carousel(retry_context)
        slides, evaluation = _evaluate_theme_carousel(payload, evidence_pack, target_slide_count)
        if evaluation["problems"] or evaluation["quality_report"]["score"] < 0.72:
            raise ValueError(
                f"Carousel generation for theme '{theme}' failed quality gate: "
                f"{'; '.join(evaluation['problems'] or evaluation['quality_report']['issues'])}"
            )

    carousel = Carousel(theme=theme, slides=slides, based_on_reports=[report.id] if report else [])
    session.add(carousel)
    session.commit()
    logger.info("Carousel generated for theme '%s' with %d slides", theme, len(slides))
    return carousel
