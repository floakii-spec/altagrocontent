# Graph Report - .  (2026-04-16)

## Corpus Check
- 44 files · ~26,427 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 127 nodes · 184 edges · 25 communities detected
- Extraction: 53% EXTRACTED · 47% INFERRED · 0% AMBIGUOUS · INFERRED: 87 edges (avg confidence: 0.73)
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

## God Nodes (most connected - your core abstractions)
1. `Post` - 16 edges
2. `Profile` - 15 edges
3. `Base` - 9 edges
4. `ProfileVoice` - 9 edges
5. `get_session()` - 9 edges
6. `PostAnalysis` - 8 edges
7. `collect_profile()` - 8 edges
8. `analyze_post()` - 8 edges
9. `render()` - 7 edges
10. `WeeklyReport` - 7 edges

## Surprising Connections (you probably didn't know these)
- `session_with_analyses()` --calls--> `PostAnalysis`  [INFERRED]
  tests/test_weekly_report.py → src/models.py
- `test_generate_weekly_report_creates_report()` --calls--> `generate_weekly_report()`  [INFERRED]
  tests/test_weekly_report.py → src/reporter/weekly_report.py
- `test_basic_score()` --calls--> `calculate_virality_score()`  [INFERRED]
  tests/test_virality.py → src/analyzer/virality.py
- `test_score_clamped_to_one()` --calls--> `calculate_virality_score()`  [INFERRED]
  tests/test_virality.py → src/analyzer/virality.py
- `test_zero_followers_returns_zero()` --calls--> `calculate_virality_score()`  [INFERRED]
  tests/test_virality.py → src/analyzer/virality.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.17
Nodes (15): collect_profile(), Coleta posts novos de um perfil. Tenta Apify primeiro, cai para Instaloader em c, Post, Profile, db_session(), test_collect_profile_skips_existing_posts(), session_with_post(), session() (+7 more)

### Community 1 - "Community 1"
Cohesion: 0.17
Nodes (13): DeclarativeBase, generate_carousel(), Gera carrossel viral com base no tema, voz própria e último relatório semanal., Base, Carousel, GeneratedPost, WeeklyReport, session_with_context() (+5 more)

### Community 2 - "Community 2"
Cohesion: 0.16
Nodes (10): fetch_posts_apify(), Busca posts de um perfil via Apify Instagram Scraper.     Retorna lista de dicts, fetch_posts_instaloader(), _get_loader(), Busca posts via Instaloader com login para evitar bloqueios.     Retorna lista d, sync_all(), test_collect_profile_saves_new_posts(), test_fetch_posts_apify_maps_video_to_reel() (+2 more)

### Community 3 - "Community 3"
Cohesion: 0.2
Nodes (7): render(), _render_carousel(), render(), _get_engine(), get_session(), render(), render()

### Community 4 - "Community 4"
Cohesion: 0.24
Nodes (7): analyze_post(), Analisa um post com GPT-4o Vision. Se já analisado, retorna análise existente., PostAnalysis, render_post_card(), render(), test_analyze_post_creates_analysis(), test_analyze_post_skips_already_analyzed()

### Community 5 - "Community 5"
Cohesion: 0.33
Nodes (7): _build_approved_section(), generate_post(), Gera um post adaptado com base no post do concorrente, voz do autor e exemplos a, _get_approved_examples(), _get_competitor_posts(), _get_voice(), render()

### Community 6 - "Community 6"
Cohesion: 0.36
Nodes (6): test_basic_score(), test_score_clamped_to_one(), test_zero_engagement_returns_zero(), test_zero_followers_returns_zero(), calculate_virality_score(), Normaliza engajamento pelo número de seguidores. Retorna valor entre 0 e 1.

### Community 7 - "Community 7"
Cohesion: 0.38
Nodes (5): ProfileVoice, analyze_voice(), Analisa os posts do perfil próprio e gera/atualiza o perfil de voz., generate_voice_profile(), Analisa os posts do perfil próprio e gera um perfil de voz atualizado.

### Community 8 - "Community 8"
Cohesion: 0.5
Nodes (1): initial_schema  Revision ID: 001 Revises: Create Date: 2026-04-14 00:00:00.00000

### Community 9 - "Community 9"
Cohesion: 0.5
Nodes (1): content_studio  Revision ID: 002 Revises: a1b2c3d4e5f6 Create Date: 2026-04-15 0

### Community 10 - "Community 10"
Cohesion: 0.67
Nodes (0): 

### Community 11 - "Community 11"
Cohesion: 0.67
Nodes (0): 

### Community 12 - "Community 12"
Cohesion: 0.67
Nodes (0): 

### Community 13 - "Community 13"
Cohesion: 1.0
Nodes (0): 

### Community 14 - "Community 14"
Cohesion: 1.0
Nodes (0): 

### Community 15 - "Community 15"
Cohesion: 1.0
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

## Knowledge Gaps
- **5 isolated node(s):** `initial_schema  Revision ID: 001 Revises: Create Date: 2026-04-14 00:00:00.00000`, `content_studio  Revision ID: 002 Revises: a1b2c3d4e5f6 Create Date: 2026-04-15 0`, `Busca posts de um perfil via Apify Instagram Scraper.     Retorna lista de dicts`, `Busca posts via Instaloader com login para evitar bloqueios.     Retorna lista d`, `Normaliza engajamento pelo número de seguidores. Retorna valor entre 0 e 1.`
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 13`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 14`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (1 nodes): `app.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (1 nodes): `config.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_session()` connect `Community 3` to `Community 2`, `Community 4`, `Community 5`?**
  _High betweenness centrality (0.153) - this node is a cross-community bridge._
- **Why does `analyze_post()` connect `Community 4` to `Community 3`, `Community 6`?**
  _High betweenness centrality (0.138) - this node is a cross-community bridge._
- **Why does `Post` connect `Community 0` to `Community 1`, `Community 2`, `Community 4`, `Community 5`, `Community 7`?**
  _High betweenness centrality (0.136) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Post` (e.g. with `Consolida análises da semana em um relatório via GPT-4o.` and `Analisa os posts do perfil próprio e gera um perfil de voz atualizado.`) actually correct?**
  _`Post` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `Profile` (e.g. with `Analisa os posts do perfil próprio e gera um perfil de voz atualizado.` and `Coleta posts novos de um perfil. Tenta Apify primeiro, cai para Instaloader em c`) actually correct?**
  _`Profile` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `ProfileVoice` (e.g. with `Analisa os posts do perfil próprio e gera um perfil de voz atualizado.` and `Gera carrossel viral com base no tema, voz própria e último relatório semanal.`) actually correct?**
  _`ProfileVoice` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `get_session()` (e.g. with `render()` and `render()`) actually correct?**
  _`get_session()` has 7 INFERRED edges - model-reasoned connections that need verification._