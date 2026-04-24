# Data Lock + Pledge + Self-Refinement Engine

**Data:** 2026-04-24  
**Módulo:** Content Studio (`src/generator/content_generator.py`) + Carousel (`src/carousel/generator.py`)  
**Status:** Aprovado — implementação em duas fases

## Fases de implementação

| Fase | Escopo | Objetivo |
|---|---|---|
| **Fase 1** | Data Lock + Pledge + Validation Gate | Garantir que dados do post-fonte sobrevivem ao Studio |
| **Fase 2** | PatternBank + Self-Refinement Loop | Aprender com posts aprovados para melhorar gerações futuras |

Fase 2 depende de Fase 1 e de pré-requisitos de infraestrutura detalhados abaixo.

---

## Problema

O Studio gera posts adaptando conteúdo de concorrentes, mas não tem garantia de que os dados do post original (números, mecanismos, cadeia causal) sobrevivem até o texto final. O modelo pode omitir dados críticos, citar números sem contexto ou inverter o sentido de uma afirmação — e o quality gate atual não detecta nenhum desses casos com precisão cirúrgica.

---

## Fase 1 — Data Lock + Pledge + Validation Gate

### 1. Data Lock — evidência nasce na análise, geração tira snapshot

A extração de evidências acontece **quando o post é analisado** (pipeline de análise), não na geração. Isso cria uma biblioteca de estudos reutilizável e evita recalcular evidência a cada geração.

**`PostIntelligence` ganha o campo `evidence_inventory`** — estruturado em `required` e `optional`:

```json
{
  "required": {
    "numbers": ["R$ 2,5bi", "R$ 427mi", "R$ 1,4bi"],
    "mechanisms": ["recuperação judicial", "patrimônio líquido negativo", "capital de giro"],
    "causal_steps": [
      "Textor compra SAF em 2022 com promessa de capital externo contínuo",
      "Clube ganha Libertadores em novembro de 2024",
      "BDO já alertava desde 2024: patrimônio negativo e capital de giro deficiente",
      "Capital prometido não chegou — Cork Gully bloqueia novos investidores",
      "R$ 2,5bi em passivos, R$ 427mi de patrimônio negativo",
      "Recuperação judicial protocolada no TJRJ"
    ],
    "definitions": [
      {"term": "recuperação judicial", "definition": "proteção temporária contra credores — não é falência"},
      {"term": "patrimônio líquido negativo", "definition": "dívidas maiores que todos os ativos somados"}
    ]
  },
  "optional": {
    "claims": ["dívidas maiores que todos os ativos somados"],
    "sources": ["BDO", "Demonstrações Contábeis SAF"],
    "context": "modelo dependia de capital externo contínuo que nunca chegou"
  }
}
```

**Severidade explícita:**
- `required` — o Validation Gate exige presença no post gerado. Ausência é issue bloqueante.
- `optional` — sugerido ao modelo via prompt, mas ausência não bloqueia. Evita reprovar adaptações boas.

**`GeneratedPost.source_data_inventory`** é um snapshot imutável do `PostIntelligence.evidence_inventory` no momento da geração. Se o `PostIntelligence` for re-analisado depois, o contrato daquela geração específica não muda.

**Extração do `evidence_inventory`:** GPT call sobre o `visual_transcript` durante o pipeline de análise de posts (junto com os demais campos de `PostIntelligence`). `causal_steps` e `definitions` são novos; `numbers`, `mechanisms`, `claims`, `sources` são reorganizações dos campos já extraídos hoje. Posts sem estrutura educacional retornam `definitions: []` e `causal_steps: []`.

---

### 2. Pledge — compromisso pré-escrita dentro do `planejamento_narrativo`

Nova seção obrigatória `dados_prometidos` dentro do `planejamento_narrativo` existente. O modelo recebe o `source_data_inventory` no prompt e deve comprometer-se, **para cada item `required`**, onde vai aparecer e como será adaptado — antes de escrever qualquer slide.

**Estrutura:**

