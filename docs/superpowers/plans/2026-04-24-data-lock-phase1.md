# Data Lock + Pledge + Validation Gate — Fase 1

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Garantir que todos os dados críticos (números, mecanismos, cadeia causal, definições) de um post-fonte sobrevivem intactos até o post gerado pelo Studio, usando um inventário travado + pledge pré-escrita + gate de validação em cinco camadas.

**Architecture:** `PostIntelligence.evidence_inventory` é extraído no pipeline de análise (GPT call sobre visual_transcript). No momento da geração, `generate_post()` tira um snapshot imutável em `GeneratedPost.source_data_inventory`. O modelo deve comprometer-se em `dados_prometidos` (dentro do `planejamento_narrativo`) a usar cada item `required` antes de escrever slides; cinco funções de validação auditam cobertura, rastreabilidade, bounds, fulfillment e contexto semântico.

**Tech Stack:** Python 3.11, SQLAlchemy 2.0 mapped_column, Alembic, OpenAI GPT-4o, pytest

---

## File Map

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `alembic/versions/011_evidence_inventory.py` | Criar | Migração: 2 novas colunas JSON |
| `src/models.py` | Modificar | Campos `evidence_inventory` e `source_data_inventory` |
| `src/analyzer/post_intelligence.py` | Modificar | `_extract_evidence_inventory()` + wiring |
| `src/generator/pledge_validator.py` | Criar | 5 funções de validação — sem dependências externas |
| `src/generator/content_generator.py` | Modificar | Pledge no SYSTEM_PROMPT, snapshot, wiring dos validators |
| `tests/test_pledge_validator.py` | Criar | Testes unitários dos 5 validators |
| `tests/test_post_intelligence_evidence.py` | Criar | Testes de extração do evidence_inventory |
| `tests/test_content_generator.py` | Modificar | Testes de snapshot e integração do gate |

---

## Task 1: Migration 011

**Files:**
- Create: `alembic/versions/011_evidence_inventory.py`

- [ ] **Step 1: Criar o arquivo de migração**

```python
# alembic/versions/011_evidence_inventory.py
"""add evidence_inventory to post_intelligence and source_data_inventory to generated_posts

Revision ID: 011
Revises: 010
Create Date: 2026-04-24 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "post_intelligence",
        sa.Column("evidence_inventory", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )
    op.add_column(
        "generated_posts",
        sa.Column("source_data_inventory", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )


def downgrade() -> None:
    op.drop_column("post_intelligence", "evidence_inventory")
    op.drop_column("generated_posts", "source_data_inventory")
```

- [ ] **Step 2: Aplicar a migração localmente**

```bash
cd /Users/floakii/Claudio/agro-content
alembic upgrade head
```

Expected: `Running upgrade 010 -> 011, add evidence_inventory...`

- [ ] **Step 3: Commit**

```bash
git add alembic/versions/011_evidence_inventory.py
git commit -m "feat: migration 011 — evidence_inventory + source_data_inventory columns"
```

---

## Task 2: Model Fields

**Files:**
- Modify: `src/models.py`

- [ ] **Step 1: Adicionar campos aos dois models**

Em `src/models.py`, localize a classe `PostIntelligence` (linha ~157) e adicione após `carousel_complexity`:

```python
# src/models.py — dentro de PostIntelligence, após carousel_complexity
evidence_inventory: Mapped[dict] = mapped_column(JSON, default=dict)
```

Localize a classe `GeneratedPost` (linha ~82) e adicione após `planning_narrative`:

```python
# src/models.py — dentro de GeneratedPost, após planning_narrative
source_data_inventory: Mapped[dict] = mapped_column(JSON, default=dict)
```

- [ ] **Step 2: Verificar que os imports existentes cobrem JSON**

`JSON` já está importado em `src/models.py` (usado por `planning_narrative`). Sem mudança de imports necessária.

- [ ] **Step 3: Teste rápido de modelo**

