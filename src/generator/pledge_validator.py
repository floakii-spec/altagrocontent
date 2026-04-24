# src/generator/pledge_validator.py
from __future__ import annotations

import re
from typing import Any

_DEFINITIONAL_MARKERS = (
    "significa",
    "não é",
    "≠",
    "em outras palavras",
    "na prática",
    "é o mesmo que",
    "quer dizer",
)


def validate_pledge_coverage(
    dados_prometidos: list[dict[str, Any]],
    inventory: dict[str, Any],
) -> list[str]:
    """Checks that all required inventory items have at least one pledge entry."""
    if not inventory:
        return []

    required = inventory.get("required", {})
    issues: list[str] = []

    pledged_items_lower = [str(p.get("item", "")).lower() for p in dados_prometidos]

    for number in required.get("numbers") or []:
        num_lower = str(number).lower()
        if not any(num_lower in t for t in pledged_items_lower):
            issues.append(f"pledge incompleto — número '{number}' do inventário sem compromisso")

    for mech in required.get("mechanisms") or []:
        mech_lower = str(mech).lower()
        if not any(mech_lower in t for t in pledged_items_lower):
            issues.append(f"pledge incompleto — mecanismo '{mech}' do inventário sem compromisso")

    steps = required.get("causal_steps") or []
    if steps:
        min_covered = max(1, int(len(steps) * 0.7))
        causal_pledges = [p for p in dados_prometidos if p.get("item_type") == "cadeia_causal"]
        covered = 0
        for step in steps:
            step_words = {w.lower() for w in re.findall(r"\b\w{4,}\b", step)}
            for pledge in causal_pledges:
                pledge_words = {w.lower() for w in re.findall(r"\b\w{4,}\b", str(pledge.get("item", "")))}
                if len(step_words & pledge_words) >= 2:
                    covered += 1
                    break
        if covered < min_covered:
            issues.append(
                f"pledge incompleto — cadeia causal cobre {covered}/{len(steps)} passos (mínimo: {min_covered})"
            )

    defs = required.get("definitions") or []
    if defs:
        def_pledges = [p for p in dados_prometidos if p.get("item_type") == "definicao"]
        if not def_pledges:
            issues.append("pledge incompleto — nenhuma definição do inventário representada no pledge")

    return issues


def validate_pledge_traceability(
    dados_prometidos: list[dict[str, Any]],
    inventory: dict[str, Any],
) -> list[str]:
    """Checks that each pledge item traces back to the inventory."""
    if not inventory:
        return []

    required = inventory.get("required", {})
    issues: list[str] = []

    numbers_lower = [str(n).lower() for n in (required.get("numbers") or [])]
    mechs_lower = [str(m).lower() for m in (required.get("mechanisms") or [])]
    steps = [str(s) for s in (required.get("causal_steps") or [])]
    def_terms_lower = [str(d.get("term", "")).lower() for d in (required.get("definitions") or []) if isinstance(d, dict)]

    for pledge in dados_prometidos:
        item_type = pledge.get("item_type", "")
        item = str(pledge.get("item", "")).strip()
        if not item:
            continue

        if item_type == "numero":
            item_lower = item.lower()
            if not any(item_lower in n or n in item_lower for n in numbers_lower):
                issues.append(f"pledge inválido — número '{item}' não rastreia ao inventário")

        elif item_type == "mecanismo":
            item_lower = item.lower()
            if not any(item_lower in m or m in item_lower for m in mechs_lower):
                issues.append(f"pledge inválido — mecanismo '{item}' não rastreia ao inventário")

        elif item_type == "cadeia_causal":
            item_words = {w.lower() for w in re.findall(r"\b\w{4,}\b", item)}
            found = any(
                len(item_words & {w.lower() for w in re.findall(r"\b\w{4,}\b", step)}) >= 2
                for step in steps
            )
            if not found and steps:
                issues.append(f"pledge inválido — item de cadeia causal '{item[:60]}' não rastreia ao inventário")

        elif item_type == "definicao":
            item_lower = item.lower()
            if not any(item_lower in t or t in item_lower for t in def_terms_lower):
                issues.append(f"pledge inválido — definição '{item}' não rastreia ao inventário")

    return issues


def validate_pledge_slide_bounds(
    dados_prometidos: list[dict[str, Any]],
    slides: list[dict[str, Any]],
) -> list[str]:
    """Checks that each slide_number in the pledge exists in the carousel (1-based)."""
    issues: list[str] = []
    n = len(slides)

    for pledge in dados_prometidos:
        item = str(pledge.get("item", ""))[:60]
        slide_number = pledge.get("slide_number")

        if slide_number is None:
            issues.append(f"pledge inválido — item '{item}' sem slide_number")
            continue

        try:
            sn = int(slide_number)
        except (TypeError, ValueError):
            issues.append(f"pledge inválido — slide_number '{slide_number}' não é inteiro para item '{item}'")
            continue

        if not (1 <= sn <= n):
            issues.append(f"pledge inválido — slide_number {sn} fora do range [1, {n}] para item '{item}'")

    return issues


