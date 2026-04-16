# Content Strategy Engine — Plan B: Intelligence

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Prerequisite:** Plan A must be complete (migration 003 applied, NewsItem/ContentCalendar models exist, news_monitor, seasonal, gap_analyzer implemented).

**Goal:** Build the carousel slide analyzer (GPT-4o Vision, slide-by-slide narrative extraction), the AI strategy engine (generates original content ideas from market intelligence without requiring a specific competitor post), and the weekly editorial calendar generator.

**Architecture:** Three independent service modules. `carousel_analyzer` processes images via GPT-4o Vision. `strategy_engine` acts as an agro market expert — combines news, seasonal context, gap analysis, and voice profile to generate `GeneratedPost` records with funnel stage and 3 hook variations. `calendar_generator` produces a 7-day `ContentCalendar` by calling `strategy_engine` four times with different funnel stages.

**Tech Stack:** Python 3.9, SQLAlchemy 2.0, OpenAI GPT-4o + GPT-4o Vision, base64 image encoding, httpx, pytest

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Modify | `src/collector/apify_client.py` | Extract `sidecarImages` slide URLs for carousel posts |
| Create | `src/analyzer/carousel_analyzer.py` | Slide-by-slide GPT-4o Vision analysis + narrative arc |
| Create | `src/generator/strategy_engine.py` | AI market expert: generates original content ideas |
| Create | `src/generator/calendar_generator.py` | Weekly editorial calendar (4 posts, balanced funnel) |
| Create | `tests/test_carousel_analyzer.py` | Tests for carousel analyzer |
| Create | `tests/test_strategy_engine.py` | Tests for strategy engine |
| Create | `tests/test_calendar_generator.py` | Tests for calendar generator |

---

## Task 1: Extract carousel slides in Apify collector

The Apify Instagram Scraper returns a `sidecarImages` array for carousel (Sidecar) posts. We need to extract those URLs and include them in the normalized post dict so they get saved to `Post.slides`.

**Files:**
- Modify: `src/collector/apify_client.py`
- Modify: `src/collector/collector.py` (or wherever `apify_client` output is saved to DB)

- [ ] **Step 1: Read the collector to understand how posts are saved**

Read `src/collector/collector.py` to find where `fetch_posts_apify` results are turned into `Post` DB objects. Note the field mapping.

- [ ] **Step 2: Write a failing test**

Create `tests/test_apify_slides.py`:

```python
from unittest.mock import MagicMock, patch
from src.collector.apify_client import fetch_posts_apify


def _make_mock_item(post_type="Sidecar", sidecar_images=None):
    item = {
        "id": "IG_CAROUSEL_1",
        "type": post_type,
        "displayUrl": "https://example.com/cover.jpg",
        "caption": "Carrossel de teste",
        "hashtags": ["agro"],
        "likesCount": 500,
        "commentsCount": 30,
        "timestamp": "2026-04-16T10:00:00Z",
    }
    if sidecar_images:
        item["sidecarImages"] = sidecar_images
    return item


def test_carousel_slides_extracted(monkeypatch):
    sidecar_images = [
        {"url": "https://example.com/slide1.jpg"},
        {"url": "https://example.com/slide2.jpg"},
        {"url": "https://example.com/slide3.jpg"},
    ]
    mock_item = _make_mock_item(sidecar_images=sidecar_images)

    mock_run = {"status": "SUCCEEDED", "defaultDatasetId": "ds1"}
    mock_dataset = MagicMock()
    mock_dataset.iterate_items.return_value = [mock_item]
    mock_client = MagicMock()
    mock_client.actor.return_value.call.return_value = mock_run
    mock_client.dataset.return_value = mock_dataset

    with patch("src.collector.apify_client.ApifyClient", return_value=mock_client):
        posts = fetch_posts_apify("testhandle", "fake-token", months_back=12)

    assert len(posts) == 1
    assert posts[0]["slides"] == [
        "https://example.com/slide1.jpg",
        "https://example.com/slide2.jpg",
        "https://example.com/slide3.jpg",
    ]


def test_feed_post_has_empty_slides(monkeypatch):
    mock_item = _make_mock_item(post_type="Image")

    mock_run = {"status": "SUCCEEDED", "defaultDatasetId": "ds1"}
    mock_dataset = MagicMock()
    mock_dataset.iterate_items.return_value = [mock_item]
    mock_client = MagicMock()
    mock_client.actor.return_value.call.return_value = mock_run
    mock_client.dataset.return_value = mock_dataset

    with patch("src.collector.apify_client.ApifyClient", return_value=mock_client):
        posts = fetch_posts_apify("testhandle", "fake-token", months_back=12)

    assert posts[0]["slides"] == []
```