```python
# tests/test_models.py — adicionar ao arquivo existente
def test_post_intelligence_has_evidence_inventory_field():
    intel = PostIntelligence(post_id=1)
    assert hasattr(intel, "evidence_inventory")
    assert intel.evidence_inventory == {}

def test_generated_post_has_source_data_inventory_field():
    gp = GeneratedPost()
    assert hasattr(gp, "source_data_inventory")
    assert gp.source_data_inventory == {}
```

Run: `pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/models.py tests/test_models.py
git commit -m "feat: add evidence_inventory to PostIntelligence, source_data_inventory to GeneratedPost"
```

---

## Task 3: Evidence Extractor

**Files:**
- Modify: `src/analyzer/post_intelligence.py`
- Create: `tests/test_post_intelligence_evidence.py`

- [ ] **Step 1: Escrever os testes unitários**

```python
# tests/test_post_intelligence_evidence.py
from unittest.mock import MagicMock, patch

from src.analyzer.post_intelligence import _extract_evidence_inventory


def _mock_gpt_response(content: str):
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


_SAMPLE_DATA = {
    "technical_claims": ["patrimônio líquido negativo em R$ 427 milhões", "SAF acumulou R$ 2,5bi em passivos"],
    "data_points": [
        {"value": "R$ 2,5bi", "context": "passivos totais", "source": None},
        {"value": "R$ 427mi", "context": "patrimônio negativo", "source": None},
    ],
    "sources_referenced": ["BDO", "Demonstrações Contábeis SAF"],
    "core_argument": "modelo dependia de capital externo que nunca chegou",
}

_SAMPLE_GPT_JSON = """{
  "mechanisms": ["recuperação judicial", "patrimônio líquido negativo"],
  "causal_steps": [
    "Textor compra SAF em 2022",
    "Clube ganha Libertadores em novembro de 2024",
    "Capital prometido não chegou"
  ],
  "definitions": [
    {"term": "recuperação judicial", "definition": "proteção temporária contra credores"}
  ]
}"""


def test_extract_evidence_inventory_required_numbers():
    with patch("src.analyzer.post_intelligence.openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_gpt_response(_SAMPLE_GPT_JSON)
        result = _extract_evidence_inventory("Slide 1: conteúdo", _SAMPLE_DATA, "legenda")
    assert "R$ 2,5bi" in result["required"]["numbers"]
    assert "R$ 427mi" in result["required"]["numbers"]


def test_extract_evidence_inventory_required_mechanisms():
    with patch("src.analyzer.post_intelligence.openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_gpt_response(_SAMPLE_GPT_JSON)
        result = _extract_evidence_inventory("Slide 1", _SAMPLE_DATA, "legenda")
    assert "recuperação judicial" in result["required"]["mechanisms"]
    assert "patrimônio líquido negativo" in result["required"]["mechanisms"]


def test_extract_evidence_inventory_causal_steps():
    with patch("src.analyzer.post_intelligence.openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_gpt_response(_SAMPLE_GPT_JSON)
        result = _extract_evidence_inventory("Slide 1", _SAMPLE_DATA, "legenda")
    assert len(result["required"]["causal_steps"]) == 3
    assert "Textor compra SAF em 2022" in result["required"]["causal_steps"]


def test_extract_evidence_inventory_definitions():
    with patch("src.analyzer.post_intelligence.openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_gpt_response(_SAMPLE_GPT_JSON)
        result = _extract_evidence_inventory("Slide 1", _SAMPLE_DATA, "legenda")
    assert result["required"]["definitions"][0]["term"] == "recuperação judicial"


def test_extract_evidence_inventory_optional_fields():
    with patch("src.analyzer.post_intelligence.openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_gpt_response(_SAMPLE_GPT_JSON)
        result = _extract_evidence_inventory("Slide 1", _SAMPLE_DATA, "legenda")
    assert "BDO" in result["optional"]["sources"]
    assert result["optional"]["context"] == "modelo dependia de capital externo que nunca chegou"


def test_extract_evidence_inventory_gpt_failure_returns_partial():
    with patch("src.analyzer.post_intelligence.openai_client") as mock_client:
        mock_client.chat.completions.create.side_effect = Exception("timeout")
        result = _extract_evidence_inventory("Slide 1", _SAMPLE_DATA, "legenda")
    # numbers still extracted from data_points even if GPT fails
    assert "R$ 2,5bi" in result["required"]["numbers"]
    assert result["required"]["causal_steps"] == []
    assert result["required"]["definitions"] == []
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_post_intelligence_evidence.py -v
```