def _slides_window_text(
    slides: list[dict[str, Any]],
    caption: str,
    cta: str,
    target_slide_number: int,
    window: int,
) -> str:
    n = len(slides)
    start = max(0, target_slide_number - 1 - window)
    end = min(n, target_slide_number + window)
    parts = [slides[i].get("title", "") + " " + slides[i].get("copy", "") for i in range(start, end)]
    parts += [caption, cta]
    return " ".join(parts)


def _full_text(slides: list[dict[str, Any]], caption: str, cta: str) -> str:
    parts = [caption, cta]
    for s in slides:
        parts.append(s.get("title", ""))
        parts.append(s.get("copy", ""))
    return " ".join(parts)


def validate_pledge_fulfillment(
    dados_prometidos: list[dict[str, Any]],
    slides: list[dict[str, Any]],
    caption: str,
    cta: str,
) -> list[str]:
    """Checks that each pledged item appears in the generated content."""
    issues: list[str] = []
    full = _full_text(slides, caption, cta)

    for pledge in dados_prometidos:
        item_type = pledge.get("item_type", "")
        item = str(pledge.get("item", "")).strip()
        slide_number = pledge.get("slide_number")
        if not item or slide_number is None:
            continue
        try:
            sn = int(slide_number)
        except (TypeError, ValueError):
            continue

        if item_type == "numero":
            near = _slides_window_text(slides, caption, cta, sn, window=1)
            if item not in near and item not in full:
                issues.append(f"pledge violado — número '{item}' prometido mas ausente no texto final")

        elif item_type == "mecanismo":
            near = _slides_window_text(slides, caption, cta, sn, window=1)
            if item.lower() not in near.lower() and item.lower() not in full.lower():
                issues.append(f"pledge violado — mecanismo '{item}' prometido mas ausente no texto final")

        elif item_type == "cadeia_causal":
            key_words = [w for w in re.findall(r"\b\w{5,}\b", item)][:3]
            if not key_words:
                continue
            near = _slides_window_text(slides, caption, cta, sn, window=2)
            if not any(w.lower() in near.lower() for w in key_words):
                if not any(w.lower() in full.lower() for w in key_words):
                    issues.append(
                        f"pledge violado — passo de cadeia causal '{item[:60]}' sem rastro no texto final"
                    )

        elif item_type == "definicao":
            near = _slides_window_text(slides, caption, cta, sn, window=1)
            if not any(marker in near.lower() for marker in _DEFINITIONAL_MARKERS):
                issues.append(
                    f"pledge violado (revisão) — definição de '{item}' sem estrutura definitória no slide {sn}"
                )

    return issues


def validate_number_context(
    dados_prometidos: list[dict[str, Any]],
    slides: list[dict[str, Any]],
    inventory: dict[str, Any],
) -> list[str]:
    """Checks that pledged numbers appear with correct semantic context (not inverted)."""
    if not inventory:
        return []

    required = inventory.get("required", {})
    mechs_lower = {
        word.lower()
        for mech in (required.get("mechanisms") or [])
        for word in re.findall(r"\b\w{4,}\b", str(mech))
    }
    causal_words = {
        w.lower()
        for step in (required.get("causal_steps") or [])
        for w in re.findall(r"\b\w{5,}\b", str(step))
    }
    context_terms = mechs_lower | causal_words

    full_slide_text = " ".join(
        s.get("title", "") + " " + s.get("copy", "") for s in slides
    )
    full_lower = full_slide_text.lower()
    issues: list[str] = []

    for pledge in dados_prometidos:
        if pledge.get("item_type") != "numero":
            continue
        number = str(pledge.get("item", "")).strip()
        if not number or number not in full_slide_text:
            continue

        number_lower = number.lower()
        pos = full_lower.find(number_lower)
        if pos == -1:
            continue

        # Extract a character window of ~60 chars each side around the number
        window_start = max(0, pos - 60)
        window_end = min(len(full_lower), pos + len(number_lower) + 60)
        window_text = full_lower[window_start:window_end]
        window_words = set(re.findall(r"\w+", window_text))

        found_context = bool(window_words & context_terms)

        if not found_context:
            issues.append(
                f"pledge violado — número '{number}' presente mas contexto semântico ausente "
                f"(possível inversão ou uso sem âncora)"
            )

    return issues
