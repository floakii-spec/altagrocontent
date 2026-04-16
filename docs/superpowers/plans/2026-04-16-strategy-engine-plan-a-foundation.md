# Content Strategy Engine — Plan A: Foundation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the database schema with all new models and columns needed for the content strategy engine, add feedparser dependency, implement the news monitor (RSS polling) and the competitor gap analyzer, and add the seasonal agro context module.

**Architecture:** New models (`NewsItem`, `ContentCalendar`) + columns on `Post`, `PostAnalysis`, `GeneratedPost` are added via a single Alembic migration (003). Service modules are thin Python files with pure functions — no classes. Tests use SQLite in-memory via the existing conftest fixtures.

**Tech Stack:** Python 3.9, SQLAlchemy 2.0, Alembic, feedparser, pytest, OpenAI GPT-4o (for gap analysis summary only)

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Modify | `requirements.txt` | Add `feedparser==6.0.11` |
| Modify | `src/models.py` | Add `NewsItem`, `ContentCalendar` classes; add columns to `Post`, `PostAnalysis`, `GeneratedPost` |
| Create | `alembic/versions/003_content_strategy.py` | Migration for all schema changes |
| Create | `src/collector/news_monitor.py` | RSS polling, deduplication, tag extraction |
| Create | `src/generator/seasonal.py` | `get_seasonal_context() -> str` — month-to-crop-phase lookup |
| Create | `src/analyzer/gap_analyzer.py` | `compute_gaps(session) -> list[dict]` — topic gap detection |
| Create | `tests/test_news_monitor.py` | Tests for news_monitor |
| Create | `tests/test_seasonal.py` | Tests for seasonal context |
| Create | `tests/test_gap_analyzer.py` | Tests for gap analyzer |
| Modify | `tests/test_models.py` | Add tests for new models and columns |

---

## Task 1: Add feedparser dependency

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add feedparser to requirements**

Edit `requirements.txt` — append this line at the end:
```
feedparser==6.0.11
```

- [ ] **Step 2: Install locally**

```bash
cd /Users/floakii/Claudio/agro-content
pip install feedparser==6.0.11
```

Expected: `Successfully installed feedparser-6.0.11`

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: add feedparser for RSS monitoring"
```

---

## Task 2: Extend models

**Files:**
- Modify: `src/models.py`

The existing `models.py` ends with the `Carousel` class. We need to:
1. Add `slides` (JSON) to `Post`
2. Add `carousel_narrative` (JSON) to `PostAnalysis`
3. Add `funnel_stage`, `format`, `hook_variations`, `news_item_ids` to `GeneratedPost`
4. Add new classes `NewsItem` and `ContentCalendar`

- [ ] **Step 1: Write failing test for new model columns**

In `tests/test_models.py`, add these imports at the top (alongside existing ones):
```python
from src.models import NewsItem, ContentCalendar, GeneratedPost
```

Add these test functions at the bottom of the file:

```python
def test_post_has_slides_column(session):
    p = Profile(handle="h2", type="competitor", niche="agro", follower_count=100)
    session.add(p)
    session.flush()
    post = Post(
        profile_id=p.id,
        instagram_id="IG_SLIDES",
        image_url="https://example.com/cover.jpg",
        caption="Carrossel teste",
        hashtags=[],
        likes=0,
        comments=0,
        post_type="carousel",
        published_at=datetime.now(timezone.utc),
        slides=["https://example.com/s1.jpg", "https://example.com/s2.jpg"],
    )
    session.add(post)
    session.commit()
    assert post.slides == ["https://example.com/s1.jpg", "https://example.com/s2.jpg"]


