import re
from dataclasses import dataclass
from typing import Any, Iterable

from src.slide_utils import extract_carousel_cta, extract_carousel_hook, normalize_carousel_slides


_PRACTICAL_MARKERS = (
    "na pratica",
    "isso significa",
    "impacto",
    "resultado",
    "na decisao",
    "no campo",
    "na lavoura",
    "no comercial",
    "na revenda",
    "para o produtor",
)

_ENGAGEMENT_MARKERS = (
    "erro",
    "perde",
    "perdendo",
    "custo",
    "margem",
    "safra",
    "produtor",
    "consultor",
    "vendedor",
    "rentabilidade",
    "preco",
    "risco",
)

_FUNNEL_CTA_MARKERS = {
    "topo": ("salve", "compartilhe", "marque"),
    "meio": ("comenta", "me conta", "responde", "me diz"),
    "fundo": ("confraria", "dm", "link", "entre", "entra"),
}

_DEVELOPMENT_OBJECTIVES = (
    "Contextualizar o problema no agro brasileiro sem enrolacao.",
    "Trazer dado, comparativo ou criterio tecnico que sustente a tese.",
    "Traduzir o impacto pratico para produtor, consultor, revenda ou vendedor.",
    "Responder objeção ou mostrar aplicacao concreta no campo/comercial.",
)


@dataclass(frozen=True)
class CarouselEvidencePack:
    numeric_fragments: tuple[str, ...] = ()
    source_labels: tuple[str, ...] = ()
    allowed_claims: tuple[str, ...] = ()
    required_terms: tuple[str, ...] = ()


def _normalize_text(text: Any) -> str:
    compact = re.sub(r"\s+", " ", str(text or "").strip().lower())
    return compact


def _unique(values: Iterable[Any], *, min_chars: int = 1) -> tuple[str, ...]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        normalized = _normalize_text(text)
        if len(normalized) < min_chars or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(text)
    return tuple(deduped)


def _find_hits(text: str, candidates: Iterable[str], *, min_chars: int = 2) -> list[str]:
    haystack = _normalize_text(text)
    hits: list[str] = []
    for candidate in _unique(candidates, min_chars=min_chars):
        if _normalize_text(candidate) in haystack:
            hits.append(candidate)
    return hits


def _cta_matches_funnel(cta: str, funnel_stage: str | None) -> bool:
    if not funnel_stage:
        return True
    markers = _FUNNEL_CTA_MARKERS.get((funnel_stage or "").strip().lower(), ())
    normalized = _normalize_text(cta)
    return any(marker in normalized for marker in markers)


def estimate_target_slide_count(
    technical_depth: str | None = None,
    complexity_score: Any = None,
    *,
    minimum: int = 5,
) -> int:
    try:
        complexity = int(complexity_score)
    except (TypeError, ValueError):
        complexity = 3

    normalized_depth = _normalize_text(technical_depth)
    if normalized_depth == "especialista" or complexity >= 4:
        return max(minimum, 7)
    if normalized_depth == "intermediario" or complexity == 3:
        return max(minimum, 6)
    return max(minimum, 5)


def build_slide_blueprint(target_slide_count: int, funnel_stage: str | None = None) -> list[dict[str, str]]:
    target = max(5, min(8, int(target_slide_count or 6)))
    development_count = max(1, target - 4)

    blueprint = [
        {
            "slide_type": "CAPA",
            "objective": "Abrir com promessa ou tese principal em linguagem especifica do agro.",
            "must_include": "Promessa clara, contraste forte ou dor concreta.",
        },
        {
            "slide_type": "HOOK",
            "objective": "Gerar tensao para a leitura continuar com dado, provocacao ou pergunta.",
            "must_include": "Numero, comparativo, erro comum ou risco real.",
        },
    ]

    for index in range(development_count):
        objective = _DEVELOPMENT_OBJECTIVES[min(index, len(_DEVELOPMENT_OBJECTIVES) - 1)]
        blueprint.append(
            {
                "slide_type": "DESENVOLVIMENTO",
                "objective": objective,
                "must_include": "Insight tecnico, implicacao pratica ou orientacao acionavel.",
            }
        )

    cta_objective = {
        "topo": "Fechar com CTA de salvar, compartilhar ou marcar alguem.",
        "meio": "Fechar com CTA de comentario, resposta ou conversa.",
        "fundo": "Fechar com CTA direto para entrar na Confraria.",
    }.get((funnel_stage or "").strip().lower(), "Fechar com um CTA unico, claro e coerente com o funil.")

    blueprint.append(
        {
            "slide_type": "PROVA",
            "objective": "Ancorar a tese em prova concreta antes do fechamento.",
            "must_include": "Numero, comparativo, caso, evidencia ou fonte do catalogo.",
        }
    )
    blueprint.append(
        {
            "slide_type": "CTA",
            "objective": cta_objective,
            "must_include": "Uma unica acao clara.",
        }
    )
    return blueprint


def score_carousel_draft(
    *,
    slides: Any,
    caption: str | None,
    cta: str | None,
    funnel_stage: str | None,
    evidence_pack: CarouselEvidencePack,
    target_slide_count: int | None = None,
    min_caption_words: int | None = None,
    max_caption_words: int | None = None,
) -> dict[str, Any]:
    normalized_slides = normalize_carousel_slides(slides)
    issues: list[str] = []
    strengths: list[str] = []
    score = 0.0

    slide_count = len(normalized_slides)
    if 5 <= slide_count <= 8:
        score += 0.08
        strengths.append("contagem de slides adequada")
    else:
        issues.append(f"carrossel fora do tamanho ideal ({slide_count} slides)")

    if target_slide_count is not None and slide_count:
        if abs(slide_count - target_slide_count) <= 2:
            score += 0.05
        else:
            issues.append(f"carrossel fugiu do blueprint ideal de {target_slide_count} slides")

    structure_ok = (
        slide_count >= 5
        and normalized_slides[0]["slide_type"] == "CAPA"
        and normalized_slides[1]["slide_type"] == "HOOK"
        and normalized_slides[-2]["slide_type"] == "PROVA"
        and normalized_slides[-1]["slide_type"] == "CTA"
    )
    if structure_ok:
        score += 0.12
        strengths.append("progressao estrutural completa")
    else:
        issues.append("estrutura obrigatoria incompleta (CAPA -> HOOK -> DESENVOLVIMENTO -> PROVA -> CTA)")

    hook_slide = next((slide for slide in normalized_slides if slide["slide_type"] == "HOOK"), None)
    hook_text = " ".join(
        part for part in [
            extract_carousel_hook(normalized_slides) or "",
            hook_slide["copy"] if hook_slide else "",
        ] if part
    ).strip()
    normalized_hook = _normalize_text(hook_text)
    if hook_text and (
        re.search(r"\d", hook_text)
        or "?" in hook_text
        or any(marker in normalized_hook for marker in _ENGAGEMENT_MARKERS)
    ):
        score += 0.08
        strengths.append("hook com sinal claro de engajamento")
    else:
        issues.append("hook generico ou pouco especifico")

    development_slides = [slide for slide in normalized_slides if slide["slide_type"] == "DESENVOLVIMENTO"]
    if development_slides:
        avg_dev_words = sum(len((slide["copy"] or "").split()) for slide in development_slides) / max(len(development_slides), 1)
        if avg_dev_words >= 8:
            score += 0.08
            strengths.append("miolo com densidade adequada")
        else:
            issues.append("slides de desenvolvimento superficiais")
    else:
        issues.append("faltam slides de desenvolvimento")

    practical_hits = 0
    for slide in development_slides:
        body = " ".join([slide["title"], slide["copy"]])
        if _find_hits(body, _PRACTICAL_MARKERS, min_chars=4):
            practical_hits += 1
    if development_slides and practical_hits >= max(1, len(development_slides) // 2):
        score += 0.10
        strengths.append("desenvolvimento traduz impacto pratico")
    elif development_slides:
        issues.append("faltou traduzir o dado em implicacao pratica em parte do miolo")

    caption_text = (caption or "").strip()
    if min_caption_words is not None and max_caption_words is not None:
        if not caption_text:
            issues.append("legenda ausente")
        else:
            caption_words = len(caption_text.split())
            if min_caption_words <= caption_words <= max_caption_words:
                score += 0.10
                strengths.append("legenda densa na medida certa")
            else:
                issues.append(f"legenda fora da faixa ideal ({caption_words} palavras)")
    else:
        score += 0.05

    cta_text = (cta or "").strip() or (extract_carousel_cta(normalized_slides) or "")
    if cta_text:
        score += 0.08
    else:
        issues.append("cta ausente")

    if cta_text and _cta_matches_funnel(cta_text, funnel_stage):
        score += 0.08
        strengths.append("cta coerente com o funil")
    elif cta_text and funnel_stage:
        issues.append(f"cta pouco alinhado ao funil {funnel_stage}")
    elif cta_text:
        score += 0.04

    combined_text = " ".join(
        [caption_text, cta_text]
        + [slide["title"] for slide in normalized_slides]
        + [slide["copy"] for slide in normalized_slides]
    )
    proof_text = " ".join(str(value) for value in normalized_slides[-2].values()) if slide_count >= 2 else ""

    numeric_hits = _find_hits(combined_text, evidence_pack.numeric_fragments, min_chars=2)
    source_hits = _find_hits(combined_text, evidence_pack.source_labels, min_chars=3)
    proof_hits = _find_hits(proof_text, evidence_pack.numeric_fragments + evidence_pack.source_labels, min_chars=2)
    term_hits = _find_hits(combined_text, evidence_pack.required_terms, min_chars=3)

    if evidence_pack.numeric_fragments:
        needed_hits = 2 if len(evidence_pack.numeric_fragments) >= 2 else 1
        if len(numeric_hits) >= needed_hits:
            score += 0.15
            strengths.append("dados numericos validados reaproveitados")
        else:
            issues.append("poucos dados validados do catalogo chegaram ao texto final")
    else:
        score += 0.08

    if evidence_pack.numeric_fragments or evidence_pack.source_labels:
        if proof_hits:
            score += 0.10
            strengths.append("slide de prova ancorado em evidencia")
        else:
            issues.append("slide de prova sem ancora tecnica forte")
    else:
        if len(proof_text.split()) >= 8:
            score += 0.06
            strengths.append("slide de prova detalhado mesmo sem catalogo rico")
        else:
            issues.append("slide de prova raso demais")

    if evidence_pack.source_labels:
        if source_hits:
            score += 0.08
            strengths.append("fonte ou origem da evidencia apareceu")
        else:
            issues.append("faltou citar a fonte/origem disponivel no catalogo")
    else:
        score += 0.05

    if evidence_pack.required_terms:
        if term_hits:
            score += 0.06
        else:
            issues.append("tema central pouco refletido no texto final")
    else:
        score += 0.03

    final_score = round(min(score, 1.0), 2)
    return {
        "score": final_score,
        "issues": issues,
        "strengths": strengths,
        "metrics": {
            "slide_count": slide_count,
            "target_slide_count": target_slide_count,
            "numeric_hits": len(numeric_hits),
            "source_hits": len(source_hits),
            "proof_hits": len(proof_hits),
            "practical_hits": practical_hits,
        },
    }


def format_quality_feedback(report: dict[str, Any]) -> str:
    lines = [f"score calculado: {int((report.get('score') or 0) * 100)}%"]
    strengths = report.get("strengths") or []
    if strengths:
        lines.append("forcas: " + "; ".join(strengths[:4]))
    issues = report.get("issues") or []
    if issues:
        lines.append("ajustes obrigatorios: " + "; ".join(issues))
    metrics = report.get("metrics") or {}
    if metrics:
        lines.append(
            "metricas: "
            f"slides={metrics.get('slide_count')}, "
            f"hits_numericos={metrics.get('numeric_hits')}, "
            f"hits_fontes={metrics.get('source_hits')}, "
            f"hits_prova={metrics.get('proof_hits')}"
        )
    return "\n".join(lines)
