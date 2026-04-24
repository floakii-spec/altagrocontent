# Data Lock + Pledge + Self-Refinement Engine

**Data:** 2026-04-24  
**Módulo:** Content Studio (`src/generator/content_generator.py`) + Carousel (`src/carousel/generator.py`)  
**Status:** Aprovado — pronto para implementação

---

## Problema

O Studio gera posts adaptando conteúdo de concorrentes, mas não tem garantia de que os dados do post original (números, mecanismos, cadeia causal) sobrevivem até o texto final. O modelo pode omitir dados críticos, citar números sem contexto ou inverter o sentido de uma afirmação — e o quality gate atual não detecta nenhum desses casos com precisão cirúrgica.

---

## Solução em três camadas

### 1. Data Lock — inventário congelado por geração

Ao iniciar uma geração no Studio, os dados críticos do post-fonte são extraídos e persistidos como `source_data_inventory` no `GeneratedPost`. O inventário é imutável — se o `PostIntelligence` do post-fonte for re-analisado depois, o contrato daquela geração específica não muda.

**Campos do inventário:**

```json
{
  "numeros_obrigatoriamente_ancorados": ["R$ 2,5bi", "R$ 427mi", "R$ 1,4bi"],
  "mecanismos_que_nao_podem_sumir": ["recuperação judicial", "patrimônio líquido negativo"],
  "afirmacoes_tecnicas": ["dívidas maiores que todos os ativos somados"],
  "argumento_central": "modelo dependia de capital externo que nunca chegou",
  "fontes_disponiveis": ["BDO", "Demonstrações Contábeis SAF"],
  "cadeia_causal": [
    "Textor compra SAF em 2022 com promessa de capital externo contínuo",
    "Clube ganha Libertadores em novembro de 2024",
    "BDO já alertava desde 2024: patrimônio negativo e capital de giro deficiente",
    "Capital prometido não chegou — Cork Gully bloqueia novos investidores",
    "R$ 2,5bi em passivos, R$ 427mi de patrimônio negativo",
    "Recuperação judicial protocolada no TJRJ"
  ],
  "definicoes_ensinadas": [
    {"termo": "recuperação judicial", "definicao": "proteção temporária contra credores — não é falência"},
    {"termo": "patrimônio líquido negativo", "definicao": "dívidas maiores que todos os ativos somados"}
  ]
}
```

`cadeia_causal` e `definicoes_ensinadas` são extraídos via GPT call sobre o `visual_transcript` no momento da geração (não no pipeline de análise — nenhuma migração no `PostIntelligence`). Posts sem estrutura educacional retornam listas vazias.

Os demais campos vêm de `_build_validated_data_catalog()` já existente.

---

### 2. Pledge — compromisso pré-escrita dentro do `planejamento_narrativo`

Nova seção obrigatória `dados_prometidos` dentro do `planejamento_narrativo` existente. O modelo recebe o `source_data_inventory` no prompt e deve comprometer-se, para cada item crítico que vai usar, **onde vai aparecer e como será adaptado** — antes de escrever qualquer slide.

**Estrutura:**

```json
"dados_prometidos": [
  {
    "item_type": "numero",
    "item": "R$ 2,5bi",
    "slide_index": 4,
    "como_vai_aparecer": "convertido para equivalente em custo de safra de soja"
  },
  {
    "item_type": "cadeia_causal",
    "item": "capital prometido não chegou — estrutura colapsou",
    "slide_index": 7,
    "como_vai_aparecer": "crédito rural previsto no plano que nunca saiu"
  },
  {
    "item_type": "definicao",
    "item": "recuperação judicial",
    "slide_index": 9,
    "como_vai_aparecer": "analogia com renegociação de dívida rural — proteção, não colapso"
  }
]
```

**Três `item_type` suportados:** `numero`, `cadeia_causal`, `definicao`.

O pledge trava o *dado*, não a *copy*. "R$ 2,5bi" pode virar "o equivalente a 3 safras de uma fazenda média do Mato Grosso" — o número ancora, a linguagem é Nathan.

---