Expected: `ImportError` ou `AttributeError` — `_extract_evidence_inventory` ainda não existe.

- [ ] **Step 3: Implementar `_EVIDENCE_PROMPT` e `_extract_evidence_inventory`**

Em `src/analyzer/post_intelligence.py`, adicione após as constantes existentes (`_VISION_PROMPT`, `_SYSTEM_PROMPT`):

```python
# src/analyzer/post_intelligence.py — após _SYSTEM_PROMPT
import re as _re

_EVIDENCE_PROMPT = """Analise o conteúdo do post abaixo e extraia o inventário de evidências.

Retorne APENAS um JSON com esta estrutura:
{
  "mechanisms": ["<termo ou conceito-chave central ao argumento, ex: 'recuperação judicial'>"],
  "causal_steps": ["<passo 1 da cadeia lógica>", "<passo 2>"],
  "definitions": [
    {"term": "<termo técnico>", "definition": "<como o post define em linguagem simples>"}
  ]
}

- "mechanisms": máximo 8 termos curtos (2-4 palavras) que são conceitos centrais do argumento.
- "causal_steps": 3-8 eventos em ordem lógica que constroem o argumento. Lista vazia se não houver cadeia causal.
- "definitions": termos que o post explica explicitamente. Lista vazia se não houver.
Responda APENAS com o JSON."""


def _extract_evidence_inventory(
    visual_transcript: str,
    data: dict,
    caption: str,
) -> dict:
    # Extract numbers from data_points
    numbers: list[str] = []
    seen_numbers: set[str] = set()
    for point in data.get("data_points") or []:
        if isinstance(point, dict):
            value = str(point.get("value", "")).strip()
            if value and value not in seen_numbers:
                seen_numbers.add(value)
                numbers.append(value)
    for claim in data.get("technical_claims") or []:
        if not isinstance(claim, str):
            continue
        for match in _re.findall(r"R\$\s*[\d.,]+(?:\s*(?:bi|mi|mil|bilh[õo]es|milh[õo]es))?|\d+[.,]?\d*%", claim):
            if match not in seen_numbers:
                seen_numbers.add(match)
                numbers.append(match)

    # Call GPT for mechanisms, causal_steps, definitions
    mechanisms: list[str] = []
    causal_steps: list[str] = []
    definitions: list[dict] = []

    content_parts = []
    if visual_transcript:
        content_parts.append(f"Conteúdo visual:\n{visual_transcript}")
    if caption:
        content_parts.append(f"Legenda: {caption}")
    content = "\n\n".join(content_parts)

    if content.strip():
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": _EVIDENCE_PROMPT},
                    {"role": "user", "content": content[:6000]},
                ],
                max_tokens=600,
            )
            raw = (response.choices[0].message.content or "").strip()
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.rstrip("`").strip()
            evidence_data = json.loads(raw)
            mechanisms = [str(m).strip() for m in evidence_data.get("mechanisms") or [] if str(m).strip()]
            causal_steps = [str(s).strip() for s in evidence_data.get("causal_steps") or [] if str(s).strip()]
            definitions = [
                d for d in (evidence_data.get("definitions") or [])
                if isinstance(d, dict) and d.get("term") and d.get("definition")
            ]
        except Exception as exc:
            logger.warning("Evidence inventory GPT extraction failed for post: %s", exc)

    return {
        "required": {
            "numbers": numbers,
            "mechanisms": mechanisms,
            "causal_steps": causal_steps,
            "definitions": definitions,
        },
        "optional": {
            "claims": [c.strip() for c in (data.get("technical_claims") or []) if isinstance(c, str) and c.strip()],
            "sources": [str(s).strip() for s in (data.get("sources_referenced") or []) if str(s).strip()],
            "context": data.get("core_argument") or "",
        },
    }
