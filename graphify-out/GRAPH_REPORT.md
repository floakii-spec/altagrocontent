# Graph Report - .  (2026-04-24)

## Corpus Check
- 111 files · ~359,523 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 679 nodes · 1449 edges · 72 communities detected
- Extraction: 62% EXTRACTED · 38% INFERRED · 0% AMBIGUOUS · INFERRED: 555 edges (avg confidence: 0.7)
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
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]

## God Nodes (most connected - your core abstractions)
1. `Post` - 79 edges
2. `Profile` - 65 edges
3. `session()` - 47 edges
4. `generate_post()` - 43 edges
5. `PostAnalysis` - 35 edges
6. `ProfileVoice` - 30 edges
7. `PostIntelligence` - 27 edges
8. `ArgumentBank` - 22 edges
9. `generate_carousel()` - 17 edges
10. `analyze_post_intelligence()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `override_db()` --calls--> `session()`  [INFERRED]
  tests/test_api_intelligence.py → /Users/floakii/Claudio/agro-content/tests/test_models.py
- `test_start_analysis_job_returns_live_job()` --calls--> `Post`  [INFERRED]
  tests/test_api_intelligence.py → /Users/floakii/Claudio/agro-content/src/models.py
- `override_db()` --calls--> `session()`  [INFERRED]
  tests/test_api_carousel.py → /Users/floakii/Claudio/agro-content/tests/test_models.py
- `test_generate_carousel()` --calls--> `Post`  [INFERRED]
  tests/test_api_carousel.py → /Users/floakii/Claudio/agro-content/src/models.py
- `test_refresh_suggestions()` --calls--> `Post`  [INFERRED]
  tests/test_api_carousel.py → /Users/floakii/Claudio/agro-content/src/models.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (104): BaseModel, CarouselEvidencePack, Coleta posts novos de um perfil. Tenta Apify primeiro, cai para Instaloader em c, Coleta posts novos de um perfil. Tenta Apify primeiro, cai para Instaloader em c, Coleta posts novos de um perfil. Tenta Apify primeiro, cai para Instaloader em c, add_profile(), _build_post_status(), _build_post_title() (+96 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (84): _build_summary(), _evaluate_generated_output(), main(), _query_candidate_post_ids(), _run_single(), format_quality_feedback(), _align_cta_to_funnel(), _apply_local_quality_repairs() (+76 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (36): _extract_promised_data(), _required_inventory_has_items(), _validate_data_pledge(), _full_text(), Checks that each slide_number in the pledge exists in the carousel (1-based)., Checks that each pledged item appears in the generated content., Checks that all required inventory items have at least one pledge entry., Checks that pledged numbers appear with correct semantic context (not inverted). (+28 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (26): _append_unique(), _extract_slide_urls(), fetch_posts_apify(), Busca posts de um perfil via Apify Instagram Scraper.     Se since_date for forn, collect_profile(), _merge_post(), _get_engine(), get_session() (+18 more)

### Community 4 - "Community 4"
Cohesion: 0.1
Nodes (30): sync_profiles(), analyze_post(), AnalyzeJobOut, get_analysis_job_status(), get_intelligence(), _intel_to_out(), _append_error(), _copy_job() (+22 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (32): build_slide_blueprint(), _cta_matches_funnel(), estimate_target_slide_count(), _find_hits(), _find_token_overlap_hits(), _normalize_text(), Estimate how many slides the argument needs. No upper cap — depth drives count., Build a narrative blueprint. No upper cap — argument depth determines slide coun (+24 more)

### Community 6 - "Community 6"
Cohesion: 0.1
Nodes (24): CarouselGenerateIn, CarouselOut, CarouselSuggestionOut, generate(), get_suggestions(), list_carousels(), refresh_suggestions(), SlideOut (+16 more)

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (23): NewsItem, list_news(), _extract_tags(), fetch_all_feeds(), _fetch_all_raw(), get_recent_news(), _parse_feed(), Return news items from the last `days` days, optionally filtered by tags. (+15 more)

### Community 8 - "Community 8"
Cohesion: 0.17
Nodes (19): analyze_post_intelligence(), _coerce_slide_urls(), _extract_evidence_inventory(), _snapshot_intelligence(), _to_data_url(), _transcribe_visual_assets(), _mock_gpt_response(), test_extract_evidence_inventory_causal_steps() (+11 more)

### Community 9 - "Community 9"
Cohesion: 0.31
Nodes (14): _average_virality(), _candidate_texts(), _compute_quality_score(), _normalize(), remove_arguments_for_post(), upsert_arguments(), _make_intelligence(), _make_post_with_analysis() (+6 more)

### Community 10 - "Community 10"
Cohesion: 0.35
Nodes (14): build_source_creative_brief(), build_theme_creative_brief(), _clean(), _data_labels(), _extract_causal_chain(), _field_contexts(), Select the most fitting hook archetype based on post intelligence signals., Select the most fitting narrative arc based on post intelligence signals. (+6 more)

### Community 11 - "Community 11"
Cohesion: 0.19
Nodes (6): override_db(), _seed_intelligence(), test_get_intelligence_by_post_id(), test_list_intelligence_prioritizes_competitors_before_own_profile(), test_list_intelligence_returns_data(), test_start_analysis_job_returns_live_job()

### Community 12 - "Community 12"
Cohesion: 0.3
Nodes (9): drillInto(), fadeIn(), makeNode(), makePulse(), makeRings(), renderHome(), setPos(), startOrbit() (+1 more)

### Community 13 - "Community 13"
Cohesion: 0.38
Nodes (9): compute_gaps(), _extract_topics(), _make_post_with_analysis(), _make_profile(), test_compute_gaps_identifies_uncovered_topic(), test_compute_gaps_no_competitors_returns_empty(), test_compute_gaps_returns_list(), test_extract_topics_empty() (+1 more)

### Community 14 - "Community 14"
Cohesion: 0.25
Nodes (0):

### Community 15 - "Community 15"
Cohesion: 0.32
Nodes (5): generate_report(), list_reports(), ReportOut, test_generate_weekly_report_creates_report(), generate_weekly_report()

### Community 16 - "Community 16"
Cohesion: 0.32
Nodes (5): test_generate_voice_profile_creates_profile(), analyze_voice(), get_voice(), generate_voice_profile(), VoiceOut

### Community 17 - "Community 17"
Cohesion: 0.36
Nodes (6): get_seasonal_context(), Return the current month's agro seasonal context string., test_july_august_context(), test_march_april_context(), test_november_december_context(), test_returns_string()

### Community 18 - "Community 18"
Cohesion: 0.48
Nodes (5): analyze(), load(), removeOwnProfile(), saveOwnProfile(), syncOwnProfile()

### Community 19 - "Community 19"
Cohesion: 0.6
Nodes (5): _candidate_vault_paths(), load_studio_context(), _read_note(), _repo_root(), _resolve_vault_path()

### Community 20 - "Community 20"
Cohesion: 0.5
Nodes (2): generate(), loadHistory()

### Community 21 - "Community 21"
Cohesion: 0.5
Nodes (2): Badge(), cn()

### Community 22 - "Community 22"
Cohesion: 0.5
Nodes (0):

### Community 23 - "Community 23"
Cohesion: 0.5
Nodes (0):

### Community 24 - "Community 24"
Cohesion: 0.5
Nodes (0):

### Community 25 - "Community 25"
Cohesion: 0.5
Nodes (1): content_strategy_engine  Revision ID: 003 Revises: 002 Create Date: 2026-04-17 0

### Community 26 - "Community 26"
Cohesion: 0.5
Nodes (1): add visual transcript to post intelligence  Revision ID: 009 Revises: 008 Create

### Community 27 - "Community 27"
Cohesion: 0.5
Nodes (1): add slides to generated_posts  Revision ID: 008 Revises: 007 Create Date: 2026-0

### Community 28 - "Community 28"
Cohesion: 0.5
Nodes (1): fix profile_voice tone column from VARCHAR(100) to TEXT  Revision ID: 006 Revise

### Community 29 - "Community 29"
Cohesion: 0.5
Nodes (1): initial_schema  Revision ID: 001 Revises: Create Date: 2026-04-14 00:00:00.00000

### Community 30 - "Community 30"
Cohesion: 0.5
Nodes (1): content_studio  Revision ID: 002 Revises: a1b2c3d4e5f6 Create Date: 2026-04-15 0

### Community 31 - "Community 31"
Cohesion: 0.5
Nodes (1): add carousel intelligence fields  Revision ID: 007 Revises: 006 Create Date: 202

### Community 32 - "Community 32"
Cohesion: 0.5
Nodes (1): add planning narrative to generated posts  Revision ID: 010 Revises: 009 Create

### Community 33 - "Community 33"
Cohesion: 0.5
Nodes (1): post_intelligence and argument_bank tables  Revision ID: 005 Revises: 004 Create

### Community 34 - "Community 34"
Cohesion: 0.5
Nodes (1): carousel_suggestions table  Revision ID: 004 Revises: 003 Create Date: 2026-04-1

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (2): proxy(), sha256hex()

### Community 36 - "Community 36"
Cohesion: 0.67
Nodes (1): POST()

### Community 37 - "Community 37"
Cohesion: 0.67
Nodes (0):

### Community 38 - "Community 38"
Cohesion: 0.67
Nodes (0):

### Community 39 - "Community 39"
Cohesion: 0.67
Nodes (0):

### Community 40 - "Community 40"
Cohesion: 0.67
Nodes (0):

### Community 41 - "Community 41"
Cohesion: 0.67
Nodes (0):

### Community 42 - "Community 42"
Cohesion: 0.67
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
Nodes (0):

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (0):

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (0):

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (0):

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (0):

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (0):

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (0):

### Community 66 - "Community 66"
Cohesion: 1.0
Nodes (1): Busca posts de um perfil via Apify Instagram Scraper.     Se since_date for forn

### Community 67 - "Community 67"
Cohesion: 1.0
Nodes (1): Busca posts via Instaloader com login para evitar bloqueios.     Retorna lista d

### Community 68 - "Community 68"
Cohesion: 1.0
Nodes (1): Busca posts de um perfil via Apify Instagram Scraper.     Se since_date for forn

### Community 69 - "Community 69"
Cohesion: 1.0
Nodes (1): Busca posts via Instaloader com login para evitar bloqueios.     Retorna lista d

### Community 70 - "Community 70"
Cohesion: 1.0
Nodes (1): Busca posts de um perfil via Apify Instagram Scraper.     Retorna lista de dicts

### Community 71 - "Community 71"
Cohesion: 1.0
Nodes (1): Busca posts de um perfil via Apify Instagram Scraper.     Retorna lista de dicts

## Knowledge Gaps
- **29 isolated node(s):** `content_strategy_engine  Revision ID: 003 Revises: 002 Create Date: 2026-04-17 0`, `add visual transcript to post intelligence  Revision ID: 009 Revises: 008 Create`, `add slides to generated_posts  Revision ID: 008 Revises: 007 Create Date: 2026-0`, `fix profile_voice tone column from VARCHAR(100) to TEXT  Revision ID: 006 Revise`, `initial_schema  Revision ID: 001 Revises: Create Date: 2026-04-14 00:00:00.00000` (+24 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 43`** (2 nodes): `RootLayout()`, `layout.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (2 nodes): `resolveModule()`, `page.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (2 nodes): `proxy()`, `route.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (2 nodes): `handleSubmit()`, `page.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (2 nodes): `cn()`, `button.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (2 nodes): `formatDate()`, `DrawerConcorrentes.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (2 nodes): `ModuleDrawer()`, `ModuleDrawer.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (2 nodes): `test_health()`, `test_api_main.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `postcss.config.mjs`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `next-env.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `next.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `Sidebar.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `DrawerComingSoon.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (1 nodes): `config.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 66`** (1 nodes): `Busca posts de um perfil via Apify Instagram Scraper.     Se since_date for forn`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 67`** (1 nodes): `Busca posts via Instaloader com login para evitar bloqueios.     Retorna lista d`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 68`** (1 nodes): `Busca posts de um perfil via Apify Instagram Scraper.     Se since_date for forn`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 69`** (1 nodes): `Busca posts via Instaloader com login para evitar bloqueios.     Retorna lista d`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 70`** (1 nodes): `Busca posts de um perfil via Apify Instagram Scraper.     Retorna lista de dicts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 71`** (1 nodes): `Busca posts de um perfil via Apify Instagram Scraper.     Retorna lista de dicts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Post` connect `Community 0` to `Community 3`, `Community 4`, `Community 6`, `Community 7`, `Community 8`, `Community 9`, `Community 11`, `Community 13`, `Community 16`?**
  _High betweenness centrality (0.156) - this node is a cross-community bridge._
- **Why does `generate_post()` connect `Community 1` to `Community 0`, `Community 10`, `Community 19`, `Community 5`?**
  _High betweenness centrality (0.121) - this node is a cross-community bridge._
- **Why does `_validate_data_pledge()` connect `Community 2` to `Community 1`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Are the 77 inferred relationships involving `Post` (e.g. with `GeneratedPost.source_data_inventory must be a copy of the source intelligence ev` and `CompetitorPostOut`) actually correct?**
  _`Post` has 77 INFERRED edges - model-reasoned connections that need verification._
- **Are the 63 inferred relationships involving `Profile` (e.g. with `GeneratedPost.source_data_inventory must be a copy of the source intelligence ev` and `CompetitorPostOut`) actually correct?**
  _`Profile` has 63 INFERRED edges - model-reasoned connections that need verification._
- **Are the 46 inferred relationships involving `session()` (e.g. with `override_db()` and `test_list_competitors_returns_post_count()`) actually correct?**
  _`session()` has 46 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `generate_post()` (e.g. with `test_generate_post_retries_when_initial_draft_is_weak()` and `test_generate_post_recovers_from_empty_or_invalid_json_response()`) actually correct?**
  _`generate_post()` has 19 INFERRED edges - model-reasoned connections that need verification._