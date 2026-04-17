# Graph Report - /Users/floakii/Claudio/agro-content  (2026-04-17)

## Corpus Check
- 88 files · ~304,873 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 305 nodes · 482 edges · 54 communities detected
- Extraction: 57% EXTRACTED · 43% INFERRED · 0% AMBIGUOUS · INFERRED: 209 edges (avg confidence: 0.71)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]

## God Nodes (most connected - your core abstractions)
1. `Post` - 39 edges
2. `Profile` - 35 edges
3. `session()` - 20 edges
4. `PostAnalysis` - 20 edges
5. `ProfileVoice` - 15 edges
6. `Base` - 11 edges
7. `NewsItem` - 11 edges
8. `get_session()` - 10 edges
9. `WeeklyReport` - 9 edges
10. `collect_profile()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `test_generate_weekly_report_creates_report()` --calls--> `generate_weekly_report()`  [INFERRED]
  tests/test_weekly_report.py → src/reporter/weekly_report.py
- `session()` --calls--> `db_session()`  [INFERRED]
  /Users/floakii/Claudio/agro-content/tests/test_models.py → tests/test_collector.py
- `session_with_analyses()` --calls--> `session()`  [INFERRED]
  tests/test_weekly_report.py → /Users/floakii/Claudio/agro-content/tests/test_models.py
- `test_basic_score()` --calls--> `calculate_virality_score()`  [INFERRED]
  tests/test_virality.py → src/analyzer/virality.py
- `test_score_clamped_to_one()` --calls--> `calculate_virality_score()`  [INFERRED]
  tests/test_virality.py → src/analyzer/virality.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.12
Nodes (31): BaseModel, add_profile(), list_competitors(), ProfileIn, ProfileOut, SyncError, SyncResponse, DeclarativeBase (+23 more)

### Community 1 - "Community 1"
Cohesion: 0.1
Nodes (14): override_db(), test_generate_carousel(), test_list_carousels_returns_history(), override_db(), override_db(), test_list_news_returns_items(), test_refresh_news(), override_db() (+6 more)

### Community 2 - "Community 2"
Cohesion: 0.16
Nodes (20): NewsItem, list_news(), _extract_tags(), fetch_all_feeds(), _fetch_all_raw(), get_recent_news(), _parse_feed(), Return news items from the last `days` days, optionally filtered by tags. (+12 more)

### Community 3 - "Community 3"
Cohesion: 0.11
Nodes (11): render(), _render_carousel(), render(), _get_engine(), get_session(), get_db(), render_post_card(), render() (+3 more)

### Community 4 - "Community 4"
Cohesion: 0.15
Nodes (13): fetch_posts_apify(), Busca posts de um perfil via Apify Instagram Scraper.     Retorna lista de dicts, collect_profile(), Coleta posts novos de um perfil. Tenta Apify primeiro, cai para Instaloader em c, fetch_posts_instaloader(), _get_loader(), Busca posts via Instaloader com login para evitar bloqueios.     Retorna lista d, db_session() (+5 more)

### Community 5 - "Community 5"
Cohesion: 0.16
Nodes (12): sync_profiles(), analyze_post(), Analisa um post com GPT-4o Vision. Se já analisado, retorna análise existente., session_with_post(), test_analyze_post_creates_analysis(), test_analyze_post_skips_already_analyzed(), test_basic_score(), test_score_clamped_to_one() (+4 more)

### Community 6 - "Community 6"
Cohesion: 0.17
Nodes (10): WeeklyReport, generate_report(), list_reports(), ReportOut, override_db(), test_generate_report(), test_list_reports_returns_data(), test_create_weekly_report() (+2 more)

### Community 7 - "Community 7"
Cohesion: 0.26
Nodes (12): gap_analysis(), compute_gaps(), _extract_topics(), Extract topic strings from raw_analysis JSON., Compare topics covered by competitor posts vs own posts.     Returns list of dic, _make_post_with_analysis(), _make_profile(), test_compute_gaps_identifies_uncovered_topic() (+4 more)

### Community 8 - "Community 8"
Cohesion: 0.2
Nodes (10): ProfileVoice, session_with_own_profile(), test_generate_voice_profile_creates_profile(), analyze_voice(), analyze_voice(), Analisa os posts do perfil próprio e gera/atualiza o perfil de voz., get_voice(), generate_voice_profile() (+2 more)

### Community 9 - "Community 9"
Cohesion: 0.22
Nodes (10): CarouselGenerateIn, CarouselOut, generate(), list_carousels(), generate_carousel(), Gera carrossel viral com base no tema, voz própria e último relatório semanal., Carousel, session_with_context() (+2 more)

### Community 10 - "Community 10"
Cohesion: 0.3
Nodes (9): drillInto(), fadeIn(), makeNode(), makePulse(), makeRings(), renderHome(), setPos(), startOrbit() (+1 more)

### Community 11 - "Community 11"
Cohesion: 0.29
Nodes (8): _build_approved_section(), generate_post(), Gera um post adaptado com base no post do concorrente, voz do autor e exemplos a, _get_approved_examples(), _get_competitor_posts(), _get_voice(), render(), generate()

### Community 12 - "Community 12"
Cohesion: 0.25
Nodes (0): 

### Community 13 - "Community 13"
Cohesion: 0.36
Nodes (6): get_seasonal_context(), Return the current month's agro seasonal context string., test_july_august_context(), test_march_april_context(), test_november_december_context(), test_returns_string()

### Community 14 - "Community 14"
Cohesion: 0.5
Nodes (2): Badge(), cn()

### Community 15 - "Community 15"
Cohesion: 0.5
Nodes (1): content_strategy_engine  Revision ID: 003 Revises: 002 Create Date: 2026-04-17 0

### Community 16 - "Community 16"
Cohesion: 0.5
Nodes (1): initial_schema  Revision ID: 001 Revises: Create Date: 2026-04-14 00:00:00.00000

### Community 17 - "Community 17"
Cohesion: 0.5
Nodes (1): content_studio  Revision ID: 002 Revises: a1b2c3d4e5f6 Create Date: 2026-04-15 0

### Community 18 - "Community 18"
Cohesion: 0.67
Nodes (0): 

### Community 19 - "Community 19"
Cohesion: 0.67
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 0.67
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 0.67
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (0): 

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (0): 

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (0): 

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (0): 

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (0): 

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (0): 

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (0): 

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (0): 

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (0): 

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (0): 

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (0): 

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (0): 

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (0): 

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (0): 

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (0): 

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (0): 

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (0): 

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (1): Busca posts de um perfil via Apify Instagram Scraper.     Retorna lista de dicts

## Knowledge Gaps
- **8 isolated node(s):** `content_strategy_engine  Revision ID: 003 Revises: 002 Create Date: 2026-04-17 0`, `initial_schema  Revision ID: 001 Revises: Create Date: 2026-04-14 00:00:00.00000`, `content_studio  Revision ID: 002 Revises: a1b2c3d4e5f6 Create Date: 2026-04-15 0`, `Busca posts de um perfil via Apify Instagram Scraper.     Retorna lista de dicts`, `Busca posts via Instaloader com login para evitar bloqueios.     Retorna lista d` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 22`** (2 nodes): `RootLayout()`, `layout.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (2 nodes): `cn()`, `button.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (2 nodes): `generate()`, `DrawerRelatorios.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (2 nodes): `adapt()`, `DrawerStudio.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (2 nodes): `generate()`, `DrawerCarrossel.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (2 nodes): `ModuleDrawer()`, `ModuleDrawer.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (2 nodes): `test_health()`, `test_api_main.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (2 nodes): `health()`, `main.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (1 nodes): `postcss.config.mjs`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `next-env.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (1 nodes): `next.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (1 nodes): `page.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (1 nodes): `Sidebar.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `DrawerComingSoon.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (1 nodes): `DrawerNoticias.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (1 nodes): `DrawerIdentidade.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `DrawerConcorrentes.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (1 nodes): `app.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `config.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `Busca posts de um perfil via Apify Instagram Scraper.     Retorna lista de dicts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Post` connect `Community 0` to `Community 1`, `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 8`, `Community 11`?**
  _High betweenness centrality (0.150) - this node is a cross-community bridge._
- **Why does `Profile` connect `Community 0` to `Community 1`, `Community 3`, `Community 4`, `Community 5`, `Community 7`, `Community 8`, `Community 9`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Why does `NewsItem` connect `Community 2` to `Community 0`, `Community 1`?**
  _High betweenness centrality (0.079) - this node is a cross-community bridge._
- **Are the 37 inferred relationships involving `Post` (e.g. with `CompetitorPostOut` and `GenerateIn`) actually correct?**
  _`Post` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 33 inferred relationships involving `Profile` (e.g. with `CompetitorPostOut` and `GenerateIn`) actually correct?**
  _`Profile` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `session()` (e.g. with `override_db()` and `test_list_competitors_returns_post_count()`) actually correct?**
  _`session()` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `PostAnalysis` (e.g. with `CompetitorPostOut` and `GenerateIn`) actually correct?**
  _`PostAnalysis` has 18 INFERRED edges - model-reasoned connections that need verification._