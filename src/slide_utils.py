from typing import Any, Optional


_SLIDE_TYPE_ALIASES = {
    # Fixed anchor types
    "CAPA": "CAPA",
    "COVER": "CAPA",
    "ABERTURA": "CAPA",
    "HOOK": "HOOK",
    "GANCHO": "HOOK",
    "CTA": "CTA",
    "FECHAMENTO": "CTA",
    "ENCERRAMENTO": "CTA",
    # Narrative middle types — preserved as-is
    "MODELO": "MODELO",
    "ESCALADA": "ESCALADA",
    "DADO": "DADO",
    "DADOS": "DADO",
    "DADOS_HISTORICOS": "DADOS_HISTORICOS",
    "CURVA": "DADOS_HISTORICOS",
    "MECANISMO": "MECANISMO",
    "REVELACAO": "REVELACAO",
    "REVELAÇÃO": "REVELACAO",
    "CASO_HUMANO": "CASO_HUMANO",
    "CASO": "CASO_HUMANO",
    "CONSEQUENCIA": "CONSEQUENCIA",
    "CONSEQUÊNCIA": "CONSEQUENCIA",
    "RESPIRO": "RESPIRO",
    "HUMOR": "RESPIRO",
    "POLITICA": "POLITICA",
    "POLÍTICA": "POLITICA",
    "SINTESE": "SINTESE",
    "SÍNTESE": "SINTESE",
    # Legacy types — mapped to closest narrative equivalent
    "PROVA": "DADO",
    "PROOF": "DADO",
    "EXEMPLO": "DADO",
    "DESENVOLVIMENTO": "MECANISMO",
    "CONTEUDO": "MECANISMO",
    "CONTENT": "MECANISMO",
    "EXPLICACAO": "MECANISMO",
}

_MIDDLE_TYPES = {
    "MODELO", "ESCALADA", "DADO", "DADOS_HISTORICOS", "MECANISMO",
    "REVELACAO", "CASO_HUMANO", "CONSEQUENCIA", "RESPIRO", "POLITICA",
    "SINTESE", "DESENVOLVIMENTO",
}


def _as_text(value: Any) -> str:
    return str(value or "").strip()


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_slide_type(raw_type: Any, index: int, total: int) -> str:
    normalized = _as_text(raw_type).upper()
    if normalized in _SLIDE_TYPE_ALIASES:
        return _SLIDE_TYPE_ALIASES[normalized]
    # Position-based fallbacks only for anchor slots
    if index == 0:
        return "CAPA"
    if index == 1:
        return "HOOK"
    if total > 0 and index == total - 1:
        return "CTA"
    return "MECANISMO"


def normalize_carousel_slides(slides: Any) -> list[dict[str, Any]]:
    raw_slides = slides if isinstance(slides, list) else []
    total = len(raw_slides)
    normalized: list[dict[str, Any]] = []

    for index, raw_slide in enumerate(raw_slides):
        slide = raw_slide if isinstance(raw_slide, dict) else {}
        normalized.append(
            {
                "slide_number": _as_int(slide.get("slide_number"), index + 1),
                "slide_type": normalize_slide_type(slide.get("slide_type"), index, total),
                "title": _as_text(slide.get("title")),
                "copy": _as_text(slide.get("copy")),
                "cta": _as_text(slide.get("cta")),
            }
        )

    return normalized


def extract_carousel_hook(slides: Any) -> Optional[str]:
    normalized = normalize_carousel_slides(slides)
    for target_type in ("HOOK", "CAPA"):
        for slide in normalized:
            if slide["slide_type"] != target_type:
                continue
            if slide["title"]:
                return slide["title"]
            if slide["copy"]:
                return slide["copy"]
    return None


def extract_carousel_cta(slides: Any) -> Optional[str]:
    normalized = normalize_carousel_slides(slides)
    for slide in reversed(normalized):
        if slide["cta"]:
            return slide["cta"]
    for slide in reversed(normalized):
        if slide["slide_type"] != "CTA":
            continue
        if slide["title"]:
            return slide["title"]
        if slide["copy"]:
            return slide["copy"]
    return None
