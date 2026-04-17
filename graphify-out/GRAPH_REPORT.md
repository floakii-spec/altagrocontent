# Graph Report - /Users/floakii/Claudio/agro-content  (2026-04-17)

## Corpus Check
- 51 files · ~30,188 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 177 nodes · 280 edges · 29 communities detected
- Extraction: 54% EXTRACTED · 46% INFERRED · 0% AMBIGUOUS · INFERRED: 129 edges (avg confidence: 0.74)
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

## God Nodes (most connected - your core abstractions)
1. `Post` - 22 edges
2. `Profile` - 21 edges
3. `PostAnalysis` - 12 edges
4. `Base` - 11 edges
5. `ProfileVoice` - 9 edges
6. `NewsItem` - 9 edges
7. `get_session()` - 9 edges
8. `collect_profile()` - 8 edges
9. `analyze_post()` - 8 edges
10. `render()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `session()` --calls--> `db_session()`  [INFERRED]
  /Users/floakii/Claudio/agro-content/tests/test_models.py → tests/test_collector.py
- `test_basic_score()` --calls--> `calculate_virality_score()`  [INFERRED]
  tests/test_virality.py → src/analyzer/virality.py
- `test_score_clamped_to_one()` --calls--> `calculate_virality_score()`  [INFERRED]
  tests/test_virality.py → src/analyzer/virality.py
- `test_zero_followers_returns_zero()` --calls--> `calculate_virality_score()`  [INFERRED]
  tests/test_virality.py → src/analyzer/virality.py
- `test_zero_engagement_returns_zero()` --calls--> `calculate_virality_score()`  [INFERRED]
  tests/test_virality.py → src/analyzer/virality.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.11
Nodes (21): _build_approved_section(), generate_post(), Gera um post adaptado com base no post do concorrente, voz do autor e exemplos a, DeclarativeBase, generate_carousel(), Gera carrossel viral com base no tema, voz própria e último relatório semanal., Base, Carousel (+13 more)

### Community 1 - "Community 1"
Cohesion: 0.17
Nodes (22): collect_profile(), Coleta posts novos de um perfil. Tenta Apify primeiro, cai para Instaloader em c, Extract topic strings from raw_analysis JSON., Compare topics covered by competitor posts vs own posts.     Returns list of dic, Analisa um post com GPT-4o Vision. Se já analisado, retorna análise existente., Post, PostAnalysis, Profile (+14 more)

### Community 2 - "Community 2"
Cohesion: 0.21
Nodes (16): NewsItem, _extract_tags(), fetch_all_feeds(), _fetch_all_raw(), get_recent_news(), _parse_feed(), Return news items from the last `days` days, optionally filtered by tags., Poll all RSS feeds and save new items. Returns count of new items saved. (+8 more)

### Community 3 - "Community 3"
Cohesion: 0.18
Nodes (10): render(), _render_carousel(), _get_approved_examples(), _get_competitor_posts(), _get_voice(), render(), _get_engine(), get_session() (+2 more)

### Community 4 - "Community 4"
Cohesion: 0.16
Nodes (10): fetch_posts_apify(), Busca posts de um perfil via Apify Instagram Scraper.     Retorna lista de dicts, fetch_posts_instaloader(), _get_loader(), Busca posts via Instaloader com login para evitar bloqueios.     Retorna lista d, sync_all(), db_session(), test_fetch_posts_apify_maps_video_to_reel() (+2 more)

### Community 5 - "Community 5"
Cohesion: 0.2
Nodes (6): render(), analyze_post(), render_post_card(), render(), test_analyze_post_creates_analysis(), test_analyze_post_skips_already_analyzed()

### Community 6 - "Community 6"
Cohesion: 0.38
Nodes (9): compute_gaps(), _extract_topics(), _make_post_with_analysis(), _make_profile(), test_compute_gaps_identifies_uncovered_topic(), test_compute_gaps_no_competitors_returns_empty(), test_compute_gaps_returns_list(), test_extract_topics_empty() (+1 more)

### Community 7 - "Community 7"
Cohesion: 0.36
Nodes (6): get_seasonal_context(), Return the current month's agro seasonal context string., test_july_august_context(), test_march_april_context(), test_november_december_context(), test_returns_string()

### Community 8 - "Community 8"
Cohesion: 0.36
Nodes (6): test_basic_score(), test_score_clamped_to_one(), test_zero_engagement_returns_zero(), test_zero_followers_returns_zero(), calculate_virality_score(), Normaliza engajamento pelo número de seguidores. Retorna valor entre 0 e 1.

### Community 9 - "Community 9"
Cohesion: 0.4
Nodes (3): test_generate_voice_profile_creates_profile(), generate_voice_profile(), Analisa os posts do perfil próprio e gera um perfil de voz atualizado.

### Community 10 - "Community 10"
Cohesion: 0.5
Nodes (1): content_strategy_engine  Revision ID: 003 Revises: 002 Create Date: 2026-04-17 0

### Community 11 - "Community 11"
Cohesion: 0.5
Nodes (1): initial_schema  Revision ID: 001 Revises: Create Date: 2026-04-14 00:00:00.00000

### Community 12 - "Community 12"
Cohesion: 0.5
Nodes (1): content_studio  Revision ID: 002 Revises: a1b2c3d4e5f6 Create Date: 2026-04-15 0

### Community 13 - "Community 13"
Cohesion: 0.67
Nodes (0): 

### Community 14 - "Community 14"
Cohesion: 0.67
Nodes (0): 

### Community 15 - "Community 15"
Cohesion: 0.67
Nodes (0): 

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (0): 

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (0): 

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (0): 

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 1.0
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
Nodes (1): Busca posts de um perfil via Apify Instagram Scraper.     Retorna lista de dicts

## Knowledge Gaps
- **8 isolated node(s):** `content_strategy_engine  Revision ID: 003 Revises: 002 Create Date: 2026-04-17 0`, `initial_schema  Revision ID: 001 Revises: Create Date: 2026-04-14 00:00:00.00000`, `content_studio  Revision ID: 002 Revises: a1b2c3d4e5f6 Create Date: 2026-04-15 0`, `Busca posts de um perfil via Apify Instagram Scraper.     Retorna lista de dicts`, `Busca posts via Instaloader com login para evitar bloqueios.     Retorna lista d` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 16`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (1 nodes): `app.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `config.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (1 nodes): `Busca posts de um perfil via Apify Instagram Scraper.     Retorna lista de dicts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Post` connect `Community 1` to `Community 0`, `Community 9`, `Community 4`, `Community 6`?**
  _High betweenness centrality (0.149) - this node is a cross-community bridge._
- **Why does `NewsItem` connect `Community 2` to `Community 0`, `Community 1`?**
  _High betweenness centrality (0.133) - this node is a cross-community bridge._
- **Why does `Profile` connect `Community 1` to `Community 0`, `Community 9`, `Community 5`, `Community 6`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `Post` (e.g. with `Extract topic strings from raw_analysis JSON.` and `Compare topics covered by competitor posts vs own posts.     Returns list of dic`) actually correct?**
  _`Post` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `Profile` (e.g. with `Extract topic strings from raw_analysis JSON.` and `Compare topics covered by competitor posts vs own posts.     Returns list of dic`) actually correct?**
  _`Profile` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `PostAnalysis` (e.g. with `Extract topic strings from raw_analysis JSON.` and `Compare topics covered by competitor posts vs own posts.     Returns list of dic`) actually correct?**
  _`PostAnalysis` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `ProfileVoice` (e.g. with `session_with_context()` and `generate_voice_profile()`) actually correct?**
  _`ProfileVoice` has 7 INFERRED edges - model-reasoned connections that need verification._