def test_post_analysis_has_carousel_narrative(session):
    p = Profile(handle="h3", type="competitor", niche="agro", follower_count=100)
    session.add(p)
    session.flush()
    post = Post(profile_id=p.id, instagram_id="IG_NAR", image_url="u", caption="c",
                hashtags=[], likes=0, comments=0, post_type="carousel",
                published_at=datetime.now(timezone.utc))
    session.add(post)
    session.flush()
    analysis = PostAnalysis(
        post_id=post.id,
        virality_score=0.5,
        raw_analysis={},
        carousel_narrative={
            "slide_count": 5,
            "slides": [{"index": 0, "role": "hook", "text": "Você está perdendo dinheiro"}],
            "narrative_arc": "Problema → Causa → Solução → Prova → CTA",
        },
    )
    session.add(analysis)
    session.commit()
    assert analysis.carousel_narrative["slide_count"] == 5


def test_generated_post_strategy_fields(session):
    p = Profile(handle="h4", type="competitor", niche="agro", follower_count=100)
    session.add(p)
    session.flush()
    post = Post(profile_id=p.id, instagram_id="IG_GP", image_url="u", caption="c",
                hashtags=[], likes=0, comments=0, post_type="feed",
                published_at=datetime.now(timezone.utc))
    session.add(post)
    session.flush()
    gp = GeneratedPost(
        source_post_id=post.id,
        hook="Você sabia que 80% dos agrônomos erram nisso?",
        caption="Legenda completa aqui.",
        cta="Entre na Confraria.",
        funnel_stage="topo",
        format="carousel",
        hook_variations={
            "provocacao": "80% dos agrônomos erram nisso.",
            "dado": "Pesquisa aponta: produtores que usam esse método ganham 30% mais.",
            "pergunta": "Você já calculou quanto perde por não fazer isso?",
        },
        news_item_ids=[1, 2],
    )
    session.add(gp)
    session.commit()
    assert gp.funnel_stage == "topo"
    assert gp.hook_variations["provocacao"].startswith("80%")


def test_news_item_create(session):
    from datetime import datetime, timezone
    item = NewsItem(
        source="canal_rural",
        title="Soja atinge recorde de exportação",
        summary="Exportações de soja batem recorde histórico no primeiro trimestre.",
        url="https://canalrural.com.br/noticia/soja-recorde",
        published_at=datetime.now(timezone.utc),
        tags=["soja", "exportação", "mercado"],
    )
    session.add(item)
    session.commit()
    assert item.id is not None
    assert "soja" in item.tags


def test_content_calendar_create(session):
    from datetime import datetime, timezone
    cal = ContentCalendar(
        week_start=datetime(2026, 4, 21, tzinfo=timezone.utc),
        entries=[
            {"day": "segunda", "funnel_stage": "topo", "format": "carousel",
             "topic": "Rentabilidade da soja", "angle": "Dado de mercado surpresa",
             "hook": "Você sabia que o custo médio por hectare subiu 18% em 2025?"},
            {"day": "quarta", "funnel_stage": "meio", "format": "feed",
             "topic": "Técnica de negociação com revendedor", "angle": "Prático",
             "hook": "3 erros que todo agrônomo comete na hora de negociar insumos"},
        ],
    )
    session.add(cal)
    session.commit()
    assert len(cal.entries) == 2
```

- [ ] **Step 2: Run tests — expect failures (missing columns/classes)**

```bash
cd /Users/floakii/Claudio/agro-content
python -m pytest tests/test_models.py::test_post_has_slides_column tests/test_models.py::test_news_item_create -v
```

Expected: ImportError or AttributeError (NewsItem not defined yet)

- [ ] **Step 3: Extend models.py**

Open `src/models.py`. Make these changes:

**3a. Add `slides` to `Post` class** — add after the `collected_at` line:
```python
slides: Mapped[list] = mapped_column(JSON, default=list)
```

**3b. Add `carousel_narrative` to `PostAnalysis` class** — add after `raw_analysis` line:
```python
carousel_narrative: Mapped[dict] = mapped_column(JSON, default=dict)
```

**3c. Add strategy fields to `GeneratedPost` class** — add after `created_at` line:
```python
funnel_stage: Mapped[Optional[str]] = mapped_column(String(20))   # topo | meio | fundo
format: Mapped[Optional[str]] = mapped_column(String(20))          # carousel | feed | reel
hook_variations: Mapped[dict] = mapped_column(JSON, default=dict)
news_item_ids: Mapped[list] = mapped_column(JSON, default=list)
```

**3d. Add `NewsItem` class** — add after the `GeneratedPost` class:
```python
class NewsItem(Base):
    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