### 3. Validation Gate — cadeia completa de verificação

Quatro funções de validação em sequência, integradas ao pipeline existente como fontes adicionais de issues:

#### 3a. `_validate_pledge_coverage(dados_prometidos, source_data_inventory)`
Verifica que o pledge cobre o inventário — não o contrário.

| Item do inventário | Regra |
|---|---|
| Todos os `numeros_obrigatoriamente_ancorados` | Ao menos 1 pledge item referencia cada número |
| Todos os `mecanismos_que_nao_podem_sumir` | Ao menos 1 pledge item referencia cada mecanismo |
| `cadeia_causal` com N passos | Ao menos max(1, ⌊N × 0.7⌋) passos cobertos por pledge items |
| `definicoes_ensinadas` (se não vazia) | Ao menos 1 definição representada |

Issues bloqueantes → dispara reescrita do `planejamento_narrativo`.

#### 3b. `_validate_pledge_traceability(dados_prometidos, source_data_inventory)`
Verifica que cada item no pledge rastreia de volta ao inventário — impede que o modelo invente itens para satisfazer a cobertura.

| `item_type` | Regra de rastreabilidade |
|---|---|
| `numero` | `item` deve ser substring de algum valor em `numeros_obrigatoriamente_ancorados` |
| `cadeia_causal` | `item` deve compartilhar ao menos 2 substantivos com algum passo da `cadeia_causal` |
| `definicao` | `item` deve referenciar um `termo` de `definicoes_ensinadas` |

Issues bloqueantes → dispara reescrita do `planejamento_narrativo`.

#### 3c. `_validate_pledge_fulfillment(dados_prometidos, slides, caption, cta)`
Verifica que o que foi prometido aparece no texto final.

| `item_type` | Regra de fulfillment |
|---|---|
| `numero` | Número aparece verbatim nos slides `slide_index ±1`; fallback: texto completo |
| `cadeia_causal` | Ao menos 1 dos 2-3 termos-chave do item aparece nos slides `slide_index ±2` |
| `definicao` | Slide em `slide_index ±1` contém estrutura definitória: "significa", "não é", "≠", "em outras palavras", "na prática" |

`numero` e `cadeia_causal` ausentes → bloqueantes. `definicao` ausente → revisão (não bloqueia).

#### 3d. `_validate_number_context(dados_prometidos, slides)`
Verifica que números pledgeados aparecem com contexto semântico correto — não apenas presença textual.

Para cada pledge item do tipo `numero`: examinar janela de 15 palavras ao redor do número no texto final. Ao menos um termo dos `mecanismos_que_nao_podem_sumir` ou da `cadeia_causal` correspondente deve aparecer nessa janela.

Issue bloqueante: `"pledge violado — numero 'X' presente mas sem contexto semântico correto (possível inversão)"`.

**Pipeline de validação completo:**

Toda a validação acontece pós-chamada de API (planning + slides chegam em um único JSON). As funções de cobertura e rastreabilidade examinam o `planejamento_narrativo.dados_prometidos` retornado; se falharem, os slides não são avaliados e a resposta inteira vai para revisão.

```
GPT retorna JSON { planejamento_narrativo + slides }
        ↓
_validate_pledge_coverage()       ← dados_prometidos cobre o inventário?
_validate_pledge_traceability()   ← cada item do pledge rastreia ao inventário?
_validate_pledge_slide_bounds()   ← slide_index de cada item está dentro do range real?
   se falhar → revisão do planejamento_narrativo (slides não avaliados)
        ↓
_validate_pledge_fulfillment()    ← pledge honrado no output?
_validate_number_context()        ← números com contexto semântico correto?
        ↓
_evaluate_generation()            ← quality gate existente (sem mudança)
```

`_validate_pledge_slide_bounds`: cada `slide_index` em `dados_prometidos` deve estar em `[1, len(slides)-1]` (0 é CAPA, reservado). Issue bloqueante se fora do range.

**Prefixos bloqueantes adicionados a `_BLOCKING_ISSUE_PREFIXES`:**
- `"pledge incompleto —"`
- `"pledge violado —"`