- [ ] **Step 3: Run tests — expect FAIL (no slides key)**

```bash
python -m pytest tests/test_apify_slides.py -v
```

Expected: `KeyError: 'slides'` or `AssertionError`

- [ ] **Step 4: Modify apify_client.py to extract slides**

In `src/collector/apify_client.py`, update the dict inside the `posts.append({...})` block to add the `slides` field:

```python
posts.append({
    "instagram_id": item["id"],
    "image_url": item.get("displayUrl", ""),
    "caption": item.get("caption", ""),
    "hashtags": item.get("hashtags", []),
    "likes": item.get("likesCount", 0),
    "comments": item.get("commentsCount", 0),
    "post_type": _TYPE_MAP.get(item.get("type", ""), "feed"),
    "published_at": published_at,
    "slides": [img["url"] for img in item.get("sidecarImages", []) if img.get("url")],
})
```

- [ ] **Step 5: Find where posts are saved to DB and add slides**

Read `src/collector/collector.py`. Find the line where a `Post` object is created from the dict. Add `slides=post_data.get("slides", [])` to the `Post(...)` constructor call.

- [ ] **Step 6: Run tests — expect PASS**

```bash
python -m pytest tests/test_apify_slides.py -v
```

Expected: Both tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/collector/apify_client.py src/collector/collector.py tests/test_apify_slides.py
git commit -m "feat: extract carousel slide URLs from Apify response"
```

---

## Task 2: Carousel Analyzer

Analyzes all slides of a carousel post using GPT-4o Vision. Each slide image is fetched and base64-encoded. GPT-4o receives all slides at once and returns a structured JSON with per-slide analysis + narrative arc.

**Files:**
- Create: `src/analyzer/carousel_analyzer.py`
- Create: `tests/test_carousel_analyzer.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_carousel_analyzer.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from src.models import Profile, Post, PostAnalysis
from src.analyzer.carousel_analyzer import analyze_carousel, _build_vision_messages


def _make_carousel_post(session):
    p = Profile(handle="comp", type="competitor", niche="agro", follower_count=5000)
    session.add(p)
    session.flush()
    post = Post(
        profile_id=p.id,
        instagram_id="CAR001",
        image_url="https://example.com/slide1.jpg",
        caption="Carrossel sobre rentabilidade",
        hashtags=[],
        likes=1000,
        comments=50,
        post_type="carousel",
        published_at=datetime.now(timezone.utc),
        slides=[
            "https://example.com/slide1.jpg",
            "https://example.com/slide2.jpg",
            "https://example.com/slide3.jpg",
        ],
    )
    session.add(post)
    session.commit()
    return post


def test_build_vision_messages_structure():
    slides_b64 = ["base64data1", "base64data2"]
    messages = _build_vision_messages(slides_b64, "Legenda do post")
    assert isinstance(messages, list)
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    # Should contain at least one image_url content block
    content = messages[0]["content"]
    image_blocks = [c for c in content if c.get("type") == "image_url"]
    assert len(image_blocks) == 2


def test_analyze_carousel_returns_post_analysis(session):
    post = _make_carousel_post(session)

    mock_response = MagicMock()
    mock_response.choices[0].message.content = '''{
        "slide_count": 3,
        "slides": [
            {"index": 0, "role": "hook", "content_type": "text", "text": "Você está perdendo 30% da sua margem"},
            {"index": 1, "role": "content", "content_type": "data", "text": "Custo médio por hectare: R$4.200"},
            {"index": 2, "role": "cta", "content_type": "cta", "text": "Salve para não esquecer"}
        ],
        "narrative_arc": "Problema com dado impactante → Aprofundamento técnico → CTA de salvamento"
    }'''

    fake_b64 = ["aGVsbG8=" for _ in post.slides]

    with patch("src.analyzer.carousel_analyzer._fetch_image_b64", side_effect=fake_b64):
        with patch("src.analyzer.carousel_analyzer.openai_client") as mock_client:
            mock_client.chat.completions.create.return_value = mock_response
            analysis = analyze_carousel(post, session)

    assert isinstance(analysis, PostAnalysis)
    assert analysis.carousel_narrative["slide_count"] == 3
    assert analysis.carousel_narrative["slides"][0]["role"] == "hook"
    assert "Problema" in analysis.carousel_narrative["narrative_arc"]


def test_analyze_carousel_skips_non_carousel(session):
    p = Profile(handle="comp2", type="competitor", niche="agro", follower_count=100)
    session.add(p)
    session.flush()
    post = Post(
        profile_id=p.id, instagram_id="FEED001", image_url="u", caption="c",
        hashtags=[], likes=0, comments=0, post_type="feed",
        published_at=datetime.now(timezone.utc), slides=[],
    )
    session.add(post)
    session.commit()

    result = analyze_carousel(post, session)
    assert result is None
```

- [ ] **Step 2: Run tests — expect ImportError**

```bash
python -m pytest tests/test_carousel_analyzer.py -v
```

Expected: `ImportError: cannot import name 'analyze_carousel'`

- [ ] **Step 3: Implement carousel_analyzer.py**

Create `src/analyzer/carousel_analyzer.py`:

```python
import base64
import json
import logging
from typing import List, Optional

import httpx
from openai import OpenAI
from sqlalchemy.orm import Session

from src.config import OPENAI_API_KEY
from src.models import Post, PostAnalysis

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

CAROUSEL_PROMPT = """Você é um especialista em conteúdo para Instagram no agronegócio.
Analise as {slide_count} slides deste carrossel (post caption: "{caption}").

Para cada slide, identifique:
- role: "hook" | "content" | "proof" | "cta"
- content_type: "text" | "data" | "image_heavy" | "cta"
- text: texto principal visível ou descrição do visual

Depois, descreva o narrative_arc geral do carrossel em uma frase.

Retorne JSON exatamente neste formato:
{{
  "slide_count": {slide_count},
  "slides": [
    {{"index": 0, "role": "hook", "content_type": "text", "text": "<texto ou descrição>"}},
    ...
  ],
  "narrative_arc": "<descrição do arco narrativo>"
}}
Responda APENAS com o JSON, sem markdown."""


def _fetch_image_b64(url: str) -> str:
    """Download an image and return its base64 encoding."""
    response = httpx.get(url, timeout=15, follow_redirects=True)
    response.raise_for_status()
    return base64.b64encode(response.content).decode("utf-8")


def _build_vision_messages(slides_b64: List[str], caption: str) -> List[dict]:
    content = []
    for b64 in slides_b64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"},
        })
    content.append({
        "type": "text",
        "text": CAROUSEL_PROMPT.format(
            slide_count=len(slides_b64),
            caption=caption or "",
        ),
    })
    return [{"role": "user", "content": content}]


def analyze_carousel(post: Post, session: Session) -> Optional[PostAnalysis]:
    """
    Analyze all slides of a carousel post using GPT-4o Vision.
    Updates or creates a PostAnalysis with carousel_narrative.
    Returns None if the post is not a carousel or has no slides.
    """
    if post.post_type != "carousel" or not post.slides:
        return None

    # Fetch and encode each slide (limit to first 8 to manage token cost)
    slides_to_analyze = post.slides[:8]
    slides_b64 = []
    for url in slides_to_analyze:
        try:
            slides_b64.append(_fetch_image_b64(url))
        except Exception as exc:
            logger.warning("Failed to fetch slide %s: %s", url, exc)

    if not slides_b64:
        logger.warning("No slides could be fetched for post %s", post.instagram_id)
        return None

    messages = _build_vision_messages(slides_b64, post.caption or "")

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=800,
    )

    content = response.choices[0].message.content or ""
    content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        narrative = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.error("GPT-4o returned invalid JSON for carousel %s: %s — raw: %r", post.instagram_id, exc, content)
        raise

    analysis = session.query(PostAnalysis).filter_by(post_id=post.id).first()
    if analysis:
        analysis.carousel_narrative = narrative
    else:
        analysis = PostAnalysis(
            post_id=post.id,
            raw_analysis={},
            carousel_narrative=narrative,
        )
        session.add(analysis)

    session.commit()
    logger.info("Carousel narrative extracted for post %s (%d slides)", post.instagram_id, len(slides_b64))
    return analysis
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
python -m pytest tests/test_carousel_analyzer.py -v
```

Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/analyzer/carousel_analyzer.py tests/test_carousel_analyzer.py
git commit -m "feat: carousel analyzer - slide-by-slide GPT-4o Vision analysis"
```

---

## Task 3: Strategy Engine (AI Market Expert Mode)

Generates a `GeneratedPost` without requiring a specific competitor post as input. Instead it synthesizes: recent news, seasonal context, gap analysis, and the voice profile.

**Files:**
- Create: `src/generator/strategy_engine.py`
- Create: `tests/test_strategy_engine.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_strategy_engine.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from src.models import Profile, Post, PostAnalysis, ProfileVoice, GeneratedPost, NewsItem
from src.generator.strategy_engine import generate_content_idea, _build_strategy_prompt


def _make_voice(session, profile):
    voice = ProfileVoice(
        profile_id=profile.id,
        tone="direto e provocador",
        dominant_themes=["rentabilidade", "venda no agro"],
        vocabulary={"palavras_frequentes": ["agrônomo", "resultado", "produtor"]},
        competitor_comparison={"diferencial": "linguagem técnica acessível"},
        voice_summary="Nathan fala direto, usa dados, provoca o leitor com perguntas.",
        generated_at=datetime.now(timezone.utc),
    )
    session.add(voice)
    session.flush()
    return voice


def _make_own_profile(session):
    p = Profile(handle="nathanlimagro", type="own", active=True, niche="agro", follower_count=5000)
    session.add(p)
    session.flush()
    return p


def test_build_strategy_prompt_contains_funnel_stage():
    prompt = _build_strategy_prompt(
        funnel_stage="topo",
        voice_summary="Tom direto e provocador.",
        seasonal_context="Colheita de soja em andamento.",
        gaps=[{"topic": "rentabilidade", "gap_score": 0.4}],
        recent_news=[],
        approved_examples=[],
    )
    assert "topo" in prompt
    assert "rentabilidade" in prompt
    assert "Colheita de soja" in prompt


def test_build_strategy_prompt_includes_news():
    news = [MagicMock(title="Soja bate recorde", summary="Exportação em alta", tags=["soja"])]
    prompt = _build_strategy_prompt(
        funnel_stage="meio",
        voice_summary="Tom técnico.",
        seasonal_context="Entressafra.",
        gaps=[],
        recent_news=news,
        approved_examples=[],
    )
    assert "Soja bate recorde" in prompt


def test_generate_content_idea_returns_generated_post(session):
    own = _make_own_profile(session)
    voice = _make_voice(session, own)
    session.commit()

    mock_response = MagicMock()
    mock_response.choices[0].message.content = '''{
        "hook": "80% dos agrônomos deixam dinheiro na mesa todo ano.",
        "caption": "A rentabilidade da lavoura não depende só da produtividade...",
        "cta": "Comenta RENTABILIDADE que te mando o material.",
        "hook_variations": {
            "provocacao": "80% dos agrônomos deixam dinheiro na mesa.",
            "dado": "Custo de produção subiu 18% — você ajustou seu preço?",
            "pergunta": "Você já calculou sua margem líquida por hectare este ano?"
        },
        "news_item_ids": []
    }'''

    with patch("src.generator.strategy_engine.openai_client") as mock_client:
        with patch("src.generator.strategy_engine.get_seasonal_context", return_value="Safra em andamento."):
            with patch("src.generator.strategy_engine.compute_gaps", return_value=[{"topic": "rentabilidade", "gap_score": 0.5}]):
                with patch("src.generator.strategy_engine.get_recent_news", return_value=[]):
                    mock_client.chat.completions.create.return_value = mock_response
                    gp = generate_content_idea("topo", session)

    assert isinstance(gp, GeneratedPost)
    assert gp.funnel_stage == "topo"
    assert gp.hook.startswith("80%")
    assert gp.hook_variations["dado"].startswith("Custo")
    assert gp.source_post_id is None  # market mode: no source post


def test_generate_content_idea_raises_if_no_voice(session):
    own = _make_own_profile(session)
    session.commit()

    with pytest.raises(ValueError, match="Perfil de voz"):
        generate_content_idea("topo", session)
```

- [ ] **Step 2: Run tests — expect ImportError**

```bash
python -m pytest tests/test_strategy_engine.py -v
```

Expected: `ImportError: cannot import name 'generate_content_idea'`

- [ ] **Step 3: Implement strategy_engine.py**

Create `src/generator/strategy_engine.py`:

```python
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional

from openai import OpenAI
from sqlalchemy.orm import Session

from src.analyzer.gap_analyzer import compute_gaps
from src.collector.news_monitor import get_recent_news
from src.config import OPENAI_API_KEY
from src.generator.seasonal import get_seasonal_context
from src.models import GeneratedPost, NewsItem, Profile, ProfileVoice

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

_FUNNEL_INSTRUCTIONS = {
    "topo": (
        "TOPO DE FUNIL — objetivo: alcance e consciência. "
        "Público: produtores rurais, técnicos agrícolas. "
        "CTA deve ser leve: 'salve', 'compartilhe', 'marque um amigo agrônomo'. "
        "Tom: educativo, provocador, surpreendente."
    ),
    "meio": (
        "MEIO DE FUNIL — objetivo: autoridade e relacionamento. "
        "Público: consultores, agrônomos, revendedores de insumos. "
        "CTA deve gerar conversa: 'comenta aqui', 'me conta sua experiência'. "
        "Tom: técnico mas acessível, mostra conhecimento profundo."
    ),
    "fundo": (
        "FUNDO DE FUNIL — objetivo: conversão para a Confraria de Vendas no Agro. "
        "Público: profissionais de vendas no agronegócio que querem vender mais. "
        "CTA deve ser direto: 'entre na Confraria', 'link na bio', 'DM CONFRARIA'. "
        "Tom: urgência, exclusividade, resultado concreto."
    ),
}

STRATEGY_PROMPT = """Você é Nathan Lima, agrônomo e especialista em vendas no agronegócio, com 15 anos de experiência.
Seu objetivo é criar conteúdo original e relevante para o Instagram, com base no contexto atual do mercado.

PERFIL DE VOZ:
{voice_summary}

CONTEXTO SAZONAL ATUAL:
{seasonal_context}

LACUNAS IDENTIFICADAS (tópicos que concorrentes cobrem mas você ainda não explorou bem):
{gaps_text}

NOTÍCIAS RECENTES DO AGRO:
{news_text}

EXEMPLOS DE POSTS APROVADOS (seu estilo validado):
{approved_text}

INSTRUÇÃO DE FUNIL:
{funnel_instruction}

Gere UMA ideia de conteúdo original, relevante e atual. Não copie nenhum post existente.
O conteúdo deve ser autêntico, baseado em fatos reais do agronegócio brasileiro atual.

Retorne JSON exatamente neste formato:
{{
  "hook": "<frase de abertura principal>",
  "caption": "<legenda completa com 3-5 parágrafos, uso moderado de emojis, linguagem do agro>",
  "cta": "<call-to-action final>",
  "hook_variations": {{
    "provocacao": "<hook alternativo que desafia uma crença comum>",
    "dado": "<hook alternativo com dado/estatística surpreendente>",
    "pergunta": "<hook alternativo como pergunta direta ao leitor>"
  }},
  "news_item_ids": [<ids das notícias usadas como referência, pode ser lista vazia>]
}}
Responda APENAS com o JSON, sem markdown."""


def _build_strategy_prompt(
    funnel_stage: str,
    voice_summary: str,
    seasonal_context: str,
    gaps: List[dict],
    recent_news: List,
    approved_examples: List[GeneratedPost],
) -> str:
    gaps_text = "\n".join(
        f"- {g['topic']} (score: {g['gap_score']:.2f})" for g in gaps[:10]
    ) or "Nenhuma lacuna identificada ainda."

    news_text = "\n".join(
        f"- [{n.source}] {n.title}: {n.summary or ''}"
        for n in recent_news[:8]
    ) or "Nenhuma notícia recente disponível."

    approved_text = "\n\n".join(
        f"Hook: {ex.hook}\nLegenda: {(ex.caption or '')[:200]}..."
        for ex in approved_examples[:3]
    ) or "Nenhum exemplo aprovado ainda."

    return STRATEGY_PROMPT.format(
        voice_summary=voice_summary,
        seasonal_context=seasonal_context,
        gaps_text=gaps_text,
        news_text=news_text,
        approved_text=approved_text,
        funnel_instruction=_FUNNEL_INSTRUCTIONS.get(funnel_stage, ""),
    )


def generate_content_idea(funnel_stage: str, session: Session) -> GeneratedPost:
    """
    Generate an original content idea using market intelligence.
    Does not require a specific competitor post (source_post_id will be None).
    """
    own_profile = session.query(Profile).filter_by(type="own", active=True).first()
    if not own_profile:
        raise ValueError("Perfil próprio não encontrado. Cadastre @nathanlimagro na aba Concorrentes.")

    voice = (
        session.query(ProfileVoice)
        .filter_by(profile_id=own_profile.id)
        .order_by(ProfileVoice.generated_at.desc())
        .first()
    )
    if not voice:
        raise ValueError("Perfil de voz não gerado. Vá à aba Criar Conteúdo e clique em 'Gerar Perfil de Voz'.")

    seasonal_context = get_seasonal_context()
    gaps = compute_gaps(session)
    recent_news = get_recent_news(session, days=7)
    approved_examples = (
        session.query(GeneratedPost)
        .filter_by(status="approved")
        .order_by(GeneratedPost.created_at.desc())
        .limit(3)
        .all()
    )

    prompt = _build_strategy_prompt(
        funnel_stage=funnel_stage,
        voice_summary=voice.voice_summary or "",
        seasonal_context=seasonal_context,
        gaps=gaps,
        recent_news=recent_news,
        approved_examples=approved_examples,
    )

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200,
    )

    content = response.choices[0].message.content or ""
    content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        raw = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.error("GPT-4o invalid JSON in strategy engine for funnel %s: %s — raw: %r", funnel_stage, exc, content)
        raise

    gp = GeneratedPost(
        source_post_id=None,
        hook=raw.get("hook"),
        caption=raw.get("caption"),
        cta=raw.get("cta"),
        status="generated",
        funnel_stage=funnel_stage,
        format="carousel",
        hook_variations=raw.get("hook_variations", {}),
        news_item_ids=raw.get("news_item_ids", []),
    )
    session.add(gp)
    session.commit()
    logger.info("Content idea generated for funnel stage '%s'", funnel_stage)
    return gp
```

Note: `GeneratedPost.source_post_id` is currently `nullable=False` in the model. Update it to `nullable=True` in `src/models.py`:

```python
source_post_id: Mapped[Optional[int]] = mapped_column(ForeignKey("posts.id"), nullable=True)
```

And add a corresponding Alembic migration step — either add to migration 003 or create migration 003b. Since migration 003 may already be applied, create `alembic/versions/003b_nullable_source_post.py`:

```python
"""make source_post_id nullable

Revision ID: 003b
Revises: 003
Create Date: 2026-04-16 12:00:00.000000

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "003b"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite does not support ALTER COLUMN — this is a no-op for SQLite tests.
    # For PostgreSQL (Railway):
    with op.batch_alter_table("generated_posts") as batch_op:
        batch_op.alter_column("source_post_id", nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("generated_posts") as batch_op:
        batch_op.alter_column("source_post_id", nullable=False)
```

Run: `python -m alembic upgrade 003b`

- [ ] **Step 4: Run tests — expect PASS**

```bash
python -m pytest tests/test_strategy_engine.py -v
```

Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/generator/strategy_engine.py src/models.py \
    alembic/versions/003b_nullable_source_post.py \
    tests/test_strategy_engine.py
git commit -m "feat: strategy engine - AI market expert content generation"
```

---

## Task 4: Calendar Generator

Generates a 7-day editorial plan with 4 posts, balanced across funnel stages. Calls `generate_content_idea` for each entry but only stores metadata (topic, hook, funnel stage) in the `ContentCalendar` — not full posts.

**Files:**
- Create: `src/generator/calendar_generator.py`
- Create: `tests/test_calendar_generator.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_calendar_generator.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from src.models import Profile, ProfileVoice, GeneratedPost, ContentCalendar
from src.generator.calendar_generator import generate_weekly_calendar, _WEEKLY_PLAN


def _make_setup(session):
    p = Profile(handle="nathanlimagro", type="own", active=True, niche="agro", follower_count=5000)
    session.add(p)
    session.flush()
    v = ProfileVoice(
        profile_id=p.id,
        tone="direto",
        dominant_themes=["venda"],
        vocabulary={},
        competitor_comparison={},
        voice_summary="Tom direto.",
        generated_at=datetime.now(timezone.utc),
    )
    session.add(v)
    session.commit()


