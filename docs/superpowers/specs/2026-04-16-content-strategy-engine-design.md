# Content Strategy Engine — Design Spec

**Date:** 2026-04-16
**Status:** Approved for implementation

---

## Goal

Transform the system from a post copier into a true agro content strategist: monitors the market in real time, understands Nathan's audience funnel, identifies competitor gaps, generates a structured weekly editorial calendar, and self-improves as Nathan's own posts accumulate performance data.

---

## Context

Nathan (@nathanlimagro) is a 15-year agronomy consultant running Phos Consultoria and Agroroot. His primary monetization goal on Instagram is capturing leads for **Confraria de Vendas no Agro** — a paid community for agro sales professionals. His content must educate top-of-funnel producers, qualify middle-funnel practitioners, and convert bottom-funnel salespeople into Confraria members.

---

## Feature Scope

### 1. Carousel Deep Analysis
Collect **all slide images** from carousel posts (not just the cover). Analyze each slide individually via GPT-4o Vision, then extract the narrative structure: hook slide → content slides → CTA slide. Store as structured JSON in the `Post` record.

**Why:** Carousels are the highest-engagement format in agro. Understanding their internal structure (how top creators build tension across slides) is essential for generating effective carousels for Nathan.

### 2. Agro News Monitoring
Poll RSS feeds from major agro news sources every 6 hours:
- Canal Rural (`https://www.canalrural.com.br/feed/`)
- Globo Rural (`https://revistagloborural.globo.com/rss`)
- AgroLink (`https://www.agrolink.com.br/noticias/rss.aspx`)
- Notícias Agrícolas (`https://www.noticiasagricolas.com.br/rss/noticias.xml`)

Store headline, summary, source, URL, published_at, and auto-extracted topic tags (soja, milho, mercado, clima, tecnologia, etc.).

