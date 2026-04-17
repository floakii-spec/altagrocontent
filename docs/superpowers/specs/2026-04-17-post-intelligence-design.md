# Post Intelligence & Argument Bank Design

## Goal

Transform collected posts into professional-grade content intelligence: per-post technical deep dives (arguments, data, agro knowledge, narrative logic) plus a cross-post Argument Bank that feeds content generation — with an `origin` field ready for the future Self-Refinement Engine.

## Architecture

```
Post (already collected)
  │
  ├─► PostAnalysis (existing) — visual format, tone, trigger, virality score
  │
  └─► PostIntelligence (NEW) — technical content: arguments, data, depth, logic
        │
        └─► ArgumentBank (NEW) — de-duplicated arguments, quality + virality scored
                                  feeds Carousel Generator and Studio
```

**Flow:**
1. Daily APScheduler job (07:00 UTC) finds posts without `PostIntelligence` and processes in batch
2. GPT-4o second pass per post — focused exclusively on technical content
3. Extracted arguments inserted into `ArgumentBank` (de-duplicated by normalized text)
4. Carousel Generator and Studio query `ArgumentBank` filtered by topic, ranked by `virality_weight × quality_score`
5. New "Inteligência" module in the orbital tree exposes per-post deep dives and the browsable argument bank

## Database

### `post_intelligence`

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| post_id | FK → posts | unique per post |
| agro_topic_cluster | String(50) | soja\|milho\|pecuária\|insumos\|gestão\|tecnologia\|crédito\|outro |
| agro_segment | String(50) | grãos\|fibras\|pecuária\|horticultura\|cafeicultura\|geral |
| technical_depth | String(20) | superficial\|intermediário\|especialista |
| core_argument | Text | central thesis in one direct sentence |
| argument_structure | Text | logical flow: e.g. "dado chocante → causa → solução → prova" |
| technical_claims | JSON | list of technical assertion strings |
| data_points | JSON | list of `{value, context, source}` dicts |
| sources_referenced | JSON | list of source name strings |
| knowledge_assumptions | Text | what the post assumes the audience already knows |
| content_gaps | Text | what was missing that would enrich the content |
| replication_template | Text | replicable formula: e.g. "[DADO] + [CAUSA] + [SOLUÇÃO] + [CTA]" |
| analyzed_at | DateTime(tz) | UTC |

### `argument_bank`

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| text | Text | the argument itself |
| topic_cluster | String(50) | soja, milho, gestão, etc. |
| agro_segment | String(50) | grãos, pecuária, etc. |
| quality_score | Float 0–1 | computed on insert, no GPT call |
| virality_weight | Float 0–1 | avg virality_score of source posts |
| source_post_ids | JSON | list of post IDs where argument appeared |
| times_seen | Integer | how many posts used this argument |
| origin | String(20) | `"extracted"` or `"generated"` (Self-Refinement hook) |
| created_at | DateTime(tz) | UTC |

**Quality score logic (no GPT-4o, computed locally):**
- `+0.4` if argument contains a numeric value (regex `\d+`)
- `+0.3` if a source is referenced (non-empty `sources_referenced`)
- `+0.3` if argument text is ≥ 15 words (specificity proxy)

**De-duplication:** normalized text comparison (`lower().strip()`) before insert. If match found: increment `times_seen`, append post_id to `source_post_ids`, recompute `virality_weight`.

## Backend

### `src/analyzer/post_intelligence.py` — NEW

Single public function:
```python
def analyze_post_intelligence(post: Post, session: Session) -> PostIntelligence
```

**GPT-4o prompt (system):**
```
Você é um analista de conteúdo especialista em agronegócio brasileiro.
Analise o post fornecido com profundidade técnica e retorne APENAS um JSON:
{
  "agro_topic_cluster": "<soja|milho|pecuária|insumos|gestão|tecnologia|crédito|outro>",
  "agro_segment": "<grãos|fibras|pecuária|horticultura|cafeicultura|geral>",
  "technical_depth": "<superficial|intermediário|especialista>",
  "core_argument": "<tese central em uma frase direta>",
  "argument_structure": "<fluxo lógico: ex. dado chocante → causa → solução → prova>",
  "technical_claims": ["<afirmação técnica 1>", "<afirmação técnica 2>"],
  "data_points": [{"value": "<número>", "context": "<contexto>", "source": "<fonte ou null>"}],
  "sources_referenced": ["<Embrapa>", "<MAPA>", "<pesquisa própria>"],
  "knowledge_assumptions": "<o que assume que a audiência já sabe>",
  "content_gaps": "<o que ficou de fora e enriqueceria o conteúdo>",
  "replication_template": "<fórmula replicável: ex. [DADO] + [CAUSA] + [SOLUÇÃO] + [CTA]>"
}
```

**User message:** caption + hashtags (no image re-fetch — reuses already-collected caption)

Saves `PostIntelligence` row, then calls `upsert_arguments()`.

### `src/analyzer/argument_extractor.py` — NEW

```python
def upsert_arguments(intelligence: PostIntelligence, post: Post, session: Session) -> None
```

Iterates `technical_claims` + flattened `data_points` text. For each:
1. Normalize text
2. Query `ArgumentBank` for exact match on normalized text
3. If exists: update `times_seen`, `source_post_ids`, recompute `virality_weight`
4. If new: compute `quality_score`, insert with `origin="extracted"`

### `api/routers/intelligence.py` — NEW

```
GET  /intelligence/posts                    → list posts with PostIntelligence (paginated, 20/page)
GET  /intelligence/posts/{post_id}          → full PostIntelligence for one post
GET  /intelligence/arguments                → ArgumentBank list (filter: topic_cluster, agro_segment; sort: score)
POST /intelligence/analyze                  → trigger batch analysis of unprocessed posts (returns count)
```

### `api/main.py` — MODIFY

Add second APScheduler job:
```python
scheduler.add_job(_run_daily_intelligence, "cron", hour=7, minute=0)
```

`_run_daily_intelligence()` queries posts without `PostIntelligence`, processes up to 50 per run.

### `src/carousel/generator.py` — MODIFY

Before calling GPT-4o, query top 5 arguments by combined score (no cluster filtering — theme is free text):
```python
args = session.query(ArgumentBank)
    .filter(ArgumentBank.origin == "extracted")
    .order_by((ArgumentBank.virality_weight * ArgumentBank.quality_score).desc())
    .limit(5).all()
```
Inject as `"argumentos_de_alto_desempenho"` in the user content JSON.

## Frontend

### New module in `lib/tree-data.ts`

Add "Inteligência" to an existing group (Análise) or create new group with two children:
- `inteligencia-posts` — Deep Dive por post
- `inteligencia-argumentos` — Banco de Argumentos

### `DrawerInteligenciaPosts.tsx` — NEW

- Fetches `GET /api/intelligence/posts` on mount
- Lists posts ordered by virality_score (shows handle, likes, depth badge)
- Clicking a post expands inline or navigates to detail view showing all `PostIntelligence` fields
- "Analisar novos" button → `POST /api/intelligence/analyze` with spinner

### `DrawerInteligenciaArgumentos.tsx` — NEW

- Fetches `GET /api/intelligence/arguments` on mount
- Filter chips: topic_cluster + agro_segment
- Each argument card shows: text, quality bar, virality bar, `times_seen`, source posts count
- "Usar no carrossel" button → sets topic in DrawerCarrossel and opens it

## Alembic Migration

New migration `005_post_intelligence.py`:
- Creates `post_intelligence` table
- Creates `argument_bank` table

## Testing

- `tests/test_post_intelligence.py`: mock GPT-4o, verify `analyze_post_intelligence()` stores row with all fields; verify skips already-analyzed posts
- `tests/test_argument_extractor.py`: verify `upsert_arguments()` inserts new arguments; verify de-duplication increments `times_seen`; verify quality_score formula
- `tests/test_api_intelligence.py`: `GET /intelligence/posts` returns 200; `GET /intelligence/arguments` filters by topic_cluster; `POST /intelligence/analyze` returns processed count