```json
"dados_prometidos": [
  {
    "item_type": "numero",
    "item": "R$ 2,5bi",
    "slide_number": 4,
    "como_vai_aparecer": "convertido para equivalente em custo de safra de soja"
  },
  {
    "item_type": "cadeia_causal",
    "item": "capital prometido não chegou — estrutura colapsou",
    "slide_number": 7,
    "como_vai_aparecer": "crédito rural previsto no plano que nunca saiu"
  },
  {
    "item_type": "definicao",
    "item": "recuperação judicial",
    "slide_number": 9,
    "como_vai_aparecer": "analogia com renegociação de dívida rural — proteção, não colapso"
  }
]
```

**Três `item_type` suportados:** `numero`, `cadeia_causal`, `definicao`.

**Regra explícita sobre números:** números `required` devem aparecer **verbatim pelo menos uma vez** no texto final. Analogias e conversões de escala podem complementar o número, mas não o substituem. O número original ancora a credibilidade; a analogia ensina a escala.

**`slide_number` é 1-based** — CAPA é slide 1, CTA é slide `len(slides)`. O pledge usa `slide_number`, não índice zero.

---

### 3. Validation Gate — cinco funções em cadeia

Toda a validação acontece pós-chamada de API (planning + slides chegam em um único JSON). Funções 3a–3c examinam o `planejamento_narrativo.dados_prometidos`; se falharem, os slides não são avaliados e a resposta inteira vai para revisão.

```
GPT retorna JSON { planejamento_narrativo + slides }
        ↓
3a. _validate_pledge_coverage()       ← required do inventário coberto pelo pledge?
3b. _validate_pledge_traceability()   ← cada item do pledge rastreia ao inventário?
3c. _validate_pledge_slide_bounds()   ← slide_number existe no carrossel real?
    se qualquer falhar → revisão do planejamento_narrativo (slides não avaliados)
        ↓
3d. _validate_pledge_fulfillment()    ← pledge honrado no output?
3e. _validate_number_context()        ← números com contexto semântico correto?
        ↓
_evaluate_generation()                ← quality gate existente (sem mudança)
```

#### 3a. `_validate_pledge_coverage(dados_prometidos, source_data_inventory)`

Apenas campos `required` são exigidos no pledge. `optional` não é verificado.

| Campo `required` | Regra de cobertura |
|---|---|
| `numbers` | Ao menos 1 pledge item do tipo `numero` por número |
| `mechanisms` | Ao menos 1 pledge item referencia cada mecanismo |
| `causal_steps` com N itens | Ao menos max(1, ⌊N × 0.7⌋) passos cobertos |
| `definitions` (se não vazia) | Ao menos 1 definição representada |

Issues bloqueantes com prefixo `"pledge incompleto —"`.

#### 3b. `_validate_pledge_traceability(dados_prometidos, source_data_inventory)`

Impede que o modelo invente itens no pledge para parecer que cobre o inventário.

| `item_type` | Regra |
|---|---|
| `numero` | `item` é substring de algum valor em `required.numbers` |
| `cadeia_causal` | `item` compartilha ao menos 2 substantivos com algum passo de `required.causal_steps` |
| `definicao` | `item` referencia um `term` de `required.definitions` |

Issues bloqueantes com prefixo `"pledge inválido —"`.

#### 3c. `_validate_pledge_slide_bounds(dados_prometidos, slides)`

`slide_number` de cada item deve estar em `[1, len(slides)]`. Issue bloqueante se fora do range.

#### 3d. `_validate_pledge_fulfillment(dados_prometidos, slides, caption, cta)`

| `item_type` | Regra de fulfillment |
|---|---|
| `numero` | Número aparece **verbatim** nos slides `slide_number ±1`; fallback: texto completo. Analogias complementam mas não substituem. |
| `cadeia_causal` | Ao menos 1 dos 2-3 termos-chave do item aparece nos slides `slide_number ±2` |
| `definicao` | Slide em `slide_number ±1` contém estrutura definitória: "significa", "não é", "≠", "em outras palavras", "na prática" |

`numero` e `cadeia_causal` ausentes → bloqueantes. `definicao` ausente → revisão (não bloqueia).

#### 3e. `_validate_number_context(dados_prometidos, slides)`

Para cada pledge item do tipo `numero`: janela de 15 palavras ao redor do número no texto final deve conter ao menos 1 termo de `required.mechanisms` ou do `causal_step` correspondente.

