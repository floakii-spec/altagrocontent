# tests/test_pledge_validator.py
import pytest
from src.generator.pledge_validator import (
    validate_pledge_coverage,
    validate_pledge_traceability,
    validate_pledge_slide_bounds,
    validate_pledge_fulfillment,
    validate_number_context,
)

_INVENTORY = {
    "required": {
        "numbers": ["R$ 2,5bi", "R$ 427mi"],
        "mechanisms": ["recuperação judicial", "patrimônio líquido negativo"],
        "causal_steps": [
            "Textor compra SAF em 2022 com promessa de capital externo",
            "Clube ganha Libertadores em novembro de 2024",
            "Capital prometido não chegou",
        ],
        "definitions": [
            {"term": "recuperação judicial", "definition": "proteção temporária contra credores"},
        ],
    },
    "optional": {"claims": [], "sources": [], "context": ""},
}

_GOOD_PLEDGES = [
    {"item_type": "numero", "item": "R$ 2,5bi", "slide_number": 3, "como_vai_aparecer": "custo de safra"},
    {"item_type": "numero", "item": "R$ 427mi", "slide_number": 4, "como_vai_aparecer": "patrimônio"},
    {"item_type": "mecanismo", "item": "recuperação judicial", "slide_number": 5, "como_vai_aparecer": "renegociação"},
    {"item_type": "mecanismo", "item": "patrimônio líquido negativo", "slide_number": 4, "como_vai_aparecer": "ativo < passivo"},
    {"item_type": "cadeia_causal", "item": "Textor compra SAF em 2022 com promessa capital externo", "slide_number": 2, "como_vai_aparecer": "investidor promete crédito"},
    {"item_type": "cadeia_causal", "item": "Clube ganha Libertadores novembro 2024", "slide_number": 3, "como_vai_aparecer": "aparente sucesso"},
    {"item_type": "cadeia_causal", "item": "Capital prometido não chegou produtor sem recurso", "slide_number": 5, "como_vai_aparecer": "crédito não saiu"},
    {"item_type": "definicao", "item": "recuperação judicial", "slide_number": 7, "como_vai_aparecer": "proteção, não falência"},
]

_SLIDES_5 = [
    {"slide_number": 1, "slide_type": "CAPA", "title": "Título", "copy": "texto"},
    {"slide_number": 2, "slide_type": "HOOK", "title": "Hook", "copy": "Textor comprou SAF em 2022 com promessa capital externo"},
    {"slide_number": 3, "slide_type": "DADO", "title": "Dado", "copy": "R$ 2,5bi em passivos acumulados — equivale a 3 safras"},
    {"slide_number": 4, "slide_type": "MECANISMO", "title": "Mecanismo", "copy": "patrimônio líquido negativo: R$ 427mi a mais em dívidas do que ativos"},
    {"slide_number": 5, "slide_type": "CTA", "title": "CTA", "copy": "recuperação judicial: proteção temporária, não falência. Capital não chegou.", "cta": "Saiba mais"},
]


# --- validate_pledge_coverage ---

def test_coverage_passes_when_all_required_covered():
    issues = validate_pledge_coverage(_GOOD_PLEDGES, _INVENTORY)
    assert issues == []

def test_coverage_fails_when_number_missing():
    pledges = [p for p in _GOOD_PLEDGES if p["item"] != "R$ 427mi"]
    issues = validate_pledge_coverage(pledges, _INVENTORY)
    assert any("R$ 427mi" in i for i in issues)

def test_coverage_fails_when_mechanism_missing():
    pledges = [p for p in _GOOD_PLEDGES if p["item"] != "patrimônio líquido negativo"]
    issues = validate_pledge_coverage(pledges, _INVENTORY)
    assert any("patrimônio líquido negativo" in i for i in issues)

def test_coverage_requires_min_causal_steps():
    # Only 1 causal step pledged, min is max(1, floor(3*0.7)) = 2
    pledges = [p for p in _GOOD_PLEDGES if p["item_type"] != "cadeia_causal"]
    pledges.append({"item_type": "cadeia_causal", "item": "Textor compra SAF 2022", "slide_number": 2, "como_vai_aparecer": "x"})
    issues = validate_pledge_coverage(pledges, _INVENTORY)
    assert any("cadeia causal" in i for i in issues)

def test_coverage_empty_inventory_returns_no_issues():
    issues = validate_pledge_coverage([], {})
    assert issues == []

def test_coverage_skips_optional_fields():
    issues = validate_pledge_coverage(_GOOD_PLEDGES, _INVENTORY)
    assert not any("claims" in i or "sources" in i for i in issues)


# --- validate_pledge_traceability ---

def test_traceability_passes_for_valid_pledges():
    issues = validate_pledge_traceability(_GOOD_PLEDGES, _INVENTORY)
    assert issues == []

def test_traceability_fails_for_invented_number():
    bad_pledge = {"item_type": "numero", "item": "R$ 999bi", "slide_number": 2, "como_vai_aparecer": "x"}
    issues = validate_pledge_traceability([bad_pledge], _INVENTORY)
    assert any("R$ 999bi" in i for i in issues)