**3e. Add `ContentCalendar` class** — add after `NewsItem`:
```python
class ContentCalendar(Base):
    __tablename__ = "content_calendars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    week_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    entries: Mapped[list] = mapped_column(JSON, default=list)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
python -m pytest tests/test_models.py -v
```

Expected: All tests PASS (SQLite creates columns from mapped_column definitions)

- [ ] **Step 5: Commit**

```bash
git add src/models.py tests/test_models.py
git commit -m "feat: extend models for content strategy engine"
```

---

## Task 3: Alembic migration 003

**Files:**
- Create: `alembic/versions/003_content_strategy.py`

The migration chain is: `a1b2c3d4e5f6` → `002` → `003`

- [ ] **Step 1: Create migration file**

Create `alembic/versions/003_content_strategy.py` with this content:

```python
"""content_strategy_engine

Revision ID: 003
Revises: 002
Create Date: 2026-04-16 00:00:00.000000

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extend posts
    op.add_column("posts", sa.Column("slides", sa.JSON(), nullable=True))

    # Extend post_analyses
    op.add_column("post_analyses", sa.Column("carousel_narrative", sa.JSON(), nullable=True))

    # Extend generated_posts
    op.add_column("generated_posts", sa.Column("funnel_stage", sa.String(length=20), nullable=True))
    op.add_column("generated_posts", sa.Column("format", sa.String(length=20), nullable=True))
    op.add_column("generated_posts", sa.Column("hook_variations", sa.JSON(), nullable=True))
    op.add_column("generated_posts", sa.Column("news_item_ids", sa.JSON(), nullable=True))

    # New tables
    op.create_table(
        "news_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )

    op.create_table(
        "content_calendars",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("week_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("entries", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("content_calendars")
    op.drop_table("news_items")
    op.drop_column("generated_posts", "news_item_ids")
    op.drop_column("generated_posts", "hook_variations")
    op.drop_column("generated_posts", "format")
    op.drop_column("generated_posts", "funnel_stage")
    op.drop_column("post_analyses", "carousel_narrative")
    op.drop_column("posts", "slides")
```

- [ ] **Step 2: Run migration against Railway DB**

```bash
cd /Users/floakii/Claudio/agro-content
python -m alembic upgrade 003
```

Expected: `Running upgrade 002 -> 003, content_strategy_engine`

- [ ] **Step 3: Verify**

```bash
python -m alembic current
```

Expected: `003 (head)`

- [ ] **Step 4: Commit**

```bash
git add alembic/versions/003_content_strategy.py
git commit -m "feat: migration 003 - content strategy engine schema"
```

---

## Task 4: News Monitor