Issue bloqueante: `"pledge violado — numero 'X' presente mas contexto semântico ausente (possível inversão)"`.

**Prefixos bloqueantes adicionados a `_BLOCKING_ISSUE_PREFIXES`:**
- `"pledge incompleto —"`
- `"pledge inválido —"`
- `"pledge violado —"`

---

## Fase 2 — PatternBank + Self-Refinement Loop (futura)

### Pré-requisitos antes de iniciar Fase 2

A Fase 2 depende de infraestrutura que ainda não existe:

1. **Endpoint de aprovação no Studio** — `PATCH /generated-posts/{id}` com `status="approved"` (hoje a aprovação não tem endpoint dedicado)
2. **Persistência de métricas de qualidade em `GeneratedPost`** — colunas `quality_score`, `quality_issues` (JSON), `strict_pass` (bool). Hoje esses dados só existem em memória durante a geração.

Esses dois itens devem ser entregues antes ou junto com a Fase 2.

---

### Model `GenerationPattern`

```python
class GenerationPattern(Base):
    __tablename__ = "generation_patterns"

    id: int (PK)
    generated_post_id: int (FK → generated_posts, unique)
    hook_archetype: str        # um dos 5 archetypes Varos
    narrative_arc: str         # um dos 3 arcos narrativos
    slide_type_sequence: list  # JSON: sequência de tipos de slide
    pledge_fulfillment_rate: float  # % de itens required do pledge honrados
    quality_score: float
    weight: float              # 1.0 = strict_pass / 2.0 = approved manual
    structural_insights: dict  # JSON: análise GPT do que funcionou
    extracted_at: datetime
```

**`structural_insights` extraído por GPT:**

```json
{
  "hook_technique": "afirmação paradoxal → dado imediato sem margem de dúvida",
  "data_anchoring_method": "número absoluto primeiro, contexto de escala depois",
  "tension_resolution_pattern": "contradição no slide 3, resolução adiada até slide 11",
  "teaching_pattern": "termo técnico → definição simples → analogia prática",
  "emotional_arc_summary": "espanto (1-3) → análise fria (4-8) → indignação (9) → síntese (10-11) → ação (12)"
}
```

### Extração

| Evento | Weight | Trigger |
|---|---|---|
| `GeneratedPost.status → "approved"` | 2.0 | Imediato — hook em `PATCH /generated-posts/{id}` |
| `strict_pass=True`, status `"generated"` | 1.0 | APScheduler diário (06:30 UTC) |

### Recuperação e injeção na geração

Filtro por `hook_archetype` primeiro, depois `weight` descrescente. Fallback global se menos de 2 resultados no archetype. Top 3 injetados como nova seção no SYSTEM_PROMPT antes do ETAPA 1, em ambos os geradores.

---

## Arquivos afetados

### Fase 1

| Arquivo | Mudança |
|---|---|
| `src/models.py` | `evidence_inventory` em `PostIntelligence` + `source_data_inventory` em `GeneratedPost` |
| `src/intelligence/analyzer.py` (ou equivalente) | extração de `evidence_inventory` durante análise do post |
| `src/generator/content_generator.py` | snapshot do inventário, pledge no SYSTEM_PROMPT, 5 validadores |
| `alembic/versions/011_evidence_inventory.py` | `evidence_inventory` em `post_intelligence` + `source_data_inventory` em `generated_posts` |

### Fase 2 (futura)

| Arquivo | Mudança |
|---|---|
| `src/models.py` | `GenerationPattern` (novo) + `quality_score`, `quality_issues`, `strict_pass` em `GeneratedPost` |
| `src/generator/pattern_extractor.py` | novo — `extract_and_store_pattern()` |
| `src/generator/content_generator.py` | retrieval e injeção de padrões |
| `src/carousel/generator.py` | injeção de padrões |
| `alembic/versions/012_generation_patterns.py` | tabela `generation_patterns` + colunas de qualidade em `generated_posts` |
| API | endpoint `PATCH /generated-posts/{id}` com hook de aprovação |

---

## Fora de escopo

- Fine-tuning do modelo GPT
- Validação semântica profunda além da verificação de vizinhança
- Interface no frontend para visualizar `GenerationPattern` ou `evidence_inventory`
- Exportação do PatternBank