```

- [ ] **Step 4: Rodar os testes**

```bash
pytest tests/test_post_intelligence_evidence.py -v
```

Expected: todos PASS.

- [ ] **Step 5: Commit**

```bash
git add src/analyzer/post_intelligence.py tests/test_post_intelligence_evidence.py
git commit -m "feat: add _extract_evidence_inventory to post_intelligence analyzer"
```

---

## Task 4: Wire Evidence Extraction into `analyze_post_intelligence()`

**Files:**
- Modify: `src/analyzer/post_intelligence.py`

- [ ] **Step 1: Escrever teste de integração**

```python
# tests/test_post_intelligence_evidence.py — adicionar ao final do arquivo
def test_analyze_post_intelligence_populates_evidence_inventory(db_session, competitor_post):
    """evidence_inventory deve ser populado ao final de analyze_post_intelligence."""
    with patch("src.analyzer.post_intelligence.openai_client") as mock_client:
        # First call: main analysis JSON
        main_json = json.dumps({
            "agro_topic_cluster": "gestão",
            "agro_segment": "geral",
            "technical_depth": "intermediário",
            "core_argument": "modelo dependia de capital externo",
            "argument_structure": "dado → mecanismo → conclusão",
            "technical_claims": ["R$ 2,5bi em passivos"],
            "data_points": [{"value": "R$ 2,5bi", "context": "passivos", "source": None}],
            "sources_referenced": ["BDO"],
            "knowledge_assumptions": "",
            "content_gaps": "",
            "replication_template": "",
            "slide_breakdown": [],
            "carousel_complexity": {},
        })
        evidence_json = json.dumps({
            "mechanisms": ["recuperação judicial"],
            "causal_steps": ["Textor compra SAF", "Capital não chegou"],
            "definitions": [{"term": "recuperação judicial", "definition": "proteção temporária"}],
        })
        mock_client.chat.completions.create.side_effect = [
            _mock_gpt_response(main_json),   # vision call returns ""
            _mock_gpt_response(main_json),   # main analysis
            _mock_gpt_response(evidence_json),  # evidence extraction
        ]
        # Patch _transcribe_visual_assets to return empty string (no image URLs)
        with patch("src.analyzer.post_intelligence._transcribe_visual_assets", return_value=""):
            intel = analyze_post_intelligence(competitor_post, db_session)

    assert intel.evidence_inventory != {}
    assert "required" in intel.evidence_inventory
    assert "R$ 2,5bi" in intel.evidence_inventory["required"]["numbers"]