---

## PatternBank + Self-Refinement Loop

### Model `GenerationPattern`

```python
class GenerationPattern(Base):
    __tablename__ = "generation_patterns"

    id: int (PK)
    generated_post_id: int (FK → generated_posts, unique)
    hook_archetype: str        # um dos 5 archetypes Varos
    narrative_arc: str         # um dos 3 arcos narrativos
    slide_type_sequence: list  # JSON: sequência de tipos de slide
    pledge_fulfillment_rate: float  # % de itens do pledge honrados
    quality_score: float
    weight: float              # 1.0 = strict_pass / 2.0 = approved manual
    structural_insights: dict  # JSON: análise GPT do que funcionou
    extracted_at: datetime
```

**`structural_insights` extraído por GPT após aprovação:**

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
| `GeneratedPost.status → "approved"` | 2.0 | Imediato — chamado em `PATCH /generated-posts/{id}` quando `status="approved"` |
| `strict_pass=True`, status `"generated"` | 1.0 | APScheduler diário (06:30 UTC) — processa GeneratedPosts com strict_pass sem GenerationPattern |

Função `extract_and_store_pattern(generated_post_id, session)` em `src/generator/pattern_extractor.py` (novo):
1. Carrega `GeneratedPost` com `planning_narrative`, `slides`, `source_data_inventory`
2. Extrai `hook_archetype` e `narrative_arc` do `planning_narrative`
3. Calcula `pledge_fulfillment_rate`
4. Chama GPT para `structural_insights`
5. Persiste em `GenerationPattern`

### Recuperação na geração

```python
def _retrieve_top_patterns(session, hook_archetype, limit=3):
    patterns = (query
        .filter_by(hook_archetype=hook_archetype)
        .order_by(weight.desc(), quality_score.desc())
        .limit(limit).all())
    if len(patterns) < 2:
        patterns = query.order_by(weight.desc()).limit(limit).all()
    return patterns
```

Filtro por `hook_archetype` primeiro (relevância estrutural), depois `weight` (qualidade comprovada). Fallback global se menos de 2 resultados no archetype.

### Injeção no SYSTEM_PROMPT

Nova seção antes do ETAPA 1, em ambos os geradores (`content_generator.py` e `carousel/generator.py`):

```
PADRÕES QUE FUNCIONARAM EM POSTS APROVADOS
Use como referência de raciocínio — não como template de copy.

Hook archetype: paradoxo por comparação
Arco narrativo: espiral descendente de revelações
Sequência: CAPA → HOOK → ESCALADA → DADO → REVELACAO → MECANISMO → SINTESE → CTA
Ancoragem de dados: número absoluto primeiro, contexto de escala depois
Arco emocional: espanto (1-3) → análise fria (4-8) → síntese (10-11) → ação (12)
Pledge fulfillment: 96%
```

### Crescimento do refinamento

- **Semana 1**: sem padrões → geração usa só metodologia Varos
- **~10 aprovados**: padrões começam a influenciar planejamento narrativo
- **~50 aprovados**: sistema conhece técnicas específicas para voz do Nathan e público agro

Não é fine-tuning — é few-shot learning estruturado que cresce com uso real.

---

## Arquivos afetados

| Arquivo | Mudança |
|---|---|
| `src/models.py` | `GenerationPattern` (novo) + `source_data_inventory` em `GeneratedPost` |
| `src/generator/content_generator.py` | extração do inventário, pledge, 4 validadores, retrieval de padrões |
| `src/carousel/generator.py` | injeção de padrões no SYSTEM_PROMPT |
| `src/generator/pattern_extractor.py` | novo — `extract_and_store_pattern()` |
| `alembic/versions/011_data_lock_pattern_bank.py` | `generation_patterns` + `source_data_inventory` |
| Endpoint de aprovação (API) | hook para `extract_and_store_pattern()` |

---

## Fora de escopo

- Fine-tuning do modelo GPT
- Validação semântica profunda do conteúdo (além da verificação de vizinhança)
- Interface no frontend para visualizar `GenerationPattern`
- Exportação do PatternBank
