from typing import Any, Optional


_SLIDE_TYPE_ALIASES = {
    "CAPA": "CAPA",
    "COVER": "CAPA",
    "ABERTURA": "CAPA",
    "HOOK": "HOOK",
    "GANCHO": "HOOK",
    "PROVA": "PROVA",
    "PROOF": "PROVA",
    "EXEMPLO": "PROVA",
    "DESENVOLVIMENTO": "DESENVOLVIMENTO",
    "CONTEUDO": "DESENVOLVIMENTO",
    "CONTENT": "DESENVOLVIMENTO",
    "EXPLICACAO": "DESENVOLVIMENTO",
    "CTA": "CTA",
    "FECHAMENTO": "CTA",
    "ENCERRAMENTO": "CTA",
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
    if index == 0:
        return "CAPA"
    if index == 1:
        return "HOOK"
    if total > 3 and index == total - 2:
        return "PROVA"
    if total > 0 and index == total - 1:
        return "CTA"
    return "DESENVOLVIMENTO"


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