```

Note: Este teste é de integração mais pesado — se `db_session` e `competitor_post` fixtures não existirem, pode ser marcado como `skip` e testado manualmente. O importante é que a função seja chamada.

- [ ] **Step 2: Adicionar chamada no corpo de `analyze_post_intelligence()`**

Em `src/analyzer/post_intelligence.py`, dentro de `analyze_post_intelligence()`, após as linhas que setam todos os campos de `intelligence` (após linha ~190, antes de `session.add(intelligence)`):

```python
# Após intelligence.carousel_complexity = data.get("carousel_complexity", {})
intelligence.evidence_inventory = _extract_evidence_inventory(
    visual_transcript or "",
    data,
    caption,
)
```

- [ ] **Step 3: Rodar testes existentes para garantir não-regressão**

```bash
pytest tests/ -v -k "intelligence" --tb=short
```

Expected: todos PASS (a nova chamada não quebra o fluxo existente).

- [ ] **Step 4: Commit**

```bash
git add src/analyzer/post_intelligence.py tests/test_post_intelligence_evidence.py
git commit -m "feat: populate evidence_inventory in analyze_post_intelligence"
```

---

## Task 5: Snapshot `source_data_inventory` em `generate_post()`

**Files:**
- Modify: `src/generator/content_generator.py`
- Modify: `tests/test_content_generator.py`

- [ ] **Step 1: Escrever o teste**

```python
# tests/test_content_generator.py — adicionar ao final
def test_generate_post_snapshots_source_data_inventory(session_with_generation_context):
    """GeneratedPost.source_data_inventory deve ser cópia do evidence_inventory do post-fonte."""
    session, source_post, voice, approved = session_with_generation_context

    inventory = {
        "required": {"numbers": ["R$ 2,5bi"], "mechanisms": ["custo de insumo"], "causal_steps": [], "definitions": []},
        "optional": {"claims": [], "sources": [], "context": ""},
    }
    source_post.intelligence.evidence_inventory = inventory

    good_slides = [
        {"slide_number": 1, "slide_type": "CAPA", "title": "Título", "copy": "Texto"},
        {"slide_number": 2, "slide_type": "HOOK", "title": "Hook", "copy": "R$ 2,5bi em passivos"},
        {"slide_number": 3, "slide_type": "DADO", "title": "Dado", "copy": "custo de insumo disparou"},
        {"slide_number": 4, "slide_type": "SINTESE", "title": "Síntese", "copy": "Conclusão"},
        {"slide_number": 5, "slide_type": "CTA", "title": "CTA", "copy": "texto", "cta": "Saiba mais"},
    ]

    planning = {
        "tensao_central": "paradoxo",
        "angulo_de_adaptacao": "agro",
        "camadas": [{"numero": i+1, "tipo_slide": s["slide_type"], "funcao_narrativa": "x", "pergunta_que_abre": "x", "emocao_alvo": "espanto"} for i, s in enumerate(good_slides)],
        "total_slides": "5",
        "provas_que_nao_podem_sumir": ["R$ 2,5bi"],
        "dados_prometidos": [],
        "onde_termina": "fim",
    }

    response_json = json.dumps({
        "planejamento_narrativo": planning,
        "slides": good_slides,
        "caption": "Legenda de teste " * 20,
        "cta": "Saiba mais",
        "funnel_stage": "topo",
        "format": "carousel",
    })

    with patch("src.generator.content_generator._request_generation") as mock_req:
        mock_req.return_value = json.loads(response_json)
        generated = generate_post(source_post, voice, approved, session)

    assert generated.source_data_inventory == inventory
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_content_generator.py::test_generate_post_snapshots_source_data_inventory -v
```

Expected: FAIL — `GeneratedPost` criado sem `source_data_inventory`.

- [ ] **Step 3: Adicionar snapshot no construtor de `GeneratedPost`**

Em `src/generator/content_generator.py`, localize a criação do `GeneratedPost` (linhas ~1905-1916):

```python
# Linha 1904: normalized_result = evaluation["normalized_result"]
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
    source_data_inventory=deepcopy(getattr(intel, "evidence_inventory", None) or {}),  # ← ADD
)
```

- [ ] **Step 4: Rodar o teste**

```bash
pytest tests/test_content_generator.py::test_generate_post_snapshots_source_data_inventory -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/generator/content_generator.py tests/test_content_generator.py
git commit -m "feat: snapshot evidence_inventory as source_data_inventory on GeneratedPost"
```

---

## Task 6: Pledge Validator Module

**Files:**
- Create: `src/generator/pledge_validator.py`
- Create: `tests/test_pledge_validator.py`

- [ ] **Step 1: Escrever os testes**

```python
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
    # optional.claims and optional.sources should NOT trigger coverage issues
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
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_pledge_validator.py -v
```

Expected: `ImportError` — módulo ainda não existe.

- [ ] **Step 3: Implementar `src/generator/pledge_validator.py`**

```python
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
    mechs_lower = {str(m).lower() for m in (required.get("mechanisms") or [])}
    causal_words = {
        w.lower()
        for step in (required.get("causal_steps") or [])
        for w in re.findall(r"\b\w{5,}\b", str(step))
    }
    context_terms = mechs_lower | causal_words

    full_slide_text = " ".join(
        s.get("title", "") + " " + s.get("copy", "") for s in slides
    )
    words = full_slide_text.split()
    issues: list[str] = []

    for pledge in dados_prometidos:
        if pledge.get("item_type") != "numero":
            continue
        number = str(pledge.get("item", "")).strip()
        if not number or number not in full_slide_text:
            continue

        found_context = False
        for i, word in enumerate(words):
            if number in word or number == word:
                window_start = max(0, i - 7)
                window_end = min(len(words), i + 8)
                window_words = {w.lower() for w in words[window_start:window_end]}
                if window_words & context_terms:
                    found_context = True
                break

        if not found_context:
            issues.append(
                f"pledge violado — número '{number}' presente mas contexto semântico ausente "
                f"(possível inversão ou uso sem âncora)"
            )

    return issues