### 3. AI as Agro Market Expert
The content generation engine does NOT depend on a specific competitor post. Instead it synthesizes:
- Recent news (last 7 days, filtered by relevance to Nathan's niche)
- Seasonal agro context (which crops are in which phase this month)
- Competitor gap analysis (what competitors are NOT covering)
- Nathan's voice profile
- Approved post examples

It outputs original content ideas with rationale — why this topic matters right now, for whom, and what the business angle is.

### 4. Funnel-Aware Content Strategy
Every generated piece of content is tagged with a funnel stage:

| Stage | Objective | Audience | CTA |
|-------|-----------|----------|-----|
| **Topo** | Reach & awareness | Produtores rurais, técnicos | Seguir, salvar |
| **Meio** | Authority & trust | Consultores, agrônomos, revendedores | Comentar, compartilhar |
| **Fundo** | Conversion | Profissionais de vendas no agro | Entrar na Confraria |

### 5. Seasonal Agro Calendar
Built-in monthly context for Brazil's main crops:

| Month | Context |
|-------|---------|
| Jan–Feb | Soja: desenvolvimento vegetativo no cerrado/sul |
| Mar–Apr | Soja: colheita no Centro-Oeste; 2ª safra milho: desenvolvimento |
| May–Jun | 2ª safra milho: colheita; entressafra; planejamento próxima safra |
| Jul–Aug | Planejamento safra soja; mercado de insumos aquecido |
| Sep–Oct | Plantio soja começa; cana: colheita plena; café: colheita arábica |
| Nov–Dec | Soja: plantio consolidado; milho verão: início |

The generator uses this context to make content feel timely and expert.

### 6. Weekly Editorial Calendar
Generate a 7-day content plan with funnel balance. Default structure:

- **Segunda:** Topo (educação/provocação)
- **Quarta:** Meio (técnico/prático)
- **Sexta:** Fundo (CTA explícito para Confraria)
- **Sábado:** Topo (curiosidade/dado de mercado)

Each calendar entry: topic, funnel stage, format suggestion (carousel/feed/reel), main angle, proposed hook.

### 7. Competitor Gap Analysis
Aggregate all analyzed competitor posts by topic. Compare against Nathan's own posts. Surface topics where:
- Competitors post heavily but Nathan has zero or weak coverage
- Nathan has a unique expertise angle that competitors miss
- A topic is trending in the news but no one in his niche is covering it on Instagram

### 8. Performance Feedback Loop
When Nathan's own posts (@nathanlimagro) are collected (via Apify or Instaloader), store likes + comments. After any post has 7+ days of data, compute an engagement_rate. Feed the top-performing posts back into the generator as additional approved examples, weighted by performance.

### 9. Hook Variations
For every generated post, produce 3 hook alternatives:
- **Provocação:** challenges a common belief
- **Dado:** leads with a surprising stat or market fact
- **Pergunta direta:** asks the reader something they can't ignore

Nathan picks the hook he likes best before saving.

---

## Data Model Changes

### Modify: `Post`
```python
slides: Mapped[list] = mapped_column(JSON, default=list)
# List of image URLs (ordered), populated for carousel posts
```

### Modify: `PostAnalysis`
```python
carousel_narrative: Mapped[dict] = mapped_column(JSON, default=dict)
# { "slide_count": int, "slides": [{index, content_type, text, role}], "narrative_arc": str }
```

### New: `NewsItem`
```python
class NewsItem(Base):
    __tablename__ = "news_items"
    id: Mapped[int]
    source: Mapped[str]        # "canal_rural" | "globo_rural" | "agrolink" | "noticias_agricolas"
    title: Mapped[str]
    summary: Mapped[Optional[str]]
    url: Mapped[str]           # unique
    published_at: Mapped[datetime]
    tags: Mapped[list]         # JSON: ["soja", "mercado", "tecnologia"]
    fetched_at: Mapped[datetime]
```

### New: `ContentCalendar`
```python
class ContentCalendar(Base):
    __tablename__ = "content_calendars"
    id: Mapped[int]
    week_start: Mapped[datetime]
    entries: Mapped[list]      # JSON: [{day, funnel_stage, format, topic, angle, hook}]
    generated_at: Mapped[datetime]
```

### Modify: `GeneratedPost`
```python
funnel_stage: Mapped[Optional[str]]   # "topo" | "meio" | "fundo"
format: Mapped[Optional[str]]          # "carousel" | "feed" | "reel"
hook_variations: Mapped[dict]          # JSON: {"provocacao": str, "dado": str, "pergunta": str}
news_item_ids: Mapped[list]            # JSON: [int] — news that inspired this post
```

---

## New Services

### `src/collector/news_monitor.py`
- `fetch_all_feeds() -> List[NewsItem]` — polls all 4 RSS feeds, deduplicates by URL, saves new items
- `get_recent_news(days: int, tags: List[str]) -> List[NewsItem]` — query helper

### `src/collector/carousel_collector.py`
- `collect_carousel_slides(post: Post, loader) -> List[str]` — downloads all slide images from a carousel post, returns list of URLs (stored locally or as base64)

### `src/analyzer/carousel_analyzer.py`
- `analyze_carousel(post: Post, session: Session) -> PostAnalysis` — sends all slides to GPT-4o Vision, extracts slide-by-slide content + narrative arc

### `src/analyzer/gap_analyzer.py`
- `compute_gaps(session: Session) -> dict` — aggregates competitor topics vs Nathan's topics, returns ranked gap list

### `src/generator/strategy_engine.py`
- `generate_content_idea(funnel_stage: str, session: Session) -> GeneratedPost` — AI market expert mode: uses news + seasonal context + gaps + voice to generate original idea
- `_get_seasonal_context() -> str` — returns current month's crop context string

### `src/generator/calendar_generator.py`
- `generate_weekly_calendar(session: Session) -> ContentCalendar` — generates 7-day plan with 4 posts, balanced funnel

---

## Dashboard Changes

### New tab: "📰 Notícias" (`dashboard/tabs/news.py`)
- Shows last 48h of monitored news, filterable by tag
- "Atualizar feeds" button triggers `fetch_all_feeds()`
- Each news item has "Usar como base" button → opens Content Studio with that news pre-loaded

### New tab: "📅 Calendário" (`dashboard/tabs/calendar.py`)
- Displays current week's editorial plan
- "Gerar Calendário" button → calls `generate_weekly_calendar()`
- Each calendar entry: funnel stage badge, format, topic, hook, "Desenvolver" button

### Modified: "✍️ Criar Conteúdo" (`dashboard/tabs/content_studio.py`)
- Add **Strategy Mode** toggle: "Inspiração em post" vs "Ideia de mercado"
- Strategy Mode: user selects funnel stage → system generates original idea from market intel
- Generated posts show 3 hook variations (radio button to pick one)
- Approved post shows performance_score if available (from own post analytics)

### Modified: Sidebar / Settings
- Add "Intervalo de atualização de notícias" setting (default: 6h)

---

## Alembic Migration

Single migration `003_content_strategy_engine.py`:
- Add `slides` column to `posts`
- Add `carousel_narrative` column to `post_analyses`
- Create `news_items` table
- Create `content_calendars` table
- Add `funnel_stage`, `format`, `hook_variations`, `news_item_ids` to `generated_posts`

---

## Out of Scope (this iteration)

- Automatic posting to Instagram
- Direct Apify carousel slide collection (done manually via Apify dashboard for now)
- Email/Slack notifications for new news
- Multi-profile support (only @nathanlimagro)

---

## Success Criteria

1. News monitor fetches and deduplicates articles from 4 RSS sources
2. Carousel analyzer extracts narrative structure from a multi-slide post
3. "Ideia de mercado" mode generates a post idea with no competitor post required
4. Weekly calendar generates 4 entries with correct funnel distribution
5. Competitor gap analysis surfaces at least 3 uncovered topics
6. Hook variations always produce 3 distinct alternatives
7. All generated posts carry a funnel_stage tag
