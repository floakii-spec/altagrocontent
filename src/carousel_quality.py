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

_CREATIVE_TENSION_MARKERS = (
    "decisao",
    "decisão",
    "risco",
    "margem",
    "custo",
    "erro",
    "perda",
    "perde",
    "contraste",
    "antes",
    "depois",
    "achismo",
    "criterio",
    "critério",
    "oportunidade",
)

_CAUSAL_REASONING_MARKERS = (
    "porque",
    "por isso",
    "por trás",
    "isso significa",
    "ou seja",
    "quando",
    "depende",
    "sem",
    "mas",
    "nao foi",
    "não foi",
    "foi o que",
    "foi porque",
)

# Slide types that carry the narrative middle (not anchors)
_NARRATIVE_MIDDLE_TYPES = {
    "MODELO", "ESCALADA", "DADO", "DADOS_HISTORICOS", "MECANISMO",
    "REVELACAO", "CASO_HUMANO", "CONSEQUENCIA", "RESPIRO", "POLITICA",
    "SINTESE", "DESENVOLVIMENTO",
}

_TOKEN_STOPWORDS = {
    "a", "as", "ao", "aos", "da", "das", "de", "do", "dos", "e", "em", "na", "nas",
    "no", "nos", "o", "os", "ou", "para", "por", "que", "se", "sem", "um", "uma",
    "mais", "menos", "como", "isso", "essa", "esse", "sua", "seu", "sao", "são",
    "ser", "foi", "tem", "porque", "quando", "entre", "sobre", "com", "num", "numa",
    "ate", "até", "mas", "muito", "muita", "todo", "toda", "todos", "todas",
}

_FUNNEL_CTA_MARKERS = {
    "topo": ("salve", "compartilhe", "marque"),
    "meio": ("comenta", "me conta", "responde", "me diz"),
    "fundo": ("confraria", "dm", "link", "entre", "entra"),
}

# Blueprint objectives for narrative middle slides — cycles through as needed
_MIDDLE_SLIDE_OBJECTIVES = (
    (
        "MODELO",
        "Explicar o mecanismo básico com três elementos paralelos. A regra das três negativas ou afirmações converge para uma conclusão que o leitor ainda não tem.",
        "Três elementos paralelos + conclusão que emerge deles.",
    ),
    (
        "ESCALADA",
        "Sinalizar que existe um nível mais profundo. 'Só que fica ainda melhor' — prometer e cumprir a revelação do próximo slide.",
        "Frase de transição explícita + dado ou fato que justifica a escalada.",
    ),
    (
        "DADO",
        "Apresentar dado com âncora de referência familiar e multiplicação imediata. Nunca dado isolado — sempre com comparação que o leitor não precisa calcular.",
        "Número + referência familiar + consequência imediata.",
    ),
    (
        "MECANISMO",
        "Aprofundar a engrenagem causal: o que disparou o problema, por que ele aconteceu, o que isso significa na prática.",
        "Cadeia fato → por que → implicação. Sem pular etapas.",
    ),
    (
        "REVELACAO",
        "Contradizer o que o leitor assumia. A emoção (surpresa, indignação, admiração) vem antes da explicação — nunca depois.",
        "Afirmação que quebra a suposição + explicação curta + nova lacuna aberta.",
    ),
    (
        "DADOS_HISTORICOS",
        "Apresentar curva temporal — não números isolados, mas trajetória que o leitor vê e projeta naturalmente.",
        "Série de dados em progressão + implicação da tendência.",
    ),
    (
        "CASO_HUMANO",
        "Humanizar com protagonista específico: nome, história, números reais. Remover culpa — forças externas explicam o resultado.",
        "Nome + situação concreta + números reais + forças externas como causa.",
    ),
    (
        "CONSEQUENCIA",
        "Traduzir dado em impacto fisicamente visualizável. O leitor deve conseguir imaginar a cena, não apenas entender o conceito.",
        "Cena concreta e específica que o leitor pode visualizar.",
    ),
    (
        "RESPIRO",
        "Comparação inesperada, dado absurdo ou analogia que alivia a tensão antes do próximo bloco pesado. Humor funcional — serve ao ritmo, não à comédia.",
        "Comparação fora do contexto imediato + dado que torna a comparação precisa.",
    ),
    (
        "POLITICA",
        "Mostrar a camada oculta: quem se beneficia, como o poder se perpetua, o ciclo que se fecha.",
        "Mecanismo de benefício → dependência criada → ciclo fechado.",
    ),
    (
        "SINTESE",
        "Entregar a síntese que o leitor construiu mentalmente ao longo de todos os slides anteriores. A tese central vem aqui, não no slide 1.",
        "Confirmação do que o leitor já intuía — satisfação de reconhecimento, não de aprendizado.",
    ),
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


def _tokenize(text: Any, *, min_chars: int = 4) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-ZÀ-ÿ0-9$%]+", str(text or "").lower())
        if len(token) >= min_chars and token not in _TOKEN_STOPWORDS
    }