**Files:**
- Create: `src/collector/news_monitor.py`
- Create: `tests/test_news_monitor.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_news_monitor.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from src.models import NewsItem
from src.collector.news_monitor import (
    _extract_tags,
    _parse_feed,
    fetch_all_feeds,
    get_recent_news,
)


def test_extract_tags_soja():
    text = "Exportação de soja bate recorde histórico no Brasil"
    tags = _extract_tags(text)
    assert "soja" in tags


def test_extract_tags_milho():
    text = "Safra de milho segunda safra começa colheita em MT"
    tags = _extract_tags(text)
    assert "milho" in tags


def test_extract_tags_mercado():
    text = "Preços no mercado de commodities agrícolas disparam"
    tags = _extract_tags(text)
    assert "mercado" in tags


def test_extract_tags_no_match():
    text = "Notícia sem palavras-chave do agro"
    tags = _extract_tags(text)
    assert tags == []


def test_parse_feed_returns_dicts():
    mock_feed = MagicMock()
    mock_entry = MagicMock()
    mock_entry.title = "Soja em alta"
    mock_entry.get.side_effect = lambda key, default=None: {
        "summary": "Preço da soja sobe.",
        "link": "https://example.com/soja",
    }.get(key, default)
    mock_entry.published_parsed = (2026, 4, 16, 10, 0, 0, 0, 0, 0)
    mock_feed.entries = [mock_entry]

    with patch("src.collector.news_monitor.feedparser.parse", return_value=mock_feed):
        items = _parse_feed("canal_rural", "https://example.com/feed")

    assert len(items) == 1
    assert items[0]["title"] == "Soja em alta"
    assert items[0]["source"] == "canal_rural"
    assert "soja" in items[0]["tags"]


def test_fetch_all_feeds_saves_new_skips_duplicates(session):
    existing = NewsItem(
        source="canal_rural",
        title="Já existe",
        url="https://example.com/existing",
        published_at=datetime.now(timezone.utc),
        tags=["soja"],
    )
    session.add(existing)
    session.commit()

    new_items = [
        {
            "source": "globo_rural",
            "title": "Nova notícia",
            "summary": "Resumo.",
            "url": "https://example.com/new",
            "published_at": datetime.now(timezone.utc),
            "tags": ["milho"],
        },
        {
            "source": "canal_rural",
            "title": "Já existe",
            "summary": None,
            "url": "https://example.com/existing",  # duplicate
            "published_at": datetime.now(timezone.utc),
            "tags": ["soja"],
        },
    ]

    with patch("src.collector.news_monitor._fetch_all_raw", return_value=new_items):
        saved = fetch_all_feeds(session)

    assert saved == 1
    assert session.query(NewsItem).count() == 2


def test_get_recent_news_filters_by_days(session):
    from datetime import timedelta
    old = NewsItem(source="agrolink", title="Velha", url="https://a.com/old",
                   published_at=datetime.now(timezone.utc) - timedelta(days=10), tags=["soja"])
    recent = NewsItem(source="agrolink", title="Recente", url="https://a.com/new",
                      published_at=datetime.now(timezone.utc) - timedelta(days=2), tags=["soja"])
    session.add_all([old, recent])
    session.commit()

    results = get_recent_news(session, days=7)
    assert len(results) == 1
    assert results[0].title == "Recente"


def test_get_recent_news_filters_by_tag(session):
    n1 = NewsItem(source="agrolink", title="Soja", url="https://a.com/s",
                  published_at=datetime.now(timezone.utc), tags=["soja"])
    n2 = NewsItem(source="agrolink", title="Milho", url="https://a.com/m",
                  published_at=datetime.now(timezone.utc), tags=["milho"])
    session.add_all([n1, n2])
    session.commit()

    results = get_recent_news(session, days=7, tags=["soja"])
    assert len(results) == 1
    assert results[0].title == "Soja"
```

- [ ] **Step 2: Run tests — expect ImportError**

```bash
python -m pytest tests/test_news_monitor.py -v
```

Expected: `ImportError: cannot import name '_extract_tags' from 'src.collector.news_monitor'`

- [ ] **Step 3: Implement news_monitor.py**

Create `src/collector/news_monitor.py`:

```python
import logging
from calendar import timegm
from datetime import datetime, timezone, timedelta
from typing import List, Optional

import feedparser
from sqlalchemy.orm import Session

from src.models import NewsItem

logger = logging.getLogger(__name__)

_RSS_SOURCES = {
    "canal_rural": "https://www.canalrural.com.br/feed/",
    "globo_rural": "https://revistagloborural.globo.com/rss",
    "agrolink": "https://www.agrolink.com.br/noticias/rss.aspx",
    "noticias_agricolas": "https://www.noticiasagricolas.com.br/rss/noticias.xml",
}

_KEYWORD_TAGS = {
    "soja": ["soja", "soybean"],
    "milho": ["milho", "corn", "maize"],
    "café": ["café", "coffee", "cafeicultura"],
    "cana": ["cana", "cana-de-açúcar", "sucroalcooleiro"],
    "algodão": ["algodão", "cotton"],
    "mercado": ["mercado", "preço", "cotação", "commodity", "bolsa"],
    "clima": ["clima", "chuva", "seca", "estiagem", "precipitação", "el niño", "la niña"],
    "tecnologia": ["tecnologia", "precision", "drone", "startup", "agtech"],
    "exportação": ["exportação", "exportações", "embarque", "comércio exterior"],
    "insumos": ["insumos", "fertilizante", "defensivo", "herbicida", "fungicida"],
    "crédito": ["crédito", "financiamento", "custeio", "pronaf", "pronamp"],
    "venda": ["venda", "vendas", "comercialização", "negociação"],
}


def _extract_tags(text: str) -> List[str]:
    text_lower = text.lower()
    found = []
    for tag, keywords in _KEYWORD_TAGS.items():
        if any(kw in text_lower for kw in keywords):
            found.append(tag)
    return found


def _parse_feed(source: str, url: str) -> List[dict]:
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries:
        title = getattr(entry, "title", "")
        summary = entry.get("summary") or entry.get("description") or ""
        link = entry.get("link", "")
        if not link:
            continue
        published_at = datetime.now(timezone.utc)
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published_at = datetime.fromtimestamp(timegm(entry.published_parsed), tz=timezone.utc)
        tags = _extract_tags(f"{title} {summary}")
        items.append({
            "source": source,
            "title": title,
            "summary": summary[:500] if summary else None,
            "url": link,
            "published_at": published_at,
            "tags": tags,
        })
    return items


def _fetch_all_raw() -> List[dict]:
    all_items = []
    for source, url in _RSS_SOURCES.items():
        try:
            items = _parse_feed(source, url)
            all_items.extend(items)
            logger.info("Fetched %d items from %s", len(items), source)
        except Exception as exc:
            logger.error("Failed to fetch %s: %s", source, exc)
    return all_items


def fetch_all_feeds(session: Session) -> int:
    """Poll all RSS feeds and save new items. Returns count of new items saved."""
    raw_items = _fetch_all_raw()
    existing_urls = {url for (url,) in session.query(NewsItem.url).all()}
    saved = 0
    for item in raw_items:
        if item["url"] in existing_urls:
            continue
        news = NewsItem(**item)
        session.add(news)
        existing_urls.add(item["url"])
        saved += 1
    session.commit()
    logger.info("Saved %d new news items", saved)
    return saved


def get_recent_news(
    session: Session,
    days: int = 7,
    tags: Optional[List[str]] = None,
) -> List[NewsItem]:
    """Return news items from the last `days` days, optionally filtered by tags."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = session.query(NewsItem).filter(NewsItem.published_at >= cutoff)
    items = query.order_by(NewsItem.published_at.desc()).all()
    if tags:
        items = [i for i in items if any(t in i.tags for t in tags)]
    return items
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
python -m pytest tests/test_news_monitor.py -v
```

Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/collector/news_monitor.py tests/test_news_monitor.py
git commit -m "feat: news monitor - RSS polling for 4 agro sources"
```

---

## Task 5: Seasonal Agro Context

**Files:**
- Create: `src/generator/seasonal.py`
- Create: `tests/test_seasonal.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_seasonal.py`:

```python
from unittest.mock import patch
from src.generator.seasonal import get_seasonal_context


def test_returns_string():
    ctx = get_seasonal_context()
    assert isinstance(ctx, str)
    assert len(ctx) > 20


def test_march_april_context():
    with patch("src.generator.seasonal.datetime") as mock_dt:
        mock_dt.now.return_value.month = 3
        ctx = get_seasonal_context()
    assert "soja" in ctx.lower()
    assert "colheita" in ctx.lower()


