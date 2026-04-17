# Carousel Theme Suggestions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add AI-generated theme suggestions to the carousel drawer — generated daily by APScheduler using competitor gap analysis, viral posts, and news headlines — displayed as clickable chips that auto-fill the theme textarea.

**Architecture:** A new `CarouselSuggestion` DB model stores snapshots of 6 GPT-4o-generated `{title, rationale}` pairs. APScheduler runs a job daily at 06:00 UTC that reads from the DB and calls GPT-4o. Two new FastAPI endpoints expose the cached result and allow manual refresh. The frontend adds a "Sugestões IA" section above the textarea.

**Tech Stack:** Python 3.11, SQLAlchemy 2, Alembic, APScheduler 3, OpenAI GPT-4o, FastAPI 0.111, Next.js 16 TypeScript.

---

## File Structure

```
src/models.py                              MODIFY — add CarouselSuggestion model
alembic/versions/004_carousel_suggestions.py  NEW — migration
src/carousel/theme_suggester.py            NEW — generate_theme_suggestions()
api/routers/carousel.py                    MODIFY — 2 new endpoints
api/main.py                                MODIFY — APScheduler startup/shutdown
tests/test_carousel_suggestions.py         NEW — unit tests for suggester
tests/test_api_carousel.py                 MODIFY — 2 new endpoint tests
web/components/drawers/DrawerCarrossel.tsx MODIFY — suggestions UI section
```

---

### Task 1: CarouselSuggestion model + migration

**Files:**
- Modify: `src/models.py`
- Create: `alembic/versions/004_carousel_suggestions.py`

- [ ] **Step 1: Add model to `src/models.py`**

At the end of `src/models.py`, after the `ContentCalendar` class, add:

```python
class CarouselSuggestion(Base):
    __tablename__ = "carousel_suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    themes: Mapped[list] = mapped_column(JSON, default=list)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 2: Create alembic migration**

Create `alembic/versions/004_carousel_suggestions.py`:

```python
"""carousel_suggestions table

Revision ID: 004
Revises: 003
Create Date: 2026-04-17 00:00:00.000000

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "carousel_suggestions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("themes", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("carousel_suggestions")
```

- [ ] **Step 3: Run migration locally to verify**

```bash
DATABASE_URL=sqlite:///test_migration.db alembic upgrade head
sqlite3 test_migration.db ".tables"
```

Expected output includes: `carousel_suggestions`

```bash
rm test_migration.db
```

- [ ] **Step 4: Commit**

```bash
git add src/models.py alembic/versions/004_carousel_suggestions.py
git commit -m "feat: CarouselSuggestion model and migration"
```

---

### Task 2: Theme suggester module

**Files:**
- Create: `src/carousel/theme_suggester.py`
- Create: `tests/test_carousel_suggestions.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_carousel_suggestions.py`:

```python
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session
from src.models import Base, CarouselSuggestion, NewsItem, Post, PostAnalysis, Profile


engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(engine)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


def _mock_openai(titles):
    themes = [{"title": t, "rationale": "test"} for t in titles]
    msg = MagicMock()
    msg.content = json.dumps(themes)
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_generate_stores_six_suggestions():
    from src.carousel.theme_suggester import generate_theme_suggestions
    titles = [f"Tema {i}" for i in range(6)]
    with patch("src.carousel.theme_suggester.openai_client.chat.completions.create",
               return_value=_mock_openai(titles)):
        with Session(engine) as s:
            result = generate_theme_suggestions(s)
    assert len(result.themes) == 6
    assert result.themes[0]["title"] == "Tema 0"


def test_generate_persists_to_db():
    from src.carousel.theme_suggester import generate_theme_suggestions
    titles = [f"Tema {i}" for i in range(6)]
    with patch("src.carousel.theme_suggester.openai_client.chat.completions.create",
               return_value=_mock_openai(titles)):
        with Session(engine) as s:
            generate_theme_suggestions(s)
    with Session(engine) as s:
        row = s.query(CarouselSuggestion).order_by(CarouselSuggestion.generated_at.desc()).first()
    assert row is not None
    assert len(row.themes) == 6


def test_generate_fallback_when_db_empty():
    """When no posts/news exist, GPT-4o still called with fallback prompt."""
    from src.carousel.theme_suggester import generate_theme_suggestions
    titles = [f"Fallback {i}" for i in range(6)]
    with patch("src.carousel.theme_suggester.openai_client.chat.completions.create",
               return_value=_mock_openai(titles)) as mock_create:
        with Session(engine) as s:
            result = generate_theme_suggestions(s)
    assert mock_create.called
    assert len(result.themes) == 6


def test_generate_includes_news_in_prompt():
    """Recent news titles appear in the user prompt sent to GPT-4o."""
    from src.carousel.theme_suggester import generate_theme_suggestions
    with Session(engine) as s:
        item = NewsItem(
            source="canal_rural",
            title="Soja em alta no Mato Grosso",
            url="https://example.com/soja",
            published_at=datetime.now(timezone.utc) - timedelta(hours=10),
        )
        s.add(item)
        s.commit()

    titles = [f"Tema {i}" for i in range(6)]
    with patch("src.carousel.theme_suggester.openai_client.chat.completions.create",
               return_value=_mock_openai(titles)) as mock_create:
        with Session(engine) as s:
            generate_theme_suggestions(s)

    call_kwargs = mock_create.call_args
    user_content = call_kwargs[1]["messages"][1]["content"]
    assert "Soja em alta" in user_content
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_carousel_suggestions.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.carousel.theme_suggester'`

- [ ] **Step 3: Implement `src/carousel/theme_suggester.py`**

```python
import json
import logging
from datetime import datetime, timezone, timedelta

from openai import OpenAI
from sqlalchemy.orm import Session

from src.config import OPENAI_API_KEY
from src.analyzer.gap_analyzer import compute_gaps
from src.models import CarouselSuggestion, NewsItem, Post, PostAnalysis, Profile

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

_SYSTEM_PROMPT = """Você é especialista em marketing de conteúdo para o agronegócio brasileiro no Instagram.
Crie exatamente 6 sugestões de tema para carrosséis com alta chance de viralização.
Use os dados fornecidos (gaps, posts virais, notícias) e complemente com seu próprio conhecimento sobre sazonalidade, mercado e tendências agro.
Retorne APENAS um JSON array com exatamente 6 objetos:
[{"title": "<tema curto e impactante>", "rationale": "<uma frase explicando o sinal de dados>"}, ...]"""


def generate_theme_suggestions(session: Session) -> CarouselSuggestion:
    """Gather DB signals, call GPT-4o, store and return a CarouselSuggestion row."""
    # Gap topics
    gaps = compute_gaps(session)
    top_gaps = [g["topic"] for g in gaps[:5]]

    # Top viral post captions
    viral_posts = (
        session.query(Post)
        .join(Post.analysis)
        .filter(PostAnalysis.virality_score > 0.5)
        .order_by(PostAnalysis.virality_score.desc())
        .limit(5)
        .all()
    )
    viral_captions = [p.caption for p in viral_posts if p.caption]

    # Recent news
    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    news = (
        session.query(NewsItem)
        .filter(NewsItem.published_at >= cutoff)
        .order_by(NewsItem.published_at.desc())
        .limit(10)
        .all()
    )
    news_titles = [n.title for n in news]

    user_content = json.dumps({
        "gap_topics": top_gaps,
        "viral_captions": viral_captions,
        "recent_news": news_titles,
    }, ensure_ascii=False)

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        max_tokens=800,
    )

    try:
        themes = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError as exc:
        logger.error("GPT-4o returned invalid JSON for theme suggestions: %s", exc)
        raise

    suggestion = CarouselSuggestion(themes=themes)
    session.add(suggestion)
    session.commit()
    session.refresh(suggestion)
    logger.info("Generated %d theme suggestions", len(themes))
    return suggestion
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_carousel_suggestions.py -v
```

Expected: 4 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add src/carousel/theme_suggester.py tests/test_carousel_suggestions.py
git commit -m "feat: theme suggester with GPT-4o + gap/viral/news signals"
```

---

### Task 3: API endpoints + APScheduler

**Files:**
- Modify: `api/routers/carousel.py`
- Modify: `api/main.py`
- Modify: `tests/test_api_carousel.py`

- [ ] **Step 1: Add failing tests to `tests/test_api_carousel.py`**

At the end of the existing `tests/test_api_carousel.py`, add:

```python
from src.models import CarouselSuggestion


def test_get_suggestions_empty():
    response = client.get("/carousel/suggestions")
    assert response.status_code == 204


def test_get_suggestions_returns_latest():
    with Session(engine) as s:
        s.add(CarouselSuggestion(
            themes=[{"title": "Soja alta", "rationale": "gap"}],
            generated_at=datetime.now(timezone.utc),
        ))
        s.add(CarouselSuggestion(
            themes=[{"title": "Milho baixo", "rationale": "viral"}],
            generated_at=datetime.now(timezone.utc),
        ))
        s.commit()
    response = client.get("/carousel/suggestions")
    assert response.status_code == 200
    data = response.json()
    assert data["themes"][0]["title"] == "Milho baixo"


def test_refresh_suggestions():
    from unittest.mock import patch, MagicMock
    mock_suggestion = MagicMock()
    mock_suggestion.id = 1
    mock_suggestion.themes = [{"title": "T", "rationale": "R"}]
    mock_suggestion.generated_at = datetime.now(timezone.utc)
    with patch("api.routers.carousel.generate_theme_suggestions", return_value=mock_suggestion):
        response = client.post("/carousel/suggestions/refresh")
    assert response.status_code == 200
    assert response.json()["themes"][0]["title"] == "T"
```

- [ ] **Step 2: Run new tests to verify they fail**

```bash
pytest tests/test_api_carousel.py::test_get_suggestions_empty tests/test_api_carousel.py::test_get_suggestions_returns_latest tests/test_api_carousel.py::test_refresh_suggestions -v
```

Expected: FAILED — endpoints don't exist yet

- [ ] **Step 3: Add endpoints to `api/routers/carousel.py`**

Add to the existing `api/routers/carousel.py` (after the existing imports, add `generate_theme_suggestions` import and the two new models and routes):

```python
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.models import Carousel, CarouselSuggestion
from src.carousel.generator import generate_carousel
from src.carousel.theme_suggester import generate_theme_suggestions
from api.deps import get_db

router = APIRouter(prefix="/carousel", tags=["carousel"])


class CarouselGenerateIn(BaseModel):
    theme: str


class CarouselOut(BaseModel):
    id: int
    theme: str
    slides: list
    generated_at: datetime


class SuggestionItem(BaseModel):
    title: str
    rationale: str


class CarouselSuggestionOut(BaseModel):
    id: int
    themes: List[SuggestionItem]
    generated_at: datetime


@router.get("", response_model=List[CarouselOut])
def list_carousels(db: Session = Depends(get_db)):
    rows = db.query(Carousel).order_by(Carousel.generated_at.desc()).limit(10).all()
    return [CarouselOut(id=r.id, theme=r.theme, slides=r.slides, generated_at=r.generated_at) for r in rows]


@router.post("/generate", response_model=CarouselOut)
def generate(body: CarouselGenerateIn, db: Session = Depends(get_db)):
    carousel = generate_carousel(theme=body.theme, session=db)
    return CarouselOut(id=carousel.id, theme=carousel.theme, slides=carousel.slides, generated_at=carousel.generated_at)


@router.get("/suggestions")
def get_suggestions(db: Session = Depends(get_db), response: Response = None):
    row = db.query(CarouselSuggestion).order_by(CarouselSuggestion.generated_at.desc()).first()
    if not row:
        response.status_code = 204
        return None
    return CarouselSuggestionOut(id=row.id, themes=row.themes, generated_at=row.generated_at)


@router.post("/suggestions/refresh", response_model=CarouselSuggestionOut)
def refresh_suggestions(db: Session = Depends(get_db)):
    row = generate_theme_suggestions(db)
    return CarouselSuggestionOut(id=row.id, themes=row.themes, generated_at=row.generated_at)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_api_carousel.py -v
```

Expected: all 6 tests PASSED

- [ ] **Step 5: Add APScheduler to `api/main.py`**

Replace the entire `api/main.py` with:

```python
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import competitors, carousel, news, reports, voice, studio
from src.database import get_session
from src.carousel.theme_suggester import generate_theme_suggestions

logger = logging.getLogger(__name__)


def _run_daily_suggestions():
    session = get_session()
    try:
        generate_theme_suggestions(session)
    except Exception as exc:
        logger.error("Daily suggestion job failed: %s", exc)
    finally:
        session.close()


scheduler = BackgroundScheduler()
scheduler.add_job(_run_daily_suggestions, "cron", hour=6, minute=0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    logger.info("APScheduler started")
    yield
    scheduler.shutdown(wait=False)
    logger.info("APScheduler stopped")


app = FastAPI(title="Agro Intel API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(competitors.router)
app.include_router(carousel.router)
app.include_router(news.router)
app.include_router(reports.router)
app.include_router(voice.router)
app.include_router(studio.router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests pass (APScheduler doesn't affect tests — it only runs in the real server process)

- [ ] **Step 7: Commit**

```bash
git add api/routers/carousel.py api/main.py tests/test_api_carousel.py
git commit -m "feat: carousel suggestions endpoints + daily APScheduler job"
```

---

### Task 4: Frontend — suggestions section in DrawerCarrossel

**Files:**
- Modify: `web/components/drawers/DrawerCarrossel.tsx`

- [ ] **Step 1: Replace the component**

Overwrite `web/components/drawers/DrawerCarrossel.tsx` with:

```tsx
'use client'

import { useEffect, useState } from 'react'

interface Slide {
  slide_number: number
  title: string
  copy: string
  cta: string
}

interface Carousel {
  id: number
  theme: string
  slides: Slide[]
  generated_at: string
}

interface Suggestion {
  title: string
  rationale: string
}

interface SuggestionBlock {
  id: number
  themes: Suggestion[]
  generated_at: string
}

export function DrawerCarrossel() {
  const [topic, setTopic] = useState('')
  const [generating, setGenerating] = useState(false)
  const [current, setCurrent] = useState<Carousel | null>(null)
  const [history, setHistory] = useState<Carousel[]>([])
  const [loadingHistory, setLoadingHistory] = useState(true)
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [refreshingSuggestions, setRefreshingSuggestions] = useState(false)

  async function loadHistory() {
    const res = await fetch('/api/carousel')
    if (res.ok) setHistory(await res.json())
    setLoadingHistory(false)
  }

  async function loadSuggestions() {
    const res = await fetch('/api/carousel/suggestions')
    if (res.ok) {
      const data: SuggestionBlock = await res.json()
      setSuggestions(data.themes)
    }
  }

  useEffect(() => {
    loadHistory()
    loadSuggestions()
  }, [])

  async function generate() {
    if (!topic.trim()) return
    setGenerating(true)
    const res = await fetch('/api/carousel/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ theme: topic.trim() }),
    })
    if (res.ok) {
      const data = await res.json()
      setCurrent(data)
      loadHistory()
    }
    setGenerating(false)
  }

  async function refreshSuggestions() {
    setRefreshingSuggestions(true)
    const res = await fetch('/api/carousel/suggestions/refresh', { method: 'POST' })
    if (res.ok) {
      const data: SuggestionBlock = await res.json()
      setSuggestions(data.themes)
    }
    setRefreshingSuggestions(false)
  }

  return (
    <div className="p-6 space-y-5">
      {/* Suggestions section */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
            Sugestões IA
          </p>
          <button
            onClick={refreshSuggestions}
            disabled={refreshingSuggestions}
            className="text-[11px] px-2 py-0.5 rounded"
            style={{ color: refreshingSuggestions ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.4)', background: 'rgba(255,255,255,0.04)' }}
          >
            {refreshingSuggestions ? '⟳' : '↻'}
          </button>
        </div>

        {suggestions.length === 0 ? (
          <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.25)' }}>
            A IA vai gerar sugestões às 06:00 ou clique em ↻
          </p>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {suggestions.map((s, i) => (
              <button
                key={i}
                onClick={() => setTopic(s.title)}
                title={s.rationale}
                className="px-2.5 py-1 rounded-full text-[11px] text-left transition-all"
                style={{
                  background: topic === s.title ? 'rgba(22,163,74,0.15)' : 'rgba(255,255,255,0.04)',
                  border: `1px solid ${topic === s.title ? '#16a34a44' : 'rgba(255,255,255,0.08)'}`,
                  color: topic === s.title ? '#16a34a' : 'rgba(255,255,255,0.55)',
                }}
              >
                {s.title}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Theme textarea */}
      <div className="space-y-2">
        <label className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
          Tema do carrossel
        </label>
        <textarea
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Ex: Alta da soja, irrigação inteligente, gestão de safra..."
          rows={3}
          className="w-full rounded-lg px-3 py-2.5 text-sm resize-none outline-none"
          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#fff' }}
        />
      </div>

      <button
        onClick={generate}
        disabled={generating || !topic.trim()}
        className="w-full py-2.5 rounded-lg text-sm font-semibold transition-all"
        style={{
          background: generating || !topic.trim() ? '#16a34a44' : '#16a34a',
          color: generating || !topic.trim() ? 'rgba(255,255,255,0.4)' : '#fff',
          cursor: generating || !topic.trim() ? 'not-allowed' : 'pointer',
        }}
      >
        {generating ? '⟳ Gerando com GPT-4o...' : '✦ Gerar Carrossel'}
      </button>

      {current && (
        <div className="space-y-2">
          <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
            {current.slides.length} slides gerados
          </p>
          {current.slides.map((slide) => (
            <div
              key={slide.slide_number}
              className="px-3 py-2.5 rounded-lg space-y-1"
              style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
            >
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0"
                  style={{ background: '#16a34a22', color: '#16a34a' }}>
                  {slide.slide_number}
                </span>
                <span className="text-[12px] font-semibold text-white">{slide.title}</span>
              </div>
              <p className="text-[11px] pl-7" style={{ color: 'rgba(255,255,255,0.55)' }}>{slide.copy}</p>
              {slide.cta && (
                <p className="text-[11px] pl-7" style={{ color: '#16a34a' }}>→ {slide.cta}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {!loadingHistory && history.length > 0 && (
        <div className="space-y-2 pt-2 border-t" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
          <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.3)' }}>
            Histórico
          </p>
          {history.map((c) => (
            <button
              key={c.id}
              onClick={() => setCurrent(c)}
              className="w-full text-left px-3 py-2 rounded-lg text-[11px] truncate"
              style={{
                background: current?.id === c.id ? 'rgba(22,163,74,0.1)' : 'rgba(255,255,255,0.02)',
                border: `1px solid ${current?.id === c.id ? '#16a34a33' : 'rgba(255,255,255,0.05)'}`,
                color: 'rgba(255,255,255,0.5)',
              }}
            >
              {c.theme}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: TypeScript check**

```bash
cd web && npx tsc --noEmit
```

Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add web/components/drawers/DrawerCarrossel.tsx
git commit -m "feat: suggestions IA section in DrawerCarrossel"
```

---

### Task 5: Push and deploy

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests pass

- [ ] **Step 2: Push to trigger Railway deploy**

```bash
git push origin main
```

Both services redeploy. The `alembic upgrade head` in `start.sh` runs migration 004 automatically on the FastAPI service.

- [ ] **Step 3: Smoke-test suggestions endpoint**

After deploy (~2 min):

```bash
curl -X POST https://altagro.site/api/carousel/suggestions/refresh \
  -H "Cookie: auth_token=<your-token>"
```

Expected: JSON with 6 themes from GPT-4o.

Open `https://altagro.site`, go to Carrossel drawer — chips appear in the "Sugestões IA" section.