```

- [ ] **Step 4: Rodar os testes**

```bash
pytest tests/test_pledge_validator.py -v
```

Expected: todos PASS.

- [ ] **Step 5: Commit**

```bash
git add src/generator/pledge_validator.py tests/test_pledge_validator.py
git commit -m "feat: pledge_validator module with 5 validation functions"
```

---

## Task 7: Pledge no SYSTEM_PROMPT

**Files:**
- Modify: `src/generator/content_generator.py`

- [ ] **Step 1: Adicionar etapa 6 no ETAPA 1 e `dados_prometidos` no schema JSON**

Em `src/generator/content_generator.py`, localize o bloco `ETAPA 1` (linha ~70). Adicione após o item `5. PROVAS QUE NÃO PODEM SUMIR` e antes de `6. PONTO DE TÉRMINO`:

```
6. INVENTÁRIO PROMETIDO: Para cada item em `required.numbers`, `required.mechanisms`, `required.causal_steps` e `required.definitions` do inventário abaixo, liste explicitamente no `dados_prometidos` onde vai aparecer (slide_number, 1-based) e como será adaptado para o agro. Números devem aparecer verbatim pelo menos uma vez — analogias complementam, não substituem.
```

Atualize o item `6.` atual (PONTO DE TÉRMINO) para `7.`.

No schema JSON do `planejamento_narrativo` (linha ~115), adicione `dados_prometidos` após `provas_que_nao_podem_sumir`:

```python
# Dentro do schema planejamento_narrativo, após provas_que_nao_podem_sumir
    "dados_prometidos": [
      {{
        "item_type": "<numero|mecanismo|cadeia_causal|definicao>",
        "item": "<item exato do inventário>",
        "slide_number": <número 1-based do slide>,
        "como_vai_aparecer": "<como este item será adaptado para o contexto agro>"
      }}
    ],
```

- [ ] **Step 2: Verificar que os testes existentes não regridem**

```bash
pytest tests/test_content_generator.py -v --tb=short
```

Expected: todos PASS (a mudança no prompt não afeta testes que mocam `_request_generation`).

- [ ] **Step 3: Commit**

```bash
git add src/generator/content_generator.py
git commit -m "feat: add dados_prometidos to planejamento_narrativo SYSTEM_PROMPT schema"
```

---

## Task 8: Wire Validators into `_evaluate_generation()` e Revision Directives

**Files:**
- Modify: `src/generator/content_generator.py`

- [ ] **Step 1: Escrever o teste de integração do gate**

```python
# tests/test_content_generator.py — adicionar ao final
def test_evaluate_generation_blocks_when_pledge_number_missing(session_with_generation_context):
    """Gate deve reprovar quando número pledgeado não aparece no texto final."""
    session, source_post, voice, approved = session_with_generation_context

    source_post.intelligence.evidence_inventory = {
        "required": {
            "numbers": ["R$ 2,5bi"],
            "mechanisms": ["custo de insumo"],
            "causal_steps": [],
            "definitions": [],
        },
        "optional": {"claims": [], "sources": [], "context": ""},
    }

    planning = {
        "tensao_central": "paradoxo",
        "angulo_de_adaptacao": "agro",
        "camadas": [],
        "total_slides": "5",
        "provas_que_nao_podem_sumir": ["R$ 2,5bi"],
        "dados_prometidos": [
            {"item_type": "numero", "item": "R$ 2,5bi", "slide_number": 3, "como_vai_aparecer": "safra"},
        ],
        "onde_termina": "fim",
    }

    # Slides WITHOUT "R$ 2,5bi" — pledge violated
    slides = [
        {"slide_number": 1, "slide_type": "CAPA", "title": "T", "copy": "texto"},
        {"slide_number": 2, "slide_type": "HOOK", "title": "T", "copy": "hook"},
        {"slide_number": 3, "slide_type": "DADO", "title": "T", "copy": "custo de insumo subiu muito"},
        {"slide_number": 4, "slide_type": "SINTESE", "title": "T", "copy": "conclusão"},
        {"slide_number": 5, "slide_type": "CTA", "title": "T", "copy": "CTA", "cta": "ok"},
    ]

    result = {
        "planejamento_narrativo": planning,
        "slides": slides,
        "caption": "Legenda " * 25,
        "cta": "Saiba mais",
        "funnel_stage": "topo",
        "format": "carousel",
    }

    from src.generator.content_generator import _evaluate_generation, _build_evidence_pack, _select_top_arguments
    from src.carousel_quality import estimate_target_slide_count

    top_args = _select_top_arguments(session, source_post)
    from src.generator.content_generator import _build_validated_data_catalog
    catalog = _build_validated_data_catalog(source_post, top_args)
    evidence_pack = _build_evidence_pack(source_post, top_args, catalog)
    target = estimate_target_slide_count()

    evaluation = _evaluate_generation(result, source_post, evidence_pack, target)
    combined_issues = evaluation["problems"] + evaluation["quality_report"].get("issues", [])
    assert any("pledge violado" in i for i in combined_issues)
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_content_generator.py::test_evaluate_generation_blocks_when_pledge_number_missing -v
```

Expected: FAIL — `_evaluate_generation` ainda não chama os validators.

- [ ] **Step 3: Adicionar import do pledge_validator e os 3 prefixos bloqueantes**

Em `src/generator/content_generator.py`:

No topo do arquivo, após os imports existentes:
```python
from src.generator.pledge_validator import (
    validate_pledge_coverage,
    validate_pledge_traceability,
    validate_pledge_slide_bounds,
    validate_pledge_fulfillment,
    validate_number_context,
)
```

Em `_BLOCKING_ISSUE_PREFIXES` (linha ~216), adicione ao final da tupla:
```python
    "pledge incompleto —",
    "pledge inválido —",
    "pledge violado —",