def test_july_august_context():
    with patch("src.generator.seasonal.datetime") as mock_dt:
        mock_dt.now.return_value.month = 7
        ctx = get_seasonal_context()
    assert "soja" in ctx.lower()
    assert "plantio" in ctx.lower() or "planejamento" in ctx.lower()


def test_november_december_context():
    with patch("src.generator.seasonal.datetime") as mock_dt:
        mock_dt.now.return_value.month = 11
        ctx = get_seasonal_context()
    assert "soja" in ctx.lower()
```

- [ ] **Step 2: Run tests — expect ImportError**

```bash
python -m pytest tests/test_seasonal.py -v
```

Expected: `ImportError: cannot import name 'get_seasonal_context'`

- [ ] **Step 3: Implement seasonal.py**

Create `src/generator/seasonal.py`:

```python
from datetime import datetime

_SEASONAL_CALENDAR = {
    1: (
        "Janeiro/Fevereiro — Soja em desenvolvimento vegetativo no Cerrado e Sul. "
        "Produtor preocupado com clima e pragas. Milho verão em enchimento de grãos. "
        "Tópicos quentes: manejo de doenças, previsão climática, mercado de soja."
    ),
    2: (
        "Janeiro/Fevereiro — Soja em desenvolvimento vegetativo no Cerrado e Sul. "
        "Produtor preocupado com clima e pragas. Milho verão em enchimento de grãos. "
        "Tópicos quentes: manejo de doenças, previsão climática, mercado de soja."
    ),
    3: (
        "Março/Abril — Colheita de soja no Centro-Oeste. Segunda safra de milho (safrinha) "
        "em desenvolvimento vegetativo no MT e MS. Produtor tomando decisões de venda e "
        "planejando próxima safra. Tópicos quentes: preço da soja, comercialização, custo de produção, "
        "análise de solo para próxima safra."
    ),
    4: (
        "Março/Abril — Colheita de soja no Centro-Oeste. Segunda safra de milho (safrinha) "
        "em desenvolvimento vegetativo no MT e MS. Produtor tomando decisões de venda e "
        "planejando próxima safra. Tópicos quentes: preço da soja, comercialização, custo de produção, "
        "análise de solo para próxima safra."
    ),
    5: (
        "Maio/Junho — Segunda safra de milho em colheita no Centro-Oeste. Entressafra da soja. "
        "Período de planejamento e compra de insumos para a próxima safra. Café em colheita "
        "(arábica no Sul de MG). Tópicos quentes: planejamento financeiro, insumos, crédito rural, "
        "retenção de soja, preço do milho."
    ),
    6: (
        "Maio/Junho — Segunda safra de milho em colheita no Centro-Oeste. Entressafra da soja. "
        "Período de planejamento e compra de insumos para a próxima safra. Café em colheita "
        "(arábica no Sul de MG). Tópicos quentes: planejamento financeiro, insumos, crédito rural, "
        "retenção de soja, preço do milho."
    ),
    7: (
        "Julho/Agosto — Mercado de insumos aquecido. Produtor definindo fornecedores e fechando "
        "contratos de compra de sementes e fertilizantes para a safra de soja. Regiões mais cedo "
        "já preparam solo. Tópicos quentes: negociação de insumos, análise de solo, escolha de "
        "variedades, planejamento da safra 2026/27."
    ),
    8: (
        "Julho/Agosto — Mercado de insumos aquecido. Produtor definindo fornecedores e fechando "
        "contratos de compra de sementes e fertilizantes para a safra de soja. Regiões mais cedo "
        "já preparam solo. Tópicos quentes: negociação de insumos, análise de solo, escolha de "
        "variedades, planejamento da safra 2026/27."
    ),
    9: (
        "Setembro/Outubro — Plantio de soja começa nas regiões mais precoces (MT, GO). "
        "Cana-de-açúcar em colheita plena no Centro-Sul. Café arábica em colheita final. "
        "Produtor ansioso com janela de plantio e condições climáticas. "
        "Tópicos quentes: época de plantio, tratamento de sementes, população de plantas, "
        "monitoramento de pragas na emergência."
    ),
    10: (
        "Setembro/Outubro — Plantio de soja começa nas regiões mais precoces (MT, GO). "
        "Cana-de-açúcar em colheita plena no Centro-Sul. Café arábica em colheita final. "
        "Produtor ansioso com janela de plantio e condições climáticas. "
        "Tópicos quentes: época de plantio, tratamento de sementes, população de plantas, "
        "monitoramento de pragas na emergência."
    ),
    11: (
        "Novembro/Dezembro — Plantio de soja consolidado em quase todo o Brasil. Milho verão "
        "começando no Sul. Produtor focado no manejo de lavoura (herbicidas, fungicidas). "
        "Tópicos quentes: controle de pragas, manejo de doenças, aplicação de fungicidas "
        "na soja, perspectivas de produção para a safra."
    ),
    12: (
        "Novembro/Dezembro — Plantio de soja consolidado em quase todo o Brasil. Milho verão "
        "começando no Sul. Produtor focado no manejo de lavoura (herbicidas, fungicidas). "
        "Tópicos quentes: controle de pragas, manejo de doenças, aplicação de fungicidas "
        "na soja, perspectivas de produção para a safra."
    ),
}