def _make_fake_gp(funnel_stage, hook):
    gp = MagicMock(spec=GeneratedPost)
    gp.id = 1
    gp.funnel_stage = funnel_stage
    gp.hook = hook
    gp.caption = "Legenda completa."
    gp.cta = "Entre na Confraria."
    gp.hook_variations = {"provocacao": hook, "dado": hook, "pergunta": hook}
    return gp


def test_weekly_plan_has_four_entries():
    assert len(_WEEKLY_PLAN) == 4


def test_weekly_plan_includes_all_funnel_stages():
    stages = [entry["funnel_stage"] for entry in _WEEKLY_PLAN]
    assert "topo" in stages
    assert "meio" in stages
    assert "fundo" in stages


def test_generate_weekly_calendar_returns_content_calendar(session):
    _make_setup(session)

    fake_gps = [
        _make_fake_gp("topo", "Hook topo"),
        _make_fake_gp("meio", "Hook meio"),
        _make_fake_gp("fundo", "Hook fundo"),
        _make_fake_gp("topo", "Hook topo 2"),
    ]

    with patch("src.generator.calendar_generator.generate_content_idea", side_effect=fake_gps):
        cal = generate_weekly_calendar(session)

    assert isinstance(cal, ContentCalendar)
    assert len(cal.entries) == 4
    assert cal.entries[0]["funnel_stage"] in ("topo", "meio", "fundo")
    assert "hook" in cal.entries[0]
    assert "day" in cal.entries[0]


def test_generate_weekly_calendar_saves_to_db(session):
    _make_setup(session)

    fake_gps = [_make_fake_gp("topo", f"Hook {i}") for i in range(4)]

    with patch("src.generator.calendar_generator.generate_content_idea", side_effect=fake_gps):
        cal = generate_weekly_calendar(session)

    assert session.get(ContentCalendar, cal.id) is not None
```

- [ ] **Step 2: Run tests — expect ImportError**

```bash
python -m pytest tests/test_calendar_generator.py -v
```

Expected: `ImportError: cannot import name 'generate_weekly_calendar'`

- [ ] **Step 3: Implement calendar_generator.py**

Create `src/generator/calendar_generator.py`:

```python
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from src.generator.strategy_engine import generate_content_idea
from src.models import ContentCalendar

logger = logging.getLogger(__name__)

# Default weekly editorial plan: day + funnel stage + format suggestion
_WEEKLY_PLAN = [
    {"day": "segunda", "funnel_stage": "topo", "format": "carousel"},
    {"day": "quarta", "funnel_stage": "meio", "format": "carousel"},
    {"day": "sexta", "funnel_stage": "fundo", "format": "feed"},
    {"day": "sabado", "funnel_stage": "topo", "format": "feed"},
]


def _next_monday() -> datetime:
    today = datetime.now(timezone.utc)
    days_ahead = (7 - today.weekday()) % 7 or 7
    return (today + timedelta(days=days_ahead)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def generate_weekly_calendar(session: Session) -> ContentCalendar:
    """
    Generate a 7-day editorial plan with 4 posts, balanced across funnel stages.
    Calls generate_content_idea for each plan slot and stores the result as
    ContentCalendar entries.
    """
    entries = []
    for plan_slot in _WEEKLY_PLAN:
        gp = generate_content_idea(plan_slot["funnel_stage"], session)
        entries.append({
            "day": plan_slot["day"],
            "funnel_stage": plan_slot["funnel_stage"],
            "format": plan_slot["format"],
            "generated_post_id": gp.id,
            "hook": gp.hook,
            "hook_variations": gp.hook_variations,
            "cta": gp.cta,
        })
        logger.info("Calendar entry created: %s (%s)", plan_slot["day"], plan_slot["funnel_stage"])

    cal = ContentCalendar(
        week_start=_next_monday(),
        entries=entries,
    )
    session.add(cal)
    session.commit()
    logger.info("Weekly calendar saved (week starting %s)", cal.week_start.strftime("%d/%m/%Y"))
    return cal
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
python -m pytest tests/test_calendar_generator.py -v
```

Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/generator/calendar_generator.py tests/test_calendar_generator.py
git commit -m "feat: weekly editorial calendar generator"
```

---

## Task 5: Full test suite + push

- [ ] **Step 1: Run all tests**

```bash
cd /Users/floakii/Claudio/agro-content
python -m pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 2: Push**

```bash
git push
```

Expected: Pushed. Railway auto-deploys.

---

## Plan B Complete

After this plan, Plan C (Dashboard — news tab, calendar tab, content studio updates) can begin.