```

- [ ] **Step 4: Chamar os validators em `_evaluate_generation()`**

Em `_evaluate_generation()`, após o bloco de `planning_issues` (após linha ~879), adicione:

```python
    # Pledge validation — 5-layer gate
    inventory = getattr(source_post.intelligence, "evidence_inventory", None) or {}
    if inventory:
        dados_prometidos = (result.get("planejamento_narrativo") or {}).get("dados_prometidos") or []
        # 3a: coverage (inventory → pledge)
        for issue in validate_pledge_coverage(dados_prometidos, inventory):
            if issue not in problems:
                problems.append(issue)
        # 3b: traceability (pledge items must trace to inventory)
        for issue in validate_pledge_traceability(dados_prometidos, inventory):
            if issue not in problems:
                problems.append(issue)
        # 3c: slide bounds
        for issue in validate_pledge_slide_bounds(dados_prometidos, slides):
            if issue not in problems:
                problems.append(issue)
        # 3d: fulfillment (pledge → output)
        for issue in validate_pledge_fulfillment(dados_prometidos, slides, caption, (result.get("cta") or "").strip()):
            if issue not in problems:
                problems.append(issue)
        # 3e: number context (semantic neighborhood)
        for issue in validate_number_context(dados_prometidos, slides, inventory):
            if issue not in problems:
                problems.append(issue)