def _find_token_overlap_hits(text: str, candidates: Iterable[str], *, min_overlap: int = 2) -> list[str]:
    haystack_tokens = _tokenize(text)
    hits: list[str] = []
    for candidate in _unique(candidates, min_chars=4):
        candidate_tokens = _tokenize(candidate)
        if not candidate_tokens:
            continue
        needed = min(min_overlap, len(candidate_tokens))
        if len(candidate_tokens.intersection(haystack_tokens)) >= needed:
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
    """Estimate how many slides the argument needs. No upper cap — depth drives count."""
    try:
        complexity = int(complexity_score)
    except (TypeError, ValueError):
        complexity = 3

    normalized_depth = _normalize_text(technical_depth)
    if normalized_depth == "especialista" or complexity >= 4:
        return max(minimum, 12)
    if normalized_depth == "intermediario" or complexity == 3:
        return max(minimum, 8)
    return max(minimum, 6)


def build_slide_blueprint(target_slide_count: int, funnel_stage: str | None = None) -> list[dict[str, str]]:
    """Build a narrative blueprint. No upper cap — argument depth determines slide count."""
    target = max(5, int(target_slide_count or 8))
    # CAPA + HOOK + SINTESE + CTA = 4 fixed anchor slots
    middle_count = max(1, target - 4)

    blueprint: list[dict[str, str]] = [
        {
            "slide_type": "CAPA",
            "objective": "Abrir com paradoxo, contraste ou provocação que torna o tema impossível de ignorar. O leitor precisa sentir espanto antes de entender a tese.",
            "must_include": "Tensão central ou comparação que elimina a resposta óbvia do leitor.",
        },
        {
            "slide_type": "HOOK",
            "objective": "Criar lacuna cognitiva que só pode ser fechada continuando a leitura. Terminar com pergunta ou contraste no FINAL — nunca no início.",
            "must_include": "Pergunta ou afirmação perturbadora no final do slide.",
        },
    ]

    for i in range(middle_count):
        obj = _MIDDLE_SLIDE_OBJECTIVES[i % len(_MIDDLE_SLIDE_OBJECTIVES)]
        blueprint.append(
            {
                "slide_type": obj[0],
                "objective": obj[1],
                "must_include": obj[2],
            }
        )

    cta_objective = {
        "topo": "Fechar com CTA de salvar, compartilhar ou marcar alguem.",
        "meio": "Fechar com CTA de comentario, resposta ou conversa.",
        "fundo": "Fechar com CTA direto para entrar na Confraria.",
    }.get((funnel_stage or "").strip().lower(), "Fechar com um CTA único, claro e coerente com o funil.")

    blueprint.append(
        {
            "slide_type": "SINTESE",
            "objective": "Entregar a síntese que o leitor construiu mentalmente. A tese central vem aqui, não no slide 1.",
            "must_include": "Confirmação do que o leitor já intuía — satisfação de reconhecimento.",
        }
    )
    blueprint.append(
        {
            "slide_type": "CTA",
            "objective": cta_objective,
            "must_include": "Extensão lógica do argumento — o desejo foi construído pelo post, o CTA apenas captura.",
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

    # Minimum 5 slides required — no upper cap
    if slide_count >= 5:
        score += 0.08
        strengths.append("profundidade de argumento adequada")
    else:
        issues.append(f"carrossel raso demais ({slide_count} slides — argumento incompleto)")

    # Reward depth: more slides = deeper argument (up to a point)
    if target_slide_count is not None and slide_count:
        if slide_count >= target_slide_count:
            score += 0.05
            strengths.append("argumento desenvolvido até a profundidade esperada")
        elif slide_count >= target_slide_count - 2:
            score += 0.02

    # Structure: CAPA[0] + HOOK[1] + CTA[-1] — PROVA penultimate NOT required
    structure_ok = (
        slide_count >= 5
        and normalized_slides[0]["slide_type"] == "CAPA"
        and normalized_slides[1]["slide_type"] == "HOOK"
        and normalized_slides[-1]["slide_type"] == "CTA"
    )
    if structure_ok:
        score += 0.12
        strengths.append("arco narrativo ancorado (CAPA → HOOK → ... → CTA)")
    else:
        issues.append("estrutura obrigatória incompleta (slide 1 = CAPA, slide 2 = HOOK, último = CTA)")

    # Narrative variety: distinct middle types signal real arc, not repetition
    middle_slides = normalized_slides[2:-1]
    if middle_slides:
        distinct_types = len(set(s["slide_type"] for s in middle_slides))
        if distinct_types >= 3:
            score += 0.08
            strengths.append("arco narrativo com variação de tipos de slide")
        elif distinct_types >= 2:
            score += 0.04
        else:
            issues.append("slides intermediários com tipo único — argumento provavelmente uniforme")

    # Hook quality
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

    # Middle slide density
    if middle_slides:
        avg_dev_words = sum(len((slide["copy"] or "").split()) for slide in middle_slides) / max(len(middle_slides), 1)
        if avg_dev_words >= 8:
            score += 0.08
            strengths.append("miolo com densidade adequada")
        else:
            issues.append("slides de desenvolvimento superficiais")
    else:
        issues.append("faltam slides de desenvolvimento")

    # Practical translation
    practical_hits = 0
    for slide in middle_slides:
        body = " ".join([slide["title"], slide["copy"]])
        if _find_hits(body, _PRACTICAL_MARKERS, min_chars=4):
            practical_hits += 1
    if middle_slides and practical_hits >= max(1, len(middle_slides) // 2):
        score += 0.10
        strengths.append("desenvolvimento traduz impacto pratico")
    elif middle_slides:
        issues.append("faltou traduzir o dado em implicacao pratica em parte do miolo")

    # Creative tension
    creative_tension_hits = 0
    for slide in normalized_slides:
        body = " ".join([slide["title"], slide["copy"]])
        if _find_hits(body, _CREATIVE_TENSION_MARKERS, min_chars=4):
            creative_tension_hits += 1
    if creative_tension_hits >= 2:
        score += 0.05
        strengths.append("tensao criativa agro presente")

    # Causal reasoning
    causal_hits = 0
    for slide in middle_slides:
        body = " ".join([slide["title"], slide["copy"]])
        if _find_hits(body, _CAUSAL_REASONING_MARKERS, min_chars=3):
            causal_hits += 1

    # Caption
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

    # CTA presence and funnel alignment
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

    # Evidence pack scoring
    combined_text = " ".join(
        [caption_text, cta_text]
        + [slide["title"] for slide in normalized_slides]
        + [slide["copy"] for slide in normalized_slides]
    )
    # Use last non-CTA slide as the "proof anchor" — not necessarily penultimate
    proof_slides = [s for s in normalized_slides if s["slide_type"] not in ("CTA", "CAPA", "HOOK")]
    proof_text = " ".join(
        str(v) for slide in proof_slides[-2:] for v in slide.values()
    ) if proof_slides else ""

    numeric_hits = _find_hits(combined_text, evidence_pack.numeric_fragments, min_chars=2)
    source_hits = _find_hits(combined_text, evidence_pack.source_labels, min_chars=3)
    proof_hits = _find_hits(proof_text, evidence_pack.numeric_fragments + evidence_pack.source_labels, min_chars=2)
    claim_hits = _find_token_overlap_hits(combined_text, evidence_pack.allowed_claims, min_overlap=2)
    term_hits = _find_token_overlap_hits(combined_text, evidence_pack.required_terms, min_overlap=1)

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
            strengths.append("argumento ancorado em evidencia concreta")
        else:
            issues.append("slide de prova sem ancora tecnica forte")
    else:
        if len(proof_text.split()) >= 8:
            score += 0.06
            strengths.append("argumento detalhado mesmo sem catalogo rico")
        else:
            issues.append("argumento raso demais")

    if evidence_pack.source_labels:
        if source_hits:
            score += 0.08
            strengths.append("fonte ou origem da evidencia apareceu")
        else:
            issues.append("faltou citar a fonte/origem disponivel no catalogo")
    else:
        score += 0.05

    if evidence_pack.allowed_claims:
        needed_claim_hits = 2 if len(evidence_pack.allowed_claims) >= 3 else 1
        if len(claim_hits) >= needed_claim_hits and causal_hits >= 1:
            score += 0.10
            strengths.append("cadeia causal do material-base preservada")
        elif len(evidence_pack.allowed_claims) >= 3 and (len(claim_hits) < needed_claim_hits or causal_hits == 0):
            issues.append("o texto perdeu a cadeia causal do material-base e virou abstracao generica")
    else:
        score += 0.04

    if evidence_pack.required_terms:
        needed_term_hits = 2 if len(evidence_pack.required_terms) >= 4 else 1
        if len(term_hits) >= needed_term_hits:
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
            "distinct_middle_types": len(set(s["slide_type"] for s in middle_slides)) if middle_slides else 0,
            "numeric_hits": len(numeric_hits),
            "source_hits": len(source_hits),
            "proof_hits": len(proof_hits),
            "claim_hits": len(claim_hits),
            "term_hits": len(term_hits),
            "practical_hits": practical_hits,
            "creative_tension_hits": creative_tension_hits,
            "causal_hits": causal_hits,
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
            f"tipos_distintos={metrics.get('distinct_middle_types')}, "
            f"hits_numericos={metrics.get('numeric_hits')}, "
            f"hits_fontes={metrics.get('source_hits')}, "
            f"hits_prova={metrics.get('proof_hits')}, "
            f"hits_claims={metrics.get('claim_hits')}, "
            f"hits_causais={metrics.get('causal_hits')}"
        )
    return "\n".join(lines)
