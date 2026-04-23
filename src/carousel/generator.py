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
from src.slide_utils import normalize_carousel_slides

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

_STOPWORDS = {
    "a", "as", "o", "os", "de", "da", "do", "das", "dos", "e", "em", "no", "na", "nos",
    "nas", "para", "por", "com", "sem", "um", "uma", "sobre",
}

SYSTEM_PROMPT = """Você é um copywriter especialista em carrosséis virais para Instagram no agronegócio brasileiro.
Com base no perfil de voz do criador, nos templates e estruturas reais dos cards dos concorrentes de maior viralidade, e nas referências opcionais do banco de argumentos, crie um carrossel sobre o tema fornecido.

Priorize replicar as estruturas de cards que mais performaram — argumento central forte, dado técnico específico, comparativo ou CTA claro.
Use as transcrições literais dos cards concorrentes como fonte primária para entender ordem narrativa, densidade técnica e dados que podem inspirar o novo roteiro.
Use a inteligência criativa agro para escolher uma tensão central memorável antes de escrever os slides.
Se a referencia vier de um case analitico, preserve a cadeia causal: fato disparador, mecanismo, prova e consequencia. Nao transforme isso em frase genérica de efeito.

Retorne um JSON com a estrutura de slides:
[
  {"slide_number": 1, "slide_type": "CAPA", "title": "<promessa principal>", "copy": "<texto do slide>", "cta": ""},
  {"slide_number": 2, "slide_type": "HOOK", "title": "<gancho ou dado>", "copy": "<texto do slide>", "cta": ""},
  ...
  {"slide_number": N-1, "slide_type": "PROVA", "title": "<prova ou exemplo>", "copy": "<texto>", "cta": ""},
  {"slide_number": N, "slide_type": "CTA", "title": "<fechamento>", "copy": "<texto>", "cta": "<chamada para ação>"}
]
- Entre 5 e 8 slides
- Slide 1 deve ser `CAPA`
- Slide 2 deve ser `HOOK`
- Slides intermediários devem ser `DESENVOLVIMENTO`
- Penúltimo slide deve ser `PROVA`
- Último slide deve ser `CTA`
- Use as referências do banco de argumentos apenas se elas encaixarem naturalmente no tema
- Se um dado não estiver no catálogo validado, não use
Responda APENAS com o JSON."""


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
        "A leitura precisa ganhar tensao a cada slide, sem repetir a mesma frase de jeitos diferentes.",
        "O miolo do carrossel precisa combinar dado tecnico e traducao pratica para o agro.",
        "O carrossel precisa ter uma tensao central reconhecivel: erro caro, margem em risco, decisao atrasada, contraste campo/escritorio ou oportunidade perdida.",
        "Se a referencia for um case analitico, preserve a cadeia causal e nao reduza o raciocinio a conselho generico.",
        "A criatividade deve nascer de situacoes reais do agro, nao de frase bonita sem lastro.",
        "O slide PROVA precisa ancorar um numero, comparativo ou fonte do catalogo validado.",
        "O CTA final deve pedir uma unica acao clara e nao pode soar generico.",
        "Evite frases vagas sem criterio tecnico ou prova concreta.",
    ]


def _request_carousel(context: dict[str, object]) -> dict[str, object]:
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ],
        max_tokens=1500,
    )

    raw = response.choices[0].message.content or ""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rstrip("`").strip()
    return json.loads(raw)


def _evaluate_theme_carousel(
    payload: dict[str, object] | list[dict[str, object]],
    evidence_pack: CarouselEvidencePack,
    target_slide_count: int,
) -> tuple[list[dict[str, str]], dict[str, object]]:
    slides = normalize_carousel_slides(payload.get("slides") if isinstance(payload, dict) else payload)
    if not slides:
        raise ValueError("o modelo nao retornou slides")

    problems: list[str] = []
    if slides[0]["slide_type"] != "CAPA":
        problems.append("o slide 1 precisa ser CAPA")
    if len(slides) < 2 or slides[1]["slide_type"] != "HOOK":
        problems.append("o slide 2 precisa ser HOOK")
    if len(slides) < 5:
        problems.append("o carrossel precisa ter pelo menos 5 slides")
    elif slides[-2]["slide_type"] != "PROVA":
        problems.append("o penultimo slide precisa ser PROVA")
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
        "blueprint_ideal": slide_blueprint,
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