def test_traceability_fails_for_invented_mechanism():
    bad_pledge = {"item_type": "mecanismo", "item": "mercado futuro", "slide_number": 3, "como_vai_aparecer": "x"}
    issues = validate_pledge_traceability([bad_pledge], _INVENTORY)
    assert any("mercado futuro" in i for i in issues)

def test_traceability_fails_for_invented_definition():
    bad_pledge = {"item_type": "definicao", "item": "hedge cambial", "slide_number": 5, "como_vai_aparecer": "x"}
    issues = validate_pledge_traceability([bad_pledge], _INVENTORY)
    assert any("hedge cambial" in i for i in issues)


# --- validate_pledge_slide_bounds ---

def test_slide_bounds_passes_for_valid_slide_numbers():
    issues = validate_pledge_slide_bounds(_GOOD_PLEDGES[:3], _SLIDES_5)
    assert issues == []

def test_slide_bounds_fails_for_out_of_range():
    bad = {"item_type": "numero", "item": "R$ 2,5bi", "slide_number": 99, "como_vai_aparecer": "x"}
    issues = validate_pledge_slide_bounds([bad], _SLIDES_5)
    assert any("99" in i for i in issues)

def test_slide_bounds_fails_for_zero():
    bad = {"item_type": "numero", "item": "R$ 2,5bi", "slide_number": 0, "como_vai_aparecer": "x"}
    issues = validate_pledge_slide_bounds([bad], _SLIDES_5)
    assert issues  # slide_number 0 is out of [1, 5]

def test_slide_bounds_fails_for_missing_slide_number():
    bad = {"item_type": "numero", "item": "R$ 2,5bi", "como_vai_aparecer": "x"}
    issues = validate_pledge_slide_bounds([bad], _SLIDES_5)
    assert any("sem slide_number" in i for i in issues)


# --- validate_pledge_fulfillment ---

def test_fulfillment_passes_when_numbers_present():
    pledges = [{"item_type": "numero", "item": "R$ 2,5bi", "slide_number": 3, "como_vai_aparecer": "x"}]
    issues = validate_pledge_fulfillment(pledges, _SLIDES_5, "legenda", "cta")
    assert issues == []

def test_fulfillment_fails_when_number_absent():
    pledges = [{"item_type": "numero", "item": "R$ 99bi", "slide_number": 3, "como_vai_aparecer": "x"}]
    issues = validate_pledge_fulfillment(pledges, _SLIDES_5, "legenda", "cta")
    assert any("R$ 99bi" in i for i in issues)

def test_fulfillment_passes_when_mechanism_present():
    pledges = [{"item_type": "mecanismo", "item": "recuperação judicial", "slide_number": 5, "como_vai_aparecer": "x"}]
    issues = validate_pledge_fulfillment(pledges, _SLIDES_5, "legenda", "cta")
    assert issues == []

def test_fulfillment_passes_for_definition_with_marker():
    slides = [
        {"slide_number": 1, "slide_type": "CAPA", "title": "T", "copy": "texto"},
        {"slide_number": 2, "slide_type": "HOOK", "title": "T", "copy": "recuperação judicial significa proteção temporária"},
        {"slide_number": 3, "slide_type": "CTA", "title": "T", "copy": "x", "cta": "x"},
    ]
    pledges = [{"item_type": "definicao", "item": "recuperação judicial", "slide_number": 2, "como_vai_aparecer": "x"}]
    issues = validate_pledge_fulfillment(pledges, slides, "", "")
    assert not any("bloqueante" in i or "ausente" in i for i in issues if "definição" in i)

def test_fulfillment_causal_step_key_term_found():
    pledges = [{"item_type": "cadeia_causal", "item": "Textor compra SAF com capital externo", "slide_number": 2, "como_vai_aparecer": "x"}]
    issues = validate_pledge_fulfillment(pledges, _SLIDES_5, "legenda", "cta")
    assert issues == []  # "Textor" and "capital" appear in slide 2


# --- validate_number_context ---

def test_number_context_passes_when_mechanism_nearby():
    # "R$ 2,5bi" appears in slide 3 copy near "passivos" (mechanism)
    inventory = {
        "required": {
            "numbers": ["R$ 2,5bi"],
            "mechanisms": ["passivos", "recuperação"],
            "causal_steps": [],
            "definitions": [],
        }
    }
    pledges = [{"item_type": "numero", "item": "R$ 2,5bi", "slide_number": 3, "como_vai_aparecer": "x"}]
    issues = validate_number_context(pledges, _SLIDES_5, inventory)
    assert issues == []

def test_number_context_fails_when_no_context_term_nearby():
    slides = [
        {"slide_number": 1, "slide_type": "CAPA", "title": "T", "copy": "lucro cresceu R$ 2,5bi este ano feliz"},
    ]
    inventory = {
        "required": {
            "numbers": ["R$ 2,5bi"],
            "mechanisms": ["passivos", "dívida", "recuperação"],
            "causal_steps": [],
            "definitions": [],
        }
    }
    pledges = [{"item_type": "numero", "item": "R$ 2,5bi", "slide_number": 1, "como_vai_aparecer": "x"}]
    issues = validate_number_context(pledges, slides, inventory)
    assert any("contexto semântico" in i for i in issues)