def get_seasonal_context() -> str:
    """Return the current month's agro seasonal context string."""
    month = datetime.now().month
    return _SEASONAL_CALENDAR[month]
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
python -m pytest tests/test_seasonal.py -v
```

Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/generator/seasonal.py tests/test_seasonal.py
git commit -m "feat: seasonal agro context module"
```

---

## Task 6: Competitor Gap Analyzer

**Files:**
- Create: `src/analyzer/gap_analyzer.py`
- Create: `tests/test_gap_analyzer.py`

The gap analyzer compares topics covered by competitor posts (via `raw_analysis` themes) against topics covered by Nathan's own posts. Returns a ranked list of gaps.

- [ ] **Step 1: Write failing tests**

Create `tests/test_gap_analyzer.py`:

```python
import pytest
from datetime import datetime, timezone
from src.models import Profile, Post, PostAnalysis
from src.analyzer.gap_analyzer import compute_gaps, _extract_topics


def _make_profile(session, handle, ptype):
    p = Profile(handle=handle, type=ptype, niche="agro", follower_count=1000)
    session.add(p)
    session.flush()
    return p


def _make_post_with_analysis(session, profile, insta_id, themes):
    post = Post(
        profile_id=profile.id,
        instagram_id=insta_id,
        image_url="https://example.com/img.jpg",
        caption="Caption",
        hashtags=[],
        likes=100,
        comments=5,
        post_type="feed",
        published_at=datetime.now(timezone.utc),
    )
    session.add(post)
    session.flush()
    analysis = PostAnalysis(
        post_id=post.id,
        virality_score=0.5,
        raw_analysis={"dominant_themes": themes},
    )
    session.add(analysis)
    session.flush()
    return post


def test_extract_topics_from_raw_analysis():
    raw = {"dominant_themes": ["rentabilidade", "manejo de pragas"]}
    topics = _extract_topics(raw)
    assert "rentabilidade" in topics
    assert "manejo de pragas" in topics


def test_extract_topics_empty():
    topics = _extract_topics({})
    assert topics == []


def test_compute_gaps_returns_list(session):
    competitor = _make_profile(session, "concorrente1", "competitor")
    own = _make_profile(session, "nathanlimagro", "own")

    _make_post_with_analysis(session, competitor, "C1", ["rentabilidade", "venda"])
    _make_post_with_analysis(session, competitor, "C2", ["rentabilidade", "insumos"])
    _make_post_with_analysis(session, own, "N1", ["insumos"])

    session.commit()

    gaps = compute_gaps(session)
    assert isinstance(gaps, list)
    assert len(gaps) > 0


def test_compute_gaps_identifies_uncovered_topic(session):
    competitor = _make_profile(session, "comp2", "competitor")
    own = _make_profile(session, "own2", "own")

    _make_post_with_analysis(session, competitor, "C3", ["rentabilidade"])
    _make_post_with_analysis(session, competitor, "C4", ["rentabilidade"])
    _make_post_with_analysis(session, own, "N2", ["insumos"])

    session.commit()

    gaps = compute_gaps(session)
    topics = [g["topic"] for g in gaps]
    assert "rentabilidade" in topics


def test_compute_gaps_no_competitors_returns_empty(session):
    own = _make_profile(session, "own3", "own")
    _make_post_with_analysis(session, own, "N3", ["venda"])
    session.commit()

    gaps = compute_gaps(session)
    assert gaps == []
```

