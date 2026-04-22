# Graph Report - .  (2026-04-22)

## Corpus Check
- 98 files · ~323,005 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 443 nodes · 790 edges · 63 communities detected
- Extraction: 59% EXTRACTED · 41% INFERRED · 0% AMBIGUOUS · INFERRED: 323 edges (avg confidence: 0.71)
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
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]

## God Nodes (most connected - your core abstractions)
1. `Post` - 56 edges
2. `Profile` - 48 edges
3. `session()` - 43 edges
4. `PostAnalysis` - 26 edges
5. `ProfileVoice` - 17 edges
6. `PostIntelligence` - 15 edges
7. `Base` - 14 edges
8. `analyze_post_intelligence()` - 14 edges
9. `NewsItem` - 13 edges
10. `generate_post()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `override_db()` --calls--> `session()`  [INFERRED]
  tests/test_api_competitors.py → /Users/floakii/Claudio/agro-content/tests/test_models.py
- `override_db()` --calls--> `session()`  [INFERRED]
  tests/test_api_intelligence.py → /Users/floakii/Claudio/agro-content/tests/test_models.py
- `test_refresh_news()` --calls--> `Post`  [INFERRED]
  /Users/floakii/Claudio/agro-content/tests/test_api_news.py → src/models.py
- `test_generate_carousel()` --calls--> `Post`  [INFERRED]
  /Users/floakii/Claudio/agro-content/tests/test_api_carousel.py → src/models.py
- `test_refresh_suggestions()` --calls--> `Post`  [INFERRED]
  /Users/floakii/Claudio/agro-content/tests/test_api_carousel.py → src/models.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (48): collect_profile(), _merge_post(), Coleta posts novos de um perfil. Tenta Apify primeiro, cai para Instaloader em c, Coleta posts novos de um perfil. Tenta Apify primeiro, cai para Instaloader em c, add_profile(), list_competitors(), ProfileIn, ProfileOut (+40 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (43): BaseModel, CarouselGenerateIn, CarouselOut, CarouselSuggestionOut, generate(), get_suggestions(), list_carousels(), refresh_suggestions() (+35 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (26): _average_virality(), _candidate_texts(), _compute_quality_score(), _normalize(), remove_arguments_for_post(), upsert_arguments(), override_db(), test_generate_carousel() (+18 more)

### Community 3 - "Community 3"
Cohesion: 0.11
Nodes (23): NewsItem, list_news(), _extract_tags(), fetch_all_feeds(), _fetch_all_raw(), get_recent_news(), _parse_feed(), Return news items from the last `days` days, optionally filtered by tags. (+15 more)

### Community 4 - "Community 4"
Cohesion: 0.13
Nodes (13): _get_engine(), get_session(), get_db(), load(), refresh(), _run_daily_intelligence(), _run_daily_suggestions(), _mock_openai() (+5 more)

### Community 5 - "Community 5"
Cohesion: 0.17
Nodes (18): _build_approved_section(), _extract_numeric_fragments(), _format_json(), _format_note(), generate_post(), _load_structural_patterns(), _parse_json_response(), _request_generation() (+10 more)

### Community 6 - "Community 6"
Cohesion: 0.14
Nodes (16): _append_unique(), _extract_slide_urls(), fetch_posts_apify(), Busca posts de um perfil via Apify Instagram Scraper.     Se since_date for forn, _append_unique(), _extract_sidecar_slide_urls(), fetch_posts_instaloader(), _get_loader() (+8 more)

### Community 7 - "Community 7"
Cohesion: 0.27
Nodes (11): analyze_post_intelligence(), _coerce_slide_urls(), _snapshot_intelligence(), _to_data_url(), _transcribe_visual_assets(), _make_post(), _mock_gpt(), test_analyze_persists_to_db() (+3 more)

### Community 8 - "Community 8"
Cohesion: 0.3
Nodes (9): drillInto(), fadeIn(), makeNode(), makePulse(), makeRings(), renderHome(), setPos(), startOrbit() (+1 more)

### Community 9 - "Community 9"
Cohesion: 0.33
Nodes (10): gap_analysis(), compute_gaps(), _extract_topics(), _make_post_with_analysis(), _make_profile(), test_compute_gaps_identifies_uncovered_topic(), test_compute_gaps_no_competitors_returns_empty(), test_compute_gaps_returns_list() (+2 more)

### Community 10 - "Community 10"
Cohesion: 0.24
Nodes (5): override_db(), _seed_intelligence(), test_get_intelligence_by_post_id(), test_list_arguments_with_filter(), test_list_intelligence_returns_data()

### Community 11 - "Community 11"
Cohesion: 0.25
Nodes (0): 

### Community 12 - "Community 12"
Cohesion: 0.32
Nodes (5): generate_report(), list_reports(), ReportOut, test_generate_weekly_report_creates_report(), generate_weekly_report()

### Community 13 - "Community 13"
Cohesion: 0.36
Nodes (6): test_basic_score(), test_score_clamped_to_one(), test_zero_engagement_returns_zero(), test_zero_followers_returns_zero(), calculate_virality_score(), Normaliza engajamento pelo número de seguidores. Retorna valor entre 0 e 1.

### Community 14 - "Community 14"
Cohesion: 0.32
Nodes (5): test_generate_voice_profile_creates_profile(), analyze_voice(), get_voice(), generate_voice_profile(), VoiceOut

### Community 15 - "Community 15"
Cohesion: 0.36
Nodes (6): get_seasonal_context(), Return the current month's agro seasonal context string., test_july_august_context(), test_march_april_context(), test_november_december_context(), test_returns_string()

### Community 16 - "Community 16"
Cohesion: 0.7
Nodes (4): addProfile(), load(), removeProfile(), sync()

### Community 17 - "Community 17"
Cohesion: 0.5
Nodes (2): generate(), loadHistory()

### Community 18 - "Community 18"
Cohesion: 0.5
Nodes (0): 

### Community 19 - "Community 19"
Cohesion: 0.5
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 0.83
Nodes (3): analyzeNew(), analyzeProfile(), load()

### Community 21 - "Community 21"
Cohesion: 0.5
Nodes (2): Badge(), cn()

### Community 22 - "Community 22"
Cohesion: 0.5
Nodes (1): content_strategy_engine  Revision ID: 003 Revises: 002 Create Date: 2026-04-17 0

### Community 23 - "Community 23"
Cohesion: 0.5
Nodes (1): fix profile_voice tone column from VARCHAR(100) to TEXT  Revision ID: 006 Revise

### Community 24 - "Community 24"
Cohesion: 0.5
Nodes (1): initial_schema  Revision ID: 001 Revises: Create Date: 2026-04-14 00:00:00.00000

### Community 25 - "Community 25"
Cohesion: 0.5
Nodes (1): content_studio  Revision ID: 002 Revises: a1b2c3d4e5f6 Create Date: 2026-04-15 0

### Community 26 - "Community 26"
Cohesion: 0.5
Nodes (1): add carousel intelligence fields  Revision ID: 007 Revises: 006 Create Date: 202

### Community 27 - "Community 27"
Cohesion: 0.5
Nodes (1): post_intelligence and argument_bank tables  Revision ID: 005 Revises: 004 Create

### Community 28 - "Community 28"
Cohesion: 0.5
Nodes (1): carousel_suggestions table  Revision ID: 004 Revises: 003 Create Date: 2026-04-1

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (2): proxy(), sha256hex()

### Community 30 - "Community 30"
Cohesion: 0.67
Nodes (1): POST()

### Community 31 - "Community 31"
Cohesion: 0.67
Nodes (0): 

### Community 32 - "Community 32"
Cohesion: 0.67
Nodes (0): 

### Community 33 - "Community 33"
Cohesion: 0.67
Nodes (0): 

### Community 34 - "Community 34"
Cohesion: 0.67
Nodes (0): 

### Community 35 - "Community 35"
Cohesion: 0.67
Nodes (0): 

### Community 36 - "Community 36"
Cohesion: 0.67
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
Nodes (0): 

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (0): 

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (0): 

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (0): 

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (0): 

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (0): 

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (1): Busca posts de um perfil via Apify Instagram Scraper.     Se since_date for forn

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (1): Busca posts via Instaloader com login para evitar bloqueios.     Retorna lista d

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (1): Busca posts de um perfil via Apify Instagram Scraper.     Retorna lista de dicts

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (1): Busca posts de um perfil via Apify Instagram Scraper.     Retorna lista de dicts

## Knowledge Gaps
- **15 isolated node(s):** `content_strategy_engine  Revision ID: 003 Revises: 002 Create Date: 2026-04-17 0`, `fix profile_voice tone column from VARCHAR(100) to TEXT  Revision ID: 006 Revise`, `initial_schema  Revision ID: 001 Revises: Create Date: 2026-04-14 00:00:00.00000`, `content_studio  Revision ID: 002 Revises: a1b2c3d4e5f6 Create Date: 2026-04-15 0`, `add carousel intelligence fields  Revision ID: 007 Revises: 006 Create Date: 202` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 37`** (2 nodes): `RootLayout()`, `layout.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (2 nodes): `proxy()`, `route.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (2 nodes): `handleSubmit()`, `page.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (2 nodes): `Sidebar()`, `Sidebar.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (2 nodes): `cn()`, `button.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (2 nodes): `ModuleDrawer()`, `ModuleDrawer.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (2 nodes): `test_health()`, `test_api_main.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (1 nodes): `postcss.config.mjs`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `next-env.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `next.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `page.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (1 nodes): `DrawerComingSoon.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `config.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (1 nodes): `Busca posts de um perfil via Apify Instagram Scraper.     Se since_date for forn`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `Busca posts via Instaloader com login para evitar bloqueios.     Retorna lista d`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `Busca posts de um perfil via Apify Instagram Scraper.     Retorna lista de dicts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `Busca posts de um perfil via Apify Instagram Scraper.     Retorna lista de dicts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Post` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 6`, `Community 7`, `Community 9`, `Community 10`, `Community 14`?**
  _High betweenness centrality (0.143) - this node is a cross-community bridge._
- **Why does `session()` connect `Community 2` to `Community 0`, `Community 1`, `Community 3`, `Community 4`, `Community 6`, `Community 7`, `Community 10`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Why does `Profile` connect `Community 0` to `Community 1`, `Community 2`, `Community 7`, `Community 9`, `Community 10`, `Community 14`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 54 inferred relationships involving `Post` (e.g. with `PostIntelligenceOut` and `ArgumentBankOut`) actually correct?**
  _`Post` has 54 INFERRED edges - model-reasoned connections that need verification._
- **Are the 46 inferred relationships involving `Profile` (e.g. with `PostIntelligenceOut` and `ArgumentBankOut`) actually correct?**
  _`Profile` has 46 INFERRED edges - model-reasoned connections that need verification._
- **Are the 42 inferred relationships involving `session()` (e.g. with `override_db()` and `test_list_competitors_returns_post_count()`) actually correct?**
  _`session()` has 42 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `PostAnalysis` (e.g. with `PostIntelligenceOut` and `ArgumentBankOut`) actually correct?**
  _`PostAnalysis` has 24 INFERRED edges - model-reasoned connections that need verification._