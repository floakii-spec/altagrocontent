# Carousel Theme Suggestions Design

## Goal

Add an AI-driven theme suggestion system to the carousel drawer. Suggestions are generated daily by APScheduler using competitor analysis, news headlines, and GPT-4o's own agro market knowledge. Users see 6 clickable chips that auto-fill the carousel theme textarea.

## Architecture

```
APScheduler (daily 06:00 UTC)
    └─► src/carousel/theme_suggester.py
            ├─ compute_gaps(db)           → top 5 gap topics (competitors vs own)
            ├─ top viral posts (db)       → top 5 posts by virality_score > 0.5
            ├─ recent news headlines (db) → last 48h from RSS feeds
            └─► GPT-4o                   → 6 {title, rationale} suggestions

Result stored in `carousel_suggestions` table (one row per generation)

GET  /carousel/suggestions          → reads latest row (instant)
POST /carousel/suggestions/refresh  → regenerates now, stores, returns result (~10s)

DrawerCarrossel (frontend)
    └─ "Sugestões IA" section → 6 clickable chips → fills theme textarea
```

## Database

New table `carousel_suggestions`:

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| themes | JSON | List of `{title: str, rationale: str}` |
| generated_at | DateTime(tz) | UTC timestamp |

No FK to profiles or posts — suggestions are a snapshot, not live references.

## Backend

### `src/carousel/theme_suggester.py`

Single public function:
```python
def generate_theme_suggestions(session: Session) -> CarouselSuggestion
```

**Data gathering:**
1. `compute_gaps(session)` → take top 5 by `gap_score`
2. Query `PostAnalysis` joined to `Post` where `virality_score > 0.5`, order by `virality_score desc`, limit 5 → extract captions
3. Query `NewsItem` where `published_at > now - 48h`, limit 10 → extract titles

**Prompt to GPT-4o:**
- System: "Você é especialista em marketing de conteúdo para o agronegócio brasileiro no Instagram. Crie 6 sugestões de tema para carrosséis com alta chance de viralização. Use os dados fornecidos e complemente com seu próprio conhecimento sobre sazonalidade, mercado e tendências agro."
- User: formatted block with gap topics, viral captions, and news headlines
- Response format: JSON array of `{title, rationale}` — rationale is one short sentence explaining the data signal behind the suggestion

**Fallback:** if all three data sources are empty (no posts, no news), prompt GPT-4o with only its own knowledge about current agro season and market.

**Storage:** saves result as new `CarouselSuggestion` row, returns it.

### `api/routers/carousel.py` — new endpoints

```
GET  /carousel/suggestions         → latest CarouselSuggestion or 204 if none yet
POST /carousel/suggestions/refresh → calls generate_theme_suggestions(), returns result
```

### `api/main.py` — APScheduler startup

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(run_daily_suggestions, "cron", hour=6, minute=0)
scheduler.start()
```

`run_daily_suggestions()` opens a DB session, calls `generate_theme_suggestions()`, closes session.

Scheduler starts on FastAPI `startup` event and shuts down on `shutdown`.

## Frontend — `web/components/drawers/DrawerCarrossel.tsx`

New section above the textarea:

```
┌─ Sugestões IA ──────────────────── ↻ ┐
│  [chip 1]  [chip 2]  [chip 3]        │
│  [chip 4]  [chip 5]  [chip 6]        │
└───────────────────────────────────────┘
```

- Fetches `GET /api/carousel/suggestions` on mount alongside history
- If 204/empty: shows "A IA vai gerar sugestões às 06:00 ou clique em ↻"
- Clicking a chip: sets `topic` state → fills textarea
- ↻ button: calls `POST /api/carousel/suggestions/refresh` with spinner (~10s)
- After refresh: updates displayed chips

## File Structure

```
src/carousel/theme_suggester.py     NEW — suggestion generation logic
api/routers/carousel.py             MODIFY — add 2 endpoints
api/main.py                         MODIFY — add APScheduler startup/shutdown
src/models.py                       MODIFY — add CarouselSuggestion model
alembic/versions/                   NEW — migration for carousel_suggestions table
web/components/drawers/DrawerCarrossel.tsx  MODIFY — add suggestions UI section
```

## Testing

- `tests/test_carousel_suggestions.py`: mock GPT-4o call, verify `generate_theme_suggestions()` stores a row with 6 items; verify fallback when DB is empty
- `tests/test_api_carousel.py`: add tests for `GET /carousel/suggestions` (204 when empty, 200 with data) and `POST /carousel/suggestions/refresh`