- [ ] **Step 2: Run tests — expect ImportError**

```bash
python -m pytest tests/test_gap_analyzer.py -v
```

Expected: `ImportError: cannot import name 'compute_gaps'`

- [ ] **Step 3: Implement gap_analyzer.py**

Create `src/analyzer/gap_analyzer.py`:

```python
import logging
from collections import Counter
from typing import List

from sqlalchemy.orm import Session

from src.models import Post, PostAnalysis, Profile

logger = logging.getLogger(__name__)


def _extract_topics(raw_analysis: dict) -> List[str]:
    """Extract topic strings from raw_analysis JSON."""
    themes = raw_analysis.get("dominant_themes", [])
    if isinstance(themes, list):
        return [str(t) for t in themes if t]
    return []


def compute_gaps(session: Session) -> List[dict]:
    """
    Compare topics covered by competitor posts vs own posts.
    Returns list of dicts: [{topic, competitor_count, own_count, gap_score}]
    sorted by gap_score descending.
    """
    # Collect competitor topics
    competitor_posts = (
        session.query(PostAnalysis)
        .join(PostAnalysis.post)
        .join(Post.profile)
        .filter(Profile.type == "competitor")
        .all()
    )
    if not competitor_posts:
        return []

    competitor_counts: Counter = Counter()
    for analysis in competitor_posts:
        for topic in _extract_topics(analysis.raw_analysis or {}):
            competitor_counts[topic] += 1

    # Collect own topics
    own_posts = (
        session.query(PostAnalysis)
        .join(PostAnalysis.post)
        .join(Post.profile)
        .filter(Profile.type == "own")
        .all()
    )
    own_counts: Counter = Counter()
    for analysis in own_posts:
        for topic in _extract_topics(analysis.raw_analysis or {}):
            own_counts[topic] += 1

    # Compute gaps
    total_competitor = sum(competitor_counts.values()) or 1
    gaps = []
    for topic, comp_count in competitor_counts.items():
        own_count = own_counts.get(topic, 0)
        comp_share = comp_count / total_competitor
        gap_score = comp_share * (1 - min(own_count / max(comp_count, 1), 1))
        gaps.append({
            "topic": topic,
            "competitor_count": comp_count,
            "own_count": own_count,
            "gap_score": round(gap_score, 4),
        })

    gaps.sort(key=lambda x: x["gap_score"], reverse=True)
    logger.info("Gap analysis: %d topics found, top gap: %s", len(gaps), gaps[0]["topic"] if gaps else "none")
    return gaps
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
python -m pytest tests/test_gap_analyzer.py -v
```

Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/analyzer/gap_analyzer.py tests/test_gap_analyzer.py
git commit -m "feat: competitor gap analyzer"
```

---

## Task 7: Run full test suite and push

- [ ] **Step 1: Run all tests**

```bash
cd /Users/floakii/Claudio/agro-content
python -m pytest tests/ -v
```

Expected: All tests PASS. If any existing tests fail, investigate and fix before continuing.

- [ ] **Step 2: Push to remote**

```bash
git push
```

Expected: Branch pushed. Railway will auto-deploy the migration if configured.

---

## Plan A Complete

After this plan, Plan B (Intelligence: carousel analyzer, strategy engine, calendar generator) can begin.