```

- [ ] **Step 5: Adicionar diretivas de revisão para pledge no `_build_revision_directives()`**

Em `_build_revision_directives()` (linha ~1022), antes do bloco `if not directives:`, adicione:

```python
    if any("pledge incompleto" in issue for issue in normalized_issues):
        missing = [i for i in issues if "pledge incompleto" in i.lower()]
        items_str = "; ".join(missing[:3])
        directives.append(
            f"Reescreva o planejamento_narrativo adicionando entradas em dados_prometidos para os itens ausentes: {items_str}. "
            "Cada item required do inventário deve ter um compromisso explícito."
        )
    if any("pledge inválido" in issue for issue in normalized_issues):
        directives.append(
            "Corrija o dados_prometidos: cada item deve referenciar algo existente no inventário do post-fonte. "
            "Não invente números ou mecanismos — use apenas os itens listados em required."
        )
    if any("pledge violado — número" in issue for issue in normalized_issues):
        numbers = [
            i.split("'")[1] for i in issues
            if "pledge violado — número" in i.lower() and "'" in i
        ]
        nums_str = ", ".join(numbers[:3])
        directives.append(
            f"Os números {nums_str} foram prometidos no pledge mas não aparecem no texto final. "
            "Números obrigatórios devem aparecer verbatim pelo menos uma vez — analogias complementam, não substituem."
        )
    if any("pledge violado — mecanismo" in issue for issue in normalized_issues):
        directives.append(
            "Mecanismos pledgeados estão ausentes no texto. Reinsira os termos técnicos nos slides comprometidos."
        )
    if any("pledge violado — passo de cadeia causal" in issue for issue in normalized_issues):
        directives.append(
            "A cadeia causal do material-base tem passos pledgeados que não aparecem no texto. "
            "Cada passo da cadeia deve ter ao menos um termo-chave presente no slide comprometido (±2)."
        )
    if any("contexto semântico ausente" in issue for issue in normalized_issues):
        directives.append(
            "Números presentes mas sem contexto semântico correto. "
            "Coloque o número sempre próximo de um mecanismo ou termo da cadeia causal — nunca isolado ou com valência invertida."
        )
```

- [ ] **Step 6: Rodar todos os testes**

```bash
pytest tests/test_content_generator.py tests/test_pledge_validator.py -v --tb=short
```

Expected: todos PASS.

- [ ] **Step 7: Rodar suite completa**

```bash
pytest tests/ -v --tb=short
```

Expected: sem regressões.

- [ ] **Step 8: Commit final**

```bash
git add src/generator/content_generator.py
git commit -m "feat: wire pledge validators into _evaluate_generation and _build_revision_directives"
```

---

## Task 9: Push e Deploy

- [ ] **Step 1: Push para Railway**

```bash
git push origin main
```

Expected: Railway auto-deploy dispara. Acompanhar logs no dashboard.

- [ ] **Step 2: Verificar migração 011 no Railway**

Nos logs do Railway, confirmar:
```
Running upgrade 010 -> 011, add evidence_inventory...
```

- [ ] **Step 3: Smoke test manual no frontend**

Em `altagro.site`, abrir o Studio, selecionar um post de concorrente com `PostIntelligence` existente e gerar. Verificar nos logs que:
1. `evidence_inventory` foi populado (posts novos analisados após o deploy)
2. `source_data_inventory` aparece no `GeneratedPost` criado
3. Nenhum erro 500 no gerador

---

## Self-Review

**Spec coverage check:**
- ✅ `evidence_inventory` em `PostIntelligence` — Task 2 + Task 3 + Task 4
- ✅ `source_data_inventory` em `GeneratedPost` — Task 2 + Task 5
- ✅ Migration 011 — Task 1
- ✅ `dados_prometidos` no SYSTEM_PROMPT com 4 item_types — Task 7
- ✅ `slide_number` 1-based — Task 6 (`validate_pledge_slide_bounds` valida range [1, n])
- ✅ `validate_pledge_coverage` — Task 6 + Task 8
- ✅ `validate_pledge_traceability` — Task 6 + Task 8
- ✅ `validate_pledge_slide_bounds` — Task 6 + Task 8
- ✅ `validate_pledge_fulfillment` — Task 6 + Task 8
- ✅ `validate_number_context` — Task 6 + Task 8
- ✅ Prefixos bloqueantes — Task 8
- ✅ Diretivas de revisão específicas para pledge — Task 8
- ✅ Números verbatim obrigatórios — enforced em `validate_pledge_fulfillment` + diretiva
- ✅ `required` vs `optional` — validators só exigem `required`

**Nenhum placeholder encontrado.**

**Consistência de tipos:**
- `dados_prometidos: list[dict[str, Any]]` — consistente em todos os validators e no `_evaluate_generation`
- `inventory: dict[str, Any]` — consistente
- `slides: list[dict[str, Any]]` — consistente com o formato existente no codebase (`slide_number`, `slide_type`, `title`, `copy`)
- `slide_number` é sempre `int` após `int(pledge.get("slide_number"))` — tratado em todos os validators
