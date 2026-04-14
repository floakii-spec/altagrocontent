# Instagram Competitor Intelligence Tool — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a pipeline that coleta posts de 20+ concorrentes no Instagram diariamente, analisa imagens com GPT-4o Vision, gera relatórios semanais e produz carrosséis virais adaptados à voz do perfil próprio.

**Architecture:** Python monorepo com módulos separados por responsabilidade (collector, analyzer, reporter, carousel, scheduler) compartilhando modelos SQLAlchemy e um banco PostgreSQL. Dashboard Streamlit com tabs em acordeão.

**Tech Stack:** Python 3.11, PostgreSQL 15, SQLAlchemy, Alembic, Apify, Instaloader, APScheduler, OpenAI SDK (GPT-4o + Vision), Streamlit, pytest, python-dotenv

---

## File Structure

```
agro-content/
├── .env.example
├── requirements.txt
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py
├── src/
│   ├── config.py              # env vars via python-dotenv
│   ├── database.py            # SQLAlchemy engine + session factory
│   ├── models.py              # ORM: Profile, Post, PostAnalysis, ProfileVoice, WeeklyReport, Carousel
│   ├── collector/
│   │   ├── apify_client.py    # Apify Instagram Scraper Actor
│   │   ├── instaloader_client.py  # fallback scraper
│   │   └── collector.py       # orchestrates coleta por perfil
│   ├── analyzer/
│   │   ├── virality.py        # calcula virality_score
│   │   └── image_analyzer.py  # GPT-4o Vision por post
│   ├── reporter/
│   │   ├── weekly_report.py   # gera WeeklyReport com GPT-4o
│   │   └── voice_profiler.py  # gera ProfileVoice com GPT-4o
│   ├── carousel/
│   │   └── generator.py       # gera Carousel sob demanda
│   └── scheduler.py           # APScheduler: coleta diária + relatório semanal
├── dashboard/
│   ├── app.py                 # entry point Streamlit
│   ├── tabs/
│   │   ├── competitors.py     # Tab 1
│   │   ├── posts.py           # Tab 2
│   │   ├── reports.py         # Tab 3
│   │   ├── voice.py           # Tab 4
│   │   └── carousel.py        # Tab 5
│   └── components/
│       └── post_card.py       # card reutilizável de post
└── tests/
    ├── conftest.py
    ├── test_models.py
    ├── test_virality.py
    ├── test_collector.py
    ├── test_image_analyzer.py
    ├── test_weekly_report.py
    ├── test_voice_profiler.py
    └── test_carousel_generator.py
```

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `src/config.py`

- [ ] **Step 1: Criar `requirements.txt`**

```
sqlalchemy==2.0.30
alembic==1.13.1
psycopg2-binary==2.9.9
apify-client==1.7.1
instaloader==4.13.1
openai==1.30.1
apscheduler==3.10.4
streamlit==1.35.0
python-dotenv==1.0.1
pytest==8.2.0
pytest-mock==3.14.0
```

- [ ] **Step 2: Criar `.env.example`**

```
DATABASE_URL=postgresql://user:password@localhost:5432/agro_intel
OPENAI_API_KEY=sk-...
APIFY_API_TOKEN=apify_api_...
```

- [ ] **Step 3: Escrever teste para config**

Arquivo: `tests/test_config.py`

```python
import os
import pytest
from unittest.mock import patch


def test_config_loads_from_env():
    env = {
        "DATABASE_URL": "postgresql://u:p@localhost/test",
        "OPENAI_API_KEY": "sk-test",
        "APIFY_API_TOKEN": "apify-test",
    }
    with patch.dict(os.environ, env):
        from importlib import reload
        import src.config as config
        reload(config)
        assert config.DATABASE_URL == "postgresql://u:p@localhost/test"
        assert config.OPENAI_API_KEY == "sk-test"
        assert config.APIFY_API_TOKEN == "apify-test"


def test_config_raises_if_missing_key():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(KeyError):
            from importlib import reload
            import src.config as config
            reload(config)
```

- [ ] **Step 4: Rodar o teste para confirmar que falha**

```bash
pytest tests/test_config.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'src'`

- [ ] **Step 5: Criar `src/__init__.py` e `src/config.py`**

```python
# src/config.py
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.environ["DATABASE_URL"]
OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]
APIFY_API_TOKEN: str = os.environ["APIFY_API_TOKEN"]
```

Criar também: `src/__init__.py` (vazio)

- [ ] **Step 6: Rodar o teste**

```bash
pytest tests/test_config.py -v
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add requirements.txt .env.example src/__init__.py src/config.py tests/test_config.py
git commit -m "feat: project setup with config and env loading"
```

---

## Task 2: Database Models

**Files:**
- Create: `src/database.py`
- Create: `src/models.py`
- Create: `tests/conftest.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Escrever testes de modelos**

Arquivo: `tests/test_models.py`

```python
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, Profile, Post, PostAnalysis, ProfileVoice, WeeklyReport, Carousel


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def test_create_profile(session):
    p = Profile(handle="agro_example", type="competitor", niche="agronegócio", follower_count=5000)
    session.add(p)
    session.commit()
    assert p.id is not None
    assert p.active is True


def test_create_post(session):
    p = Profile(handle="agro_example", type="competitor", niche="agronegócio", follower_count=5000)
    session.add(p)
    session.flush()
    post = Post(
        profile_id=p.id,
        instagram_id="IG123",
        image_url="https://example.com/img.jpg",
        caption="Safra recorde!",
        hashtags=["agro", "safra"],
        likes=200,
        comments=15,
        post_type="feed",
        published_at=datetime.now(timezone.utc),
    )
    session.add(post)
    session.commit()
    assert post.id is not None


def test_create_post_analysis(session):
    p = Profile(handle="h", type="competitor", niche="agro", follower_count=1000)
    session.add(p)
    session.flush()
    post = Post(profile_id=p.id, instagram_id="IG1", image_url="u", caption="c",
                hashtags=[], likes=100, comments=5, post_type="feed",
                published_at=datetime.now(timezone.utc))
    session.add(post)
    session.flush()
    analysis = PostAnalysis(
        post_id=post.id,
        visual_theme="maquinário",
        visual_format="foto real",
        emotional_tone="inspirador",
        trigger="resultado",
        virality_score=0.42,
        raw_analysis={"summary": "ok"},
    )
    session.add(analysis)
    session.commit()
    assert analysis.id is not None


def test_create_weekly_report(session):
    report = WeeklyReport(
        period_start=datetime(2026, 4, 7),
        period_end=datetime(2026, 4, 13),
        top_formats={"infográfico": 12},
        top_themes={"maquinário": 8},
        language_patterns={"tom": "direto"},
        top_hashtags=["agro", "colheita"],
        viral_posts=[1, 2, 3],
        report_text="# Relatório\n...",
    )
    session.add(report)
    session.commit()
    assert report.id is not None


def test_create_carousel(session):
    c = Carousel(
        theme="Dicas de plantio de soja",
        slides=[{"slide_number": 1, "title": "Título", "copy": "Texto", "cta": "Salve!"}],
        based_on_reports=[1],
    )
    session.add(c)
    session.commit()
    assert c.id is not None
```

- [ ] **Step 2: Rodar testes para confirmar que falham**

```bash
pytest tests/test_models.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'src.models'`

- [ ] **Step 3: Criar `src/database.py`**

```python
# src/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def get_session() -> Session:
    return SessionLocal()
```

- [ ] **Step 4: Criar `src/models.py`**

```python
# src/models.py
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text,
    ARRAY
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    handle: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # competitor | own
    niche: Mapped[Optional[str]] = mapped_column(String(100))
    follower_count: Mapped[Optional[int]] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    posts: Mapped[list["Post"]] = relationship(back_populates="profile")
    voices: Mapped[list["ProfileVoice"]] = relationship(back_populates="profile")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), nullable=False)
    instagram_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    caption: Mapped[Optional[str]] = mapped_column(Text)
    hashtags: Mapped[list] = mapped_column(JSON, default=list)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    post_type: Mapped[str] = mapped_column(String(20))  # feed | reel | carousel
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    profile: Mapped["Profile"] = relationship(back_populates="posts")
    analysis: Mapped[Optional["PostAnalysis"]] = relationship(back_populates="post", uselist=False)


class PostAnalysis(Base):
    __tablename__ = "post_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), unique=True, nullable=False)
    visual_theme: Mapped[Optional[str]] = mapped_column(String(50))
    visual_format: Mapped[Optional[str]] = mapped_column(String(50))
    emotional_tone: Mapped[Optional[str]] = mapped_column(String(50))
    trigger: Mapped[Optional[str]] = mapped_column(String(50))
    virality_score: Mapped[Optional[float]] = mapped_column(Float)
    raw_analysis: Mapped[dict] = mapped_column(JSON, default=dict)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    post: Mapped["Post"] = relationship(back_populates="analysis")


class ProfileVoice(Base):
    __tablename__ = "profile_voice"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), nullable=False)
    vocabulary: Mapped[dict] = mapped_column(JSON, default=dict)
    tone: Mapped[Optional[str]] = mapped_column(String(100))
    dominant_themes: Mapped[list] = mapped_column(JSON, default=list)
    competitor_comparison: Mapped[dict] = mapped_column(JSON, default=dict)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    profile: Mapped["Profile"] = relationship(back_populates="voices")


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    top_formats: Mapped[dict] = mapped_column(JSON, default=dict)
    top_themes: Mapped[dict] = mapped_column(JSON, default=dict)
    language_patterns: Mapped[dict] = mapped_column(JSON, default=dict)
    top_hashtags: Mapped[list] = mapped_column(JSON, default=list)
    viral_posts: Mapped[list] = mapped_column(JSON, default=list)
    report_text: Mapped[Optional[str]] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Carousel(Base):
    __tablename__ = "carousels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    theme: Mapped[str] = mapped_column(Text, nullable=False)
    slides: Mapped[list] = mapped_column(JSON, default=list)
    based_on_reports: Mapped[list] = mapped_column(JSON, default=list)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 5: Rodar testes**

```bash
pytest tests/test_models.py -v
```
Expected: PASS (5 testes)

- [ ] **Step 6: Commit**

```bash
git add src/database.py src/models.py tests/test_models.py
git commit -m "feat: database models for profiles, posts, analyses, reports and carousels"
```

---

## Task 3: Alembic Migrations

**Files:**
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/versions/001_initial_schema.py`

- [ ] **Step 1: Inicializar Alembic**

```bash
pip install alembic
alembic init alembic
```

- [ ] **Step 2: Editar `alembic/env.py` para usar os modelos**

Substituir o conteúdo de `alembic/env.py` por:

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from src.models import Base
from src.config import DATABASE_URL

config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 3: Gerar a migration inicial**

```bash
alembic revision --autogenerate -m "initial_schema"
```
Expected: arquivo criado em `alembic/versions/`

- [ ] **Step 4: Aplicar a migration (requer PostgreSQL rodando)**

```bash
alembic upgrade head
```
Expected: tabelas criadas no banco

- [ ] **Step 5: Commit**

```bash
git add alembic.ini alembic/
git commit -m "feat: alembic migrations for initial schema"
```

---

## Task 4: Virality Score

**Files:**
- Create: `src/analyzer/virality.py`
- Create: `tests/test_virality.py`

- [ ] **Step 1: Escrever testes**

Arquivo: `tests/test_virality.py`

```python
import pytest
from src.analyzer.virality import calculate_virality_score


def test_basic_score():
    score = calculate_virality_score(likes=1000, comments=50, follower_count=10000)
    # (1000 + 50*2) / 10000 = 1100/10000 = 0.11
    assert round(score, 4) == 0.11


def test_score_clamped_to_one():
    score = calculate_virality_score(likes=9999, comments=9999, follower_count=100)
    assert score == 1.0


def test_zero_followers_returns_zero():
    score = calculate_virality_score(likes=100, comments=10, follower_count=0)
    assert score == 0.0


def test_zero_engagement_returns_zero():
    score = calculate_virality_score(likes=0, comments=0, follower_count=5000)
    assert score == 0.0
```

- [ ] **Step 2: Rodar testes para confirmar que falham**

```bash
pytest tests/test_virality.py -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Criar `src/analyzer/__init__.py` e `src/analyzer/virality.py`**

```python
# src/analyzer/virality.py


def calculate_virality_score(likes: int, comments: int, follower_count: int) -> float:
    """Normaliza engajamento pelo número de seguidores. Retorna valor entre 0 e 1."""
    if follower_count == 0:
        return 0.0
    raw = (likes + comments * 2) / follower_count
    return min(raw, 1.0)
```

- [ ] **Step 4: Rodar testes**

```bash
pytest tests/test_virality.py -v
```
Expected: PASS (4 testes)

- [ ] **Step 5: Commit**

```bash
git add src/analyzer/__init__.py src/analyzer/virality.py tests/test_virality.py
git commit -m "feat: virality score calculation"
```

---

## Task 5: Apify Collector

**Files:**
- Create: `src/collector/__init__.py`
- Create: `src/collector/apify_client.py`
- Create: `tests/test_collector.py` (parcial — Apify)

- [ ] **Step 1: Escrever testes com mock do Apify**

Arquivo: `tests/test_collector.py`

```python
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from src.collector.apify_client import fetch_posts_apify


MOCK_APIFY_ITEMS = [
    {
        "id": "IG001",
        "displayUrl": "https://example.com/img1.jpg",
        "caption": "Safra recorde de soja!",
        "hashtags": ["agro", "soja"],
        "likesCount": 500,
        "commentsCount": 30,
        "type": "Image",
        "timestamp": "2026-04-10T10:00:00.000Z",
    },
    {
        "id": "IG002",
        "displayUrl": "https://example.com/img2.jpg",
        "caption": "Maquinário moderno",
        "hashtags": ["maquinas"],
        "likesCount": 200,
        "commentsCount": 10,
        "type": "Video",
        "timestamp": "2026-04-11T12:00:00.000Z",
    },
]


def test_fetch_posts_apify_returns_normalized_posts():
    mock_dataset = MagicMock()
    mock_dataset.iterate_items.return_value = iter(MOCK_APIFY_ITEMS)

    mock_run = MagicMock()
    mock_run.wait_for_finish.return_value = None
    mock_run.default_dataset.return_value = mock_dataset

    mock_actor = MagicMock()
    mock_actor.call.return_value = mock_run

    mock_client = MagicMock()
    mock_client.actor.return_value = mock_actor

    with patch("src.collector.apify_client.ApifyClient", return_value=mock_client):
        posts = fetch_posts_apify(handle="agro_example", token="fake-token", months_back=6)

    assert len(posts) == 2
    assert posts[0]["instagram_id"] == "IG001"
    assert posts[0]["image_url"] == "https://example.com/img1.jpg"
    assert posts[0]["caption"] == "Safra recorde de soja!"
    assert posts[0]["hashtags"] == ["agro", "soja"]
    assert posts[0]["likes"] == 500
    assert posts[0]["comments"] == 30
    assert posts[0]["post_type"] == "feed"
    assert isinstance(posts[0]["published_at"], datetime)


def test_fetch_posts_apify_maps_video_to_reel():
    mock_dataset = MagicMock()
    mock_dataset.iterate_items.return_value = iter([MOCK_APIFY_ITEMS[1]])

    mock_run = MagicMock()
    mock_run.wait_for_finish.return_value = None
    mock_run.default_dataset.return_value = mock_dataset

    mock_actor = MagicMock()
    mock_actor.call.return_value = mock_run

    mock_client = MagicMock()
    mock_client.actor.return_value = mock_actor

    with patch("src.collector.apify_client.ApifyClient", return_value=mock_client):
        posts = fetch_posts_apify(handle="agro_example", token="fake-token", months_back=6)

    assert posts[0]["post_type"] == "reel"
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_collector.py -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Criar `src/collector/apify_client.py`**

```python
# src/collector/apify_client.py
from datetime import datetime, timezone, timedelta
from apify_client import ApifyClient


_TYPE_MAP = {
    "Image": "feed",
    "Video": "reel",
    "Sidecar": "carousel",
}


def fetch_posts_apify(handle: str, token: str, months_back: int = 6) -> list[dict]:
    """
    Busca posts de um perfil via Apify Instagram Scraper.
    Retorna lista de dicts normalizados prontos para inserção no banco.
    """
    client = ApifyClient(token)
    cutoff = datetime.now(timezone.utc) - timedelta(days=months_back * 30)

    run = client.actor("apify/instagram-scraper").call(run_input={
        "directUrls": [f"https://www.instagram.com/{handle}/"],
        "resultsType": "posts",
        "resultsLimit": 200,
    })
    run.wait_for_finish()
    dataset = run.default_dataset()

    posts = []
    for item in dataset.iterate_items():
        published_at = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
        if published_at < cutoff:
            continue
        posts.append({
            "instagram_id": item["id"],
            "image_url": item.get("displayUrl", ""),
            "caption": item.get("caption", ""),
            "hashtags": item.get("hashtags", []),
            "likes": item.get("likesCount", 0),
            "comments": item.get("commentsCount", 0),
            "post_type": _TYPE_MAP.get(item.get("type", ""), "feed"),
            "published_at": published_at,
        })

    return posts
```

- [ ] **Step 4: Rodar testes**

```bash
pytest tests/test_collector.py -v
```
Expected: PASS (2 testes)

- [ ] **Step 5: Commit**

```bash
git add src/collector/__init__.py src/collector/apify_client.py tests/test_collector.py
git commit -m "feat: apify collector with post normalization"
```

---

## Task 6: Instaloader Fallback

**Files:**
- Create: `src/collector/instaloader_client.py`
- Modify: `tests/test_collector.py`

- [ ] **Step 1: Adicionar teste de fallback**

Adicionar ao final de `tests/test_collector.py`:

```python
from src.collector.instaloader_client import fetch_posts_instaloader


def test_fetch_posts_instaloader_returns_normalized_posts():
    mock_post = MagicMock()
    mock_post.shortcode = "SC001"
    mock_post.url = "https://example.com/img.jpg"
    mock_post.caption = "Plantio direto"
    mock_post.caption_hashtags = ["plantio", "agro"]
    mock_post.likes = 300
    mock_post.comments = 20
    mock_post.is_video = False
    mock_post.typename = "GraphImage"
    mock_post.date_utc = datetime(2026, 4, 10, tzinfo=timezone.utc)

    mock_profile = MagicMock()
    mock_profile.get_posts.return_value = [mock_post]

    with patch("src.collector.instaloader_client.instaloader.Profile.from_username", return_value=mock_profile):
        with patch("src.collector.instaloader_client.instaloader.Instaloader"):
            posts = fetch_posts_instaloader(handle="agro_example", months_back=6)

    assert len(posts) == 1
    assert posts[0]["instagram_id"] == "SC001"
    assert posts[0]["post_type"] == "feed"
    assert posts[0]["likes"] == 300
```

- [ ] **Step 2: Rodar teste para confirmar falha**

```bash
pytest tests/test_collector.py::test_fetch_posts_instaloader_returns_normalized_posts -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Criar `src/collector/instaloader_client.py`**

```python
# src/collector/instaloader_client.py
from datetime import datetime, timezone, timedelta
import instaloader


_TYPE_MAP = {
    "GraphImage": "feed",
    "GraphVideo": "reel",
    "GraphSidecar": "carousel",
}


def fetch_posts_instaloader(handle: str, months_back: int = 6) -> list[dict]:
    """
    Fallback: busca posts via Instaloader (sem token, mas mais lento e com risco de bloqueio).
    Retorna lista de dicts normalizados.
    """
    loader = instaloader.Instaloader()
    profile = instaloader.Profile.from_username(loader.context, handle)
    cutoff = datetime.now(timezone.utc) - timedelta(days=months_back * 30)

    posts = []
    for post in profile.get_posts():
        published_at = post.date_utc.replace(tzinfo=timezone.utc)
        if published_at < cutoff:
            break
        posts.append({
            "instagram_id": post.shortcode,
            "image_url": post.url,
            "caption": post.caption or "",
            "hashtags": list(post.caption_hashtags),
            "likes": post.likes,
            "comments": post.comments,
            "post_type": _TYPE_MAP.get(post.typename, "feed"),
            "published_at": published_at,
        })

    return posts
```

- [ ] **Step 4: Rodar todos os testes do collector**

```bash
pytest tests/test_collector.py -v
```
Expected: PASS (3 testes)

- [ ] **Step 5: Commit**

```bash
git add src/collector/instaloader_client.py tests/test_collector.py
git commit -m "feat: instaloader fallback collector"
```

---

## Task 7: Collector Orchestrator

**Files:**
- Create: `src/collector/collector.py`
- Modify: `tests/test_collector.py`

- [ ] **Step 1: Adicionar teste do orchestrator**

Adicionar ao final de `tests/test_collector.py`:

```python
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, Profile, Post
from src.collector.collector import collect_profile


@pytest.fixture
def db_session():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        yield s


def test_collect_profile_saves_new_posts(db_session):
    profile = Profile(handle="agro_test", type="competitor", niche="agro", follower_count=5000)
    db_session.add(profile)
    db_session.commit()

    fake_posts = [{
        "instagram_id": "NEW001",
        "image_url": "https://example.com/img.jpg",
        "caption": "Novo post",
        "hashtags": ["agro"],
        "likes": 100,
        "comments": 5,
        "post_type": "feed",
        "published_at": datetime(2026, 4, 10, tzinfo=timezone.utc),
    }]

    with patch("src.collector.collector.fetch_posts_apify", return_value=fake_posts):
        collect_profile(profile=profile, session=db_session, apify_token="tok", months_back=6)

    posts = db_session.query(Post).filter_by(profile_id=profile.id).all()
    assert len(posts) == 1
    assert posts[0].instagram_id == "NEW001"


def test_collect_profile_skips_existing_posts(db_session):
    profile = Profile(handle="agro_test2", type="competitor", niche="agro", follower_count=5000)
    db_session.add(profile)
    db_session.flush()

    existing = Post(
        profile_id=profile.id, instagram_id="EXIST001",
        image_url="u", caption="c", hashtags=[], likes=10, comments=1,
        post_type="feed", published_at=datetime(2026, 4, 9, tzinfo=timezone.utc)
    )
    db_session.add(existing)
    db_session.commit()

    fake_posts = [{
        "instagram_id": "EXIST001",
        "image_url": "https://example.com/img.jpg",
        "caption": "Duplicado",
        "hashtags": [],
        "likes": 200,
        "comments": 10,
        "post_type": "feed",
        "published_at": datetime(2026, 4, 9, tzinfo=timezone.utc),
    }]

    with patch("src.collector.collector.fetch_posts_apify", return_value=fake_posts):
        collect_profile(profile=profile, session=db_session, apify_token="tok", months_back=6)

    posts = db_session.query(Post).filter_by(profile_id=profile.id).all()
    assert len(posts) == 1  # não duplicou
```

- [ ] **Step 2: Rodar testes para confirmar falha**

```bash
pytest tests/test_collector.py::test_collect_profile_saves_new_posts -v
```
Expected: FAIL

- [ ] **Step 3: Criar `src/collector/collector.py`**

```python
# src/collector/collector.py
from sqlalchemy.orm import Session
from src.models import Profile, Post
from src.collector.apify_client import fetch_posts_apify
from src.collector.instaloader_client import fetch_posts_instaloader


def collect_profile(profile: Profile, session: Session, apify_token: str, months_back: int = 6) -> int:
    """
    Coleta posts novos de um perfil. Tenta Apify primeiro, cai para Instaloader em caso de falha.
    Retorna número de novos posts salvos.
    """
    try:
        raw_posts = fetch_posts_apify(handle=profile.handle, token=apify_token, months_back=months_back)
    except Exception:
        raw_posts = fetch_posts_instaloader(handle=profile.handle, months_back=months_back)

    existing_ids = {
        row[0] for row in session.query(Post.instagram_id).filter_by(profile_id=profile.id).all()
    }

    new_posts = []
    for raw in raw_posts:
        if raw["instagram_id"] in existing_ids:
            continue
        new_posts.append(Post(
            profile_id=profile.id,
            instagram_id=raw["instagram_id"],
            image_url=raw["image_url"],
            caption=raw["caption"],
            hashtags=raw["hashtags"],
            likes=raw["likes"],
            comments=raw["comments"],
            post_type=raw["post_type"],
            published_at=raw["published_at"],
        ))

    session.add_all(new_posts)
    session.commit()
    return len(new_posts)
```

- [ ] **Step 4: Rodar todos os testes**

```bash
pytest tests/test_collector.py -v
```
Expected: PASS (5 testes)

- [ ] **Step 5: Commit**

```bash
git add src/collector/collector.py tests/test_collector.py
git commit -m "feat: collector orchestrator with deduplication"
```

---

## Task 8: Image Analyzer (GPT-4o Vision)

**Files:**
- Create: `src/analyzer/image_analyzer.py`
- Create: `tests/test_image_analyzer.py`

- [ ] **Step 1: Escrever testes com mock da OpenAI**

Arquivo: `tests/test_image_analyzer.py`

```python
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, Profile, Post, PostAnalysis
from src.analyzer.image_analyzer import analyze_post


@pytest.fixture
def session_with_post():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        profile = Profile(handle="agro_h", type="competitor", niche="agro", follower_count=10000)
        s.add(profile)
        s.flush()
        post = Post(
            profile_id=profile.id,
            instagram_id="IG999",
            image_url="https://example.com/img.jpg",
            caption="Colheita da soja bateu recorde!",
            hashtags=["soja", "agro"],
            likes=800,
            comments=40,
            post_type="feed",
            published_at=datetime(2026, 4, 10, tzinfo=timezone.utc),
        )
        s.add(post)
        s.commit()
        yield s, profile, post


MOCK_GPT_RESPONSE = {
    "visual_theme": "campo",
    "visual_format": "foto real",
    "emotional_tone": "inspirador",
    "trigger": "resultado",
    "summary": "Imagem de colheita de soja com linguagem de conquista.",
}


def test_analyze_post_creates_analysis(session_with_post):
    session, profile, post = session_with_post

    mock_choice = MagicMock()
    mock_choice.message.content = str(MOCK_GPT_RESPONSE).replace("'", '"')

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    import json
    mock_choice.message.content = json.dumps(MOCK_GPT_RESPONSE)

    with patch("src.analyzer.image_analyzer.openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        analysis = analyze_post(post=post, session=session)

    assert analysis.visual_theme == "campo"
    assert analysis.visual_format == "foto real"
    assert analysis.emotional_tone == "inspirador"
    assert analysis.trigger == "resultado"
    assert analysis.virality_score == pytest.approx(0.088, abs=0.001)
    saved = session.query(PostAnalysis).filter_by(post_id=post.id).first()
    assert saved is not None


def test_analyze_post_skips_already_analyzed(session_with_post):
    session, profile, post = session_with_post

    existing = PostAnalysis(
        post_id=post.id,
        visual_theme="maquinário",
        visual_format="foto real",
        emotional_tone="técnico",
        trigger="autoridade",
        virality_score=0.05,
        raw_analysis={},
    )
    session.add(existing)
    session.commit()

    with patch("src.analyzer.image_analyzer.openai_client") as mock_client:
        result = analyze_post(post=post, session=session)
        mock_client.chat.completions.create.assert_not_called()

    assert result.id == existing.id
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_image_analyzer.py -v
```
Expected: FAIL

- [ ] **Step 3: Criar `src/analyzer/image_analyzer.py`**

```python
# src/analyzer/image_analyzer.py
import json
from openai import OpenAI
from sqlalchemy.orm import Session
from src.config import OPENAI_API_KEY
from src.models import Post, PostAnalysis
from src.analyzer.virality import calculate_virality_score

openai_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """Você é um especialista em marketing digital para agronegócio brasileiro.
Analise a imagem e legenda do post e retorne um JSON com exatamente estes campos:
{
  "visual_theme": "<maquinário|insumo|campo|pessoa|dado|outro>",
  "visual_format": "<infográfico|foto real|montagem|outro>",
  "emotional_tone": "<inspirador|técnico|humorístico|urgente|educativo|outro>",
  "trigger": "<autoridade|escassez|pertencimento|resultado|outro>",
  "summary": "<resumo em 1 frase do que torna este post relevante para o público do agro>"
}
Responda APENAS com o JSON, sem markdown."""


def analyze_post(post: Post, session: Session) -> PostAnalysis:
    """
    Analisa um post com GPT-4o Vision. Se já analisado, retorna análise existente.
    """
    existing = session.query(PostAnalysis).filter_by(post_id=post.id).first()
    if existing:
        return existing

    follower_count = post.profile.follower_count or 1

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": post.image_url},
                    },
                    {
                        "type": "text",
                        "text": f"Legenda: {post.caption}\nHashtags: {', '.join(post.hashtags)}",
                    },
                ],
            },
        ],
        max_tokens=300,
    )

    raw = json.loads(response.choices[0].message.content)
    score = calculate_virality_score(
        likes=post.likes,
        comments=post.comments,
        follower_count=follower_count,
    )

    analysis = PostAnalysis(
        post_id=post.id,
        visual_theme=raw.get("visual_theme"),
        visual_format=raw.get("visual_format"),
        emotional_tone=raw.get("emotional_tone"),
        trigger=raw.get("trigger"),
        virality_score=score,
        raw_analysis=raw,
    )
    session.add(analysis)
    session.commit()
    return analysis
```

- [ ] **Step 4: Rodar testes**

```bash
pytest tests/test_image_analyzer.py -v
```
Expected: PASS (2 testes)

- [ ] **Step 5: Commit**

```bash
git add src/analyzer/image_analyzer.py tests/test_image_analyzer.py
git commit -m "feat: gpt-4o vision image analyzer with virality score"
```

---

## Task 9: Weekly Report Generator

**Files:**
- Create: `src/reporter/__init__.py`
- Create: `src/reporter/weekly_report.py`
- Create: `tests/test_weekly_report.py`

- [ ] **Step 1: Escrever testes**

Arquivo: `tests/test_weekly_report.py`

```python
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, Profile, Post, PostAnalysis, WeeklyReport
from src.reporter.weekly_report import generate_weekly_report


@pytest.fixture
def session_with_analyses():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        profile = Profile(handle="concorrente1", type="competitor", niche="agro", follower_count=8000)
        s.add(profile)
        s.flush()
        for i in range(3):
            post = Post(
                profile_id=profile.id,
                instagram_id=f"IG{i}",
                image_url=f"https://example.com/{i}.jpg",
                caption=f"Post {i}",
                hashtags=["agro"],
                likes=500 + i * 100,
                comments=20 + i,
                post_type="feed",
                published_at=datetime(2026, 4, 10 + i, tzinfo=timezone.utc),
            )
            s.add(post)
            s.flush()
            analysis = PostAnalysis(
                post_id=post.id,
                visual_theme="campo",
                visual_format="foto real",
                emotional_tone="inspirador",
                trigger="resultado",
                virality_score=0.07 + i * 0.01,
                raw_analysis={"summary": f"Post {i} resumo"},
            )
            s.add(analysis)
        s.commit()
        yield s


MOCK_REPORT_RESPONSE = {
    "top_formats": {"foto real": 3},
    "top_themes": {"campo": 3},
    "language_patterns": {"tom": "inspirador"},
    "top_hashtags": ["agro"],
    "viral_posts": [],
    "report_text": "# Relatório Semanal\nForma mais viral: foto real com tema campo.",
}


def test_generate_weekly_report_creates_report(session_with_analyses):
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(MOCK_REPORT_RESPONSE)
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    period_start = datetime(2026, 4, 7, tzinfo=timezone.utc)
    period_end = datetime(2026, 4, 13, tzinfo=timezone.utc)

    with patch("src.reporter.weekly_report.openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        report = generate_weekly_report(
            session=session_with_analyses,
            period_start=period_start,
            period_end=period_end,
        )

    assert report.id is not None
    assert report.top_formats == {"foto real": 3}
    assert "Relatório" in report.report_text
    saved = session_with_analyses.query(WeeklyReport).first()
    assert saved is not None
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_weekly_report.py -v
```
Expected: FAIL

- [ ] **Step 3: Criar `src/reporter/weekly_report.py`**

```python
# src/reporter/weekly_report.py
import json
from datetime import datetime
from openai import OpenAI
from sqlalchemy.orm import Session
from src.config import OPENAI_API_KEY
from src.models import Post, PostAnalysis, WeeklyReport

openai_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """Você é um estrategista de conteúdo para agronegócio.
Com base nas análises de posts dos concorrentes, gere um relatório semanal em JSON com:
{
  "top_formats": {"<formato>": <contagem>},
  "top_themes": {"<tema>": <contagem>},
  "language_patterns": {"<padrão>": "<descrição>"},
  "top_hashtags": ["<hashtag>"],
  "viral_posts": [<post_ids com maior virality_score>],
  "report_text": "<relatório completo em markdown com insights acionáveis>"
}
Responda APENAS com o JSON."""


def generate_weekly_report(session: Session, period_start: datetime, period_end: datetime) -> WeeklyReport:
    """Consolida análises da semana em um relatório via GPT-4o."""
    analyses = (
        session.query(PostAnalysis)
        .join(Post)
        .filter(Post.published_at >= period_start, Post.published_at <= period_end)
        .all()
    )

    summaries = [
        {
            "post_id": a.post_id,
            "visual_theme": a.visual_theme,
            "visual_format": a.visual_format,
            "emotional_tone": a.emotional_tone,
            "trigger": a.trigger,
            "virality_score": a.virality_score,
            "summary": a.raw_analysis.get("summary", ""),
        }
        for a in analyses
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Análises da semana:\n{json.dumps(summaries, ensure_ascii=False)}"},
        ],
        max_tokens=1500,
    )

    raw = json.loads(response.choices[0].message.content)
    report = WeeklyReport(
        period_start=period_start,
        period_end=period_end,
        top_formats=raw.get("top_formats", {}),
        top_themes=raw.get("top_themes", {}),
        language_patterns=raw.get("language_patterns", {}),
        top_hashtags=raw.get("top_hashtags", []),
        viral_posts=raw.get("viral_posts", []),
        report_text=raw.get("report_text", ""),
    )
    session.add(report)
    session.commit()
    return report
```

- [ ] **Step 4: Rodar testes**

```bash
pytest tests/test_weekly_report.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/reporter/__init__.py src/reporter/weekly_report.py tests/test_weekly_report.py
git commit -m "feat: weekly report generator with gpt-4o"
```

---

## Task 10: Voice Profiler

**Files:**
- Create: `src/reporter/voice_profiler.py`
- Create: `tests/test_voice_profiler.py`

- [ ] **Step 1: Escrever testes**

Arquivo: `tests/test_voice_profiler.py`

```python
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, Profile, Post, ProfileVoice
from src.reporter.voice_profiler import generate_voice_profile


@pytest.fixture
def session_with_own_profile():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        profile = Profile(handle="meu_perfil", type="own", niche="agro", follower_count=3000)
        s.add(profile)
        s.flush()
        for i in range(3):
            post = Post(
                profile_id=profile.id,
                instagram_id=f"OWN{i}",
                image_url=f"https://example.com/{i}.jpg",
                caption=f"Nossa fazenda produz {i+1} toneladas por hectare",
                hashtags=["agro", "produtividade"],
                likes=300,
                comments=15,
                post_type="feed",
                published_at=datetime(2026, 4, 10, tzinfo=timezone.utc),
            )
            s.add(post)
        s.commit()
        yield s, profile


MOCK_VOICE = {
    "vocabulary": {"palavras_frequentes": ["fazenda", "toneladas", "produtividade"]},
    "tone": "técnico e acessível",
    "dominant_themes": ["produção", "resultados"],
    "competitor_comparison": {"diferencial": "foco em números concretos"},
}


def test_generate_voice_profile_creates_profile(session_with_own_profile):
    session, profile = session_with_own_profile
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(MOCK_VOICE)
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("src.reporter.voice_profiler.openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        voice = generate_voice_profile(profile=profile, session=session)

    assert voice.tone == "técnico e acessível"
    assert "produção" in voice.dominant_themes
    saved = session.query(ProfileVoice).filter_by(profile_id=profile.id).first()
    assert saved is not None
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_voice_profiler.py -v
```
Expected: FAIL

- [ ] **Step 3: Criar `src/reporter/voice_profiler.py`**

```python
# src/reporter/voice_profiler.py
import json
from openai import OpenAI
from sqlalchemy.orm import Session
from src.config import OPENAI_API_KEY
from src.models import Profile, Post, ProfileVoice

openai_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """Você é um especialista em branding e linguagem para agronegócio.
Analise as legendas dos posts abaixo e retorne um JSON com o perfil de voz do perfil:
{
  "vocabulary": {"palavras_frequentes": ["<palavra>"]},
  "tone": "<descrição do tom predominante>",
  "dominant_themes": ["<tema>"],
  "competitor_comparison": {"<insight>": "<descrição>"}
}
Responda APENAS com o JSON."""


def generate_voice_profile(profile: Profile, session: Session) -> ProfileVoice:
    """Analisa os posts do perfil próprio e gera um perfil de voz atualizado."""
    posts = session.query(Post).filter_by(profile_id=profile.id).order_by(Post.published_at.desc()).limit(50).all()
    captions = [{"caption": p.caption, "hashtags": p.hashtags} for p in posts]

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Posts do perfil @{profile.handle}:\n{json.dumps(captions, ensure_ascii=False)}"},
        ],
        max_tokens=800,
    )

    raw = json.loads(response.choices[0].message.content)
    voice = ProfileVoice(
        profile_id=profile.id,
        vocabulary=raw.get("vocabulary", {}),
        tone=raw.get("tone", ""),
        dominant_themes=raw.get("dominant_themes", []),
        competitor_comparison=raw.get("competitor_comparison", {}),
    )
    session.add(voice)
    session.commit()
    return voice
```

- [ ] **Step 4: Rodar testes**

```bash
pytest tests/test_voice_profiler.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/reporter/voice_profiler.py tests/test_voice_profiler.py
git commit -m "feat: voice profiler for own instagram profile"
```

---

## Task 11: Carousel Generator

**Files:**
- Create: `src/carousel/__init__.py`
- Create: `src/carousel/generator.py`
- Create: `tests/test_carousel_generator.py`

- [ ] **Step 1: Escrever testes**

Arquivo: `tests/test_carousel_generator.py`

```python
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, Profile, WeeklyReport, ProfileVoice, Carousel
from src.carousel.generator import generate_carousel


@pytest.fixture
def session_with_context():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        profile = Profile(handle="meu_perfil", type="own", niche="agro", follower_count=3000)
        s.add(profile)
        s.flush()

        voice = ProfileVoice(
            profile_id=profile.id,
            vocabulary={"palavras_frequentes": ["fazenda", "produtividade"]},
            tone="técnico e acessível",
            dominant_themes=["produção"],
            competitor_comparison={},
        )
        report = WeeklyReport(
            period_start=datetime(2026, 4, 7, tzinfo=timezone.utc),
            period_end=datetime(2026, 4, 13, tzinfo=timezone.utc),
            top_formats={"foto real": 5},
            top_themes={"campo": 4},
            language_patterns={"tom": "inspirador"},
            top_hashtags=["agro"],
            viral_posts=[],
            report_text="# Relatório\nFoto real com tema campo converte mais.",
        )
        s.add(voice)
        s.add(report)
        s.commit()
        yield s, profile, voice, report


MOCK_SLIDES = [
    {"slide_number": 1, "title": "Você sabia?", "copy": "A soja brasileira...", "cta": ""},
    {"slide_number": 2, "title": "O problema", "copy": "Muitos produtores...", "cta": ""},
    {"slide_number": 3, "title": "A solução", "copy": "Com manejo correto...", "cta": ""},
    {"slide_number": 4, "title": "Resultado", "copy": "Até 30% mais produtividade", "cta": "Salve este post!"},
]


def test_generate_carousel_returns_slides(session_with_context):
    session, profile, voice, report = session_with_context
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(MOCK_SLIDES)
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("src.carousel.generator.openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        carousel = generate_carousel(
            theme="Manejo de soja para alta produtividade",
            session=session,
        )

    assert len(carousel.slides) == 4
    assert carousel.slides[0]["title"] == "Você sabia?"
    assert carousel.slides[-1]["cta"] == "Salve este post!"
    saved = session.query(Carousel).first()
    assert saved is not None
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_carousel_generator.py -v
```
Expected: FAIL

- [ ] **Step 3: Criar `src/carousel/generator.py`**

```python
# src/carousel/generator.py
import json
from openai import OpenAI
from sqlalchemy.orm import Session
from src.config import OPENAI_API_KEY
from src.models import ProfileVoice, WeeklyReport, Carousel

openai_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """Você é um copywriter especialista em carrosséis virais para Instagram no agronegócio brasileiro.
Com base no perfil de voz do criador e nos padrões virais dos concorrentes, crie um carrossel sobre o tema fornecido.
Retorne um JSON com a estrutura de slides:
[
  {"slide_number": 1, "title": "<título impactante>", "copy": "<texto do slide>", "cta": ""},
  ...
  {"slide_number": N, "title": "<título>", "copy": "<texto>", "cta": "<chamada para ação>"}
]
- Entre 4 e 7 slides
- Slide 1: gancho que para o scroll
- Slides intermediários: desenvolvimento do tema com linguagem do criador
- Último slide: CTA claro
Responda APENAS com o JSON."""


def generate_carousel(theme: str, session: Session) -> Carousel:
    """Gera carrossel viral com base no tema, voz própria e último relatório semanal."""
    voice = (
        session.query(ProfileVoice)
        .order_by(ProfileVoice.generated_at.desc())
        .first()
    )
    report = (
        session.query(WeeklyReport)
        .order_by(WeeklyReport.generated_at.desc())
        .first()
    )

    context = {
        "tema": theme,
        "perfil_de_voz": {
            "tom": voice.tone if voice else "neutro",
            "temas_dominantes": voice.dominant_themes if voice else [],
            "vocabulario": voice.vocabulary if voice else {},
        } if voice else {},
        "padroes_virais_concorrentes": {
            "formatos_top": report.top_formats if report else {},
            "temas_top": report.top_themes if report else {},
            "resumo": report.report_text[:500] if report else "",
        } if report else {},
    }

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ],
        max_tokens=1200,
    )

    slides = json.loads(response.choices[0].message.content)
    report_ids = [report.id] if report else []

    carousel = Carousel(theme=theme, slides=slides, based_on_reports=report_ids)
    session.add(carousel)
    session.commit()
    return carousel
```

- [ ] **Step 4: Rodar testes**

```bash
pytest tests/test_carousel_generator.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/carousel/__init__.py src/carousel/generator.py tests/test_carousel_generator.py
git commit -m "feat: carousel generator with voice + competitive intelligence"
```

---

## Task 12: Scheduler

**Files:**
- Create: `src/scheduler.py`

- [ ] **Step 1: Criar `src/scheduler.py`**

Não há lógica de negócio para testar unitariamente aqui — apenas orchestração. Criar o arquivo direto.

```python
# src/scheduler.py
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy.orm import Session
from src.config import APIFY_API_TOKEN
from src.database import SessionLocal
from src.models import Profile
from src.collector.collector import collect_profile
from src.analyzer.image_analyzer import analyze_post
from src.reporter.weekly_report import generate_weekly_report
from src.reporter.voice_profiler import generate_voice_profile
from src.models import Post, PostAnalysis

scheduler = BlockingScheduler(timezone="America/Sao_Paulo")


def run_daily_collection():
    """Roda às 06h00: coleta posts novos de todos os perfis ativos e analisa imagens."""
    print(f"[{datetime.now()}] Iniciando coleta diária...")
    session: Session = SessionLocal()
    try:
        profiles = session.query(Profile).filter_by(active=True).all()
        for profile in profiles:
            months = 6 if _is_first_run(profile, session) else 0
            new_count = collect_profile(profile=profile, session=session, apify_token=APIFY_API_TOKEN, months_back=months or 1)
            print(f"  @{profile.handle}: {new_count} novos posts")

        # Analisa posts sem análise
        unanalyzed = (
            session.query(Post)
            .outerjoin(PostAnalysis)
            .filter(PostAnalysis.id.is_(None))
            .all()
        )
        for post in unanalyzed:
            analyze_post(post=post, session=session)
            print(f"  Analisado: post {post.instagram_id}")
    finally:
        session.close()
    print(f"[{datetime.now()}] Coleta diária concluída.")


def run_weekly_tasks():
    """Roda todo domingo às 08h00: gera relatório semanal e atualiza perfil de voz."""
    print(f"[{datetime.now()}] Iniciando tarefas semanais...")
    session: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        period_end = now
        period_start = now - timedelta(days=7)
        report = generate_weekly_report(session=session, period_start=period_start, period_end=period_end)
        print(f"  Relatório gerado: id={report.id}")

        own_profile = session.query(Profile).filter_by(type="own", active=True).first()
        if own_profile:
            voice = generate_voice_profile(profile=own_profile, session=session)
            print(f"  Perfil de voz atualizado: id={voice.id}")
    finally:
        session.close()
    print(f"[{datetime.now()}] Tarefas semanais concluídas.")


def _is_first_run(profile: Profile, session: Session) -> bool:
    return session.query(Post).filter_by(profile_id=profile.id).count() == 0


scheduler.add_job(run_daily_collection, "cron", hour=6, minute=0)
scheduler.add_job(run_weekly_tasks, "cron", day_of_week="sun", hour=8, minute=0)


if __name__ == "__main__":
    print("Scheduler iniciado. Ctrl+C para parar.")
    scheduler.start()
```

- [ ] **Step 2: Commit**

```bash
git add src/scheduler.py
git commit -m "feat: apscheduler for daily collection and weekly reporting"
```

---

## Task 13: Dashboard — App Shell e Accordion Tabs

**Files:**
- Create: `dashboard/__init__.py`
- Create: `dashboard/app.py`
- Create: `dashboard/tabs/__init__.py`

- [ ] **Step 1: Criar `dashboard/app.py`**

```python
# dashboard/app.py
import streamlit as st
from dashboard.tabs import competitors, posts, reports, voice, carousel

st.set_page_config(page_title="Agro Intel", layout="wide")
st.title("Agro Intel — Inteligência Competitiva Instagram")

TABS = {
    "concorrentes": "📊 Concorrentes",
    "posts": "🖼️ Posts",
    "relatorios": "📋 Relatório Semanal",
    "voz": "🎙️ Meu Perfil de Voz",
    "carrossel": "✨ Gerador de Carrossel",
}

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "concorrentes"

cols = st.columns(len(TABS))
for col, (key, label) in zip(cols, TABS.items()):
    if col.button(label, use_container_width=True):
        st.session_state.active_tab = key

st.divider()

active = st.session_state.active_tab
if active == "concorrentes":
    competitors.render()
elif active == "posts":
    posts.render()
elif active == "relatorios":
    reports.render()
elif active == "voz":
    voice.render()
elif active == "carrossel":
    carousel.render()
```

- [ ] **Step 2: Criar `dashboard/tabs/__init__.py`** (vazio)

- [ ] **Step 3: Commit**

```bash
git add dashboard/__init__.py dashboard/app.py dashboard/tabs/__init__.py
git commit -m "feat: streamlit app shell with accordion tab navigation"
```

---

## Task 14: Tab 1 — Concorrentes

**Files:**
- Create: `dashboard/tabs/competitors.py`

- [ ] **Step 1: Criar `dashboard/tabs/competitors.py`**

```python
# dashboard/tabs/competitors.py
import streamlit as st
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models import Profile, Post


def render():
    st.subheader("Perfis Monitorados")
    session: Session = SessionLocal()

    try:
        profiles = session.query(Profile).filter_by(active=True).order_by(Profile.handle).all()

        if profiles:
            for profile in profiles:
                post_count = session.query(Post).filter_by(profile_id=profile.id).count()
                last_post = session.query(Post).filter_by(profile_id=profile.id).order_by(Post.collected_at.desc()).first()
                last_sync = last_post.collected_at.strftime("%d/%m/%Y %H:%M") if last_post else "Nunca"

                col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
                col1.write(f"**@{profile.handle}**")
                col2.write(f"{'Meu perfil' if profile.type == 'own' else 'Concorrente'}")
                col3.write(f"{post_count} posts · Último sync: {last_sync}")
                if col4.button("Remover", key=f"remove_{profile.id}"):
                    profile.active = False
                    session.commit()
                    st.rerun()
        else:
            st.info("Nenhum perfil cadastrado ainda.")

        st.divider()
        st.subheader("Adicionar Perfil")
        with st.form("add_profile_form"):
            handle = st.text_input("Username do Instagram (sem @)")
            profile_type = st.selectbox("Tipo", ["competitor", "own"], format_func=lambda x: "Concorrente" if x == "competitor" else "Meu perfil")
            submitted = st.form_submit_button("Adicionar")
            if submitted and handle:
                existing = session.query(Profile).filter_by(handle=handle).first()
                if existing:
                    existing.active = True
                    session.commit()
                    st.success(f"@{handle} reativado.")
                else:
                    session.add(Profile(handle=handle.strip().lstrip("@"), type=profile_type, niche="agronegócio"))
                    session.commit()
                    st.success(f"@{handle} adicionado com sucesso.")
                st.rerun()
    finally:
        session.close()
```

- [ ] **Step 2: Commit**

```bash
git add dashboard/tabs/competitors.py
git commit -m "feat: competitors tab with add/remove profile"
```

---

## Task 15: Tab 2 — Posts

**Files:**
- Create: `dashboard/components/__init__.py`
- Create: `dashboard/components/post_card.py`
- Create: `dashboard/tabs/posts.py`

- [ ] **Step 1: Criar `dashboard/components/post_card.py`**

```python
# dashboard/components/post_card.py
import streamlit as st
from src.models import Post


def render_post_card(post: Post):
    with st.container(border=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(post.image_url, use_container_width=True)
        with col2:
            st.write(f"**@{post.profile.handle}** · {post.post_type.upper()} · {post.published_at.strftime('%d/%m/%Y')}")
            st.write(f"❤️ {post.likes}  💬 {post.comments}")
            if post.caption:
                st.caption(post.caption[:200] + ("..." if len(post.caption) > 200 else ""))
            if post.analysis:
                with st.expander("Ver análise"):
                    st.write(f"**Tema:** {post.analysis.visual_theme}")
                    st.write(f"**Formato:** {post.analysis.visual_format}")
                    st.write(f"**Tom:** {post.analysis.emotional_tone}")
                    st.write(f"**Gatilho:** {post.analysis.trigger}")
                    st.write(f"**Score de viralidade:** {post.analysis.virality_score:.2%}")
```

- [ ] **Step 2: Criar `dashboard/tabs/posts.py`**

```python
# dashboard/tabs/posts.py
import streamlit as st
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session, joinedload
from src.database import SessionLocal
from src.models import Profile, Post, PostAnalysis
from dashboard.components.post_card import render_post_card


def render():
    st.subheader("Feed de Posts")
    session: Session = SessionLocal()

    try:
        profiles = session.query(Profile).filter_by(active=True).all()
        profile_options = {"Todos": None} | {f"@{p.handle}": p.id for p in profiles}

        col1, col2, col3, col4 = st.columns(4)
        selected_profile = col1.selectbox("Perfil", list(profile_options.keys()))
        period = col2.selectbox("Período", ["Últimos 7 dias", "Últimos 30 dias", "Últimos 6 meses"])
        post_type = col3.selectbox("Tipo", ["Todos", "feed", "reel", "carousel"])
        min_score = col4.slider("Score mínimo de viralidade", 0.0, 1.0, 0.0, step=0.01)

        period_map = {"Últimos 7 dias": 7, "Últimos 30 dias": 30, "Últimos 6 meses": 180}
        cutoff = datetime.now(timezone.utc) - timedelta(days=period_map[period])

        query = (
            session.query(Post)
            .options(joinedload(Post.profile), joinedload(Post.analysis))
            .filter(Post.published_at >= cutoff)
        )
        if profile_options[selected_profile]:
            query = query.filter(Post.profile_id == profile_options[selected_profile])
        if post_type != "Todos":
            query = query.filter(Post.post_type == post_type)
        if min_score > 0:
            query = query.join(PostAnalysis).filter(PostAnalysis.virality_score >= min_score)

        all_posts = query.order_by(Post.published_at.desc()).limit(50).all()

        st.write(f"{len(all_posts)} posts encontrados")
        for post in all_posts:
            render_post_card(post)
    finally:
        session.close()
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/components/__init__.py dashboard/components/post_card.py dashboard/tabs/posts.py
git commit -m "feat: posts tab with filters and post card component"
```

---

## Task 16: Tab 3 — Relatório Semanal

**Files:**
- Create: `dashboard/tabs/reports.py`

- [ ] **Step 1: Criar `dashboard/tabs/reports.py`**

```python
# dashboard/tabs/reports.py
import streamlit as st
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models import WeeklyReport


def render():
    st.subheader("Relatório Semanal")
    session: Session = SessionLocal()

    try:
        reports = session.query(WeeklyReport).order_by(WeeklyReport.period_start.desc()).all()

        if not reports:
            st.info("Nenhum relatório gerado ainda. O primeiro relatório é criado todo domingo às 08h.")
            return

        report_options = {
            f"{r.period_start.strftime('%d/%m/%Y')} – {r.period_end.strftime('%d/%m/%Y')}": r
            for r in reports
        }
        selected_label = st.selectbox("Selecionar semana", list(report_options.keys()))
        report: WeeklyReport = report_options[selected_label]

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Formatos mais virais**")
            for fmt, count in (report.top_formats or {}).items():
                st.write(f"- {fmt}: {count} posts")

            st.write("**Temas em alta**")
            for theme, count in (report.top_themes or {}).items():
                st.write(f"- {theme}: {count} posts")

        with col2:
            st.write("**Hashtags recorrentes**")
            st.write(", ".join(f"#{h}" for h in (report.top_hashtags or [])))

            st.write("**Padrões de linguagem**")
            for k, v in (report.language_patterns or {}).items():
                st.write(f"- {k}: {v}")

        st.divider()
        st.write("**Relatório completo**")
        st.markdown(report.report_text or "_Sem texto disponível._")
    finally:
        session.close()
```

- [ ] **Step 2: Commit**

```bash
git add dashboard/tabs/reports.py
git commit -m "feat: weekly reports tab with period selector"
```

---

## Task 17: Tab 4 — Meu Perfil de Voz

**Files:**
- Create: `dashboard/tabs/voice.py`

- [ ] **Step 1: Criar `dashboard/tabs/voice.py`**

```python
# dashboard/tabs/voice.py
import streamlit as st
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models import Profile, ProfileVoice


def render():
    st.subheader("Meu Perfil de Voz")
    session: Session = SessionLocal()

    try:
        own_profile = session.query(Profile).filter_by(type="own", active=True).first()
        if not own_profile:
            st.warning("Nenhum perfil próprio cadastrado. Adicione seu perfil na aba Concorrentes com o tipo 'Meu perfil'.")
            return

        voice = (
            session.query(ProfileVoice)
            .filter_by(profile_id=own_profile.id)
            .order_by(ProfileVoice.generated_at.desc())
            .first()
        )

        if not voice:
            st.info("Perfil de voz ainda não gerado. Será criado automaticamente no próximo domingo.")
            return

        st.write(f"_Última atualização: {voice.generated_at.strftime('%d/%m/%Y às %H:%M')}_")
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Tom predominante**")
            st.info(voice.tone or "—")

            st.write("**Temas dominantes**")
            for theme in (voice.dominant_themes or []):
                st.write(f"- {theme}")

        with col2:
            st.write("**Vocabulário característico**")
            vocab = voice.vocabulary or {}
            words = vocab.get("palavras_frequentes", [])
            if words:
                st.write(", ".join(words))

            st.write("**Diferencial vs concorrentes**")
            for k, v in (voice.competitor_comparison or {}).items():
                st.write(f"- **{k}:** {v}")
    finally:
        session.close()
```

- [ ] **Step 2: Commit**

```bash
git add dashboard/tabs/voice.py
git commit -m "feat: voice profile tab showing tone, themes and vocabulary"
```

---

## Task 18: Tab 5 — Gerador de Carrossel

**Files:**
- Create: `dashboard/tabs/carousel.py`

- [ ] **Step 1: Criar `dashboard/tabs/carousel.py`**

```python
# dashboard/tabs/carousel.py
import streamlit as st
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models import Carousel
from src.carousel.generator import generate_carousel


def render():
    st.subheader("Gerador de Carrossel")
    session: Session = SessionLocal()

    try:
        with st.form("carousel_form"):
            theme = st.text_area("Qual é o tema ou pauta do carrossel?", placeholder="Ex: 5 técnicas de manejo do solo para aumentar produtividade")
            submitted = st.form_submit_button("✨ Gerar Carrossel")

        if submitted and theme.strip():
            with st.spinner("Gerando carrossel com base nos dados dos concorrentes e na sua voz..."):
                carousel = generate_carousel(theme=theme.strip(), session=session)
            st.success("Carrossel gerado!")
            _render_carousel(carousel)

        st.divider()
        st.subheader("Histórico de Carrosséis")
        past = session.query(Carousel).order_by(Carousel.generated_at.desc()).limit(10).all()
        if not past:
            st.info("Nenhum carrossel gerado ainda.")
        else:
            for c in past:
                with st.expander(f"📱 {c.theme[:60]} — {c.generated_at.strftime('%d/%m/%Y %H:%M')}"):
                    _render_carousel(c)
    finally:
        session.close()


def _render_carousel(carousel: Carousel):
    for slide in carousel.slides:
        with st.container(border=True):
            st.write(f"**Slide {slide['slide_number']}: {slide['title']}**")
            st.write(slide["copy"])
            if slide.get("cta"):
                st.success(f"CTA: {slide['cta']}")
```

- [ ] **Step 2: Commit**

```bash
git add dashboard/tabs/carousel.py
git commit -m "feat: carousel generator tab with history"
```

---

## Task 19: Rodar Testes Finais e Smoke Test

- [ ] **Step 1: Instalar dependências**

```bash
pip install -r requirements.txt
```

- [ ] **Step 2: Rodar todos os testes**

```bash
pytest tests/ -v
```
Expected: todos PASS

- [ ] **Step 3: Criar arquivo `.env` local com credenciais reais**

Copiar `.env.example` para `.env` e preencher:
```
DATABASE_URL=postgresql://user:password@localhost:5432/agro_intel
OPENAI_API_KEY=sk-...
APIFY_API_TOKEN=apify_api_...
```

- [ ] **Step 4: Aplicar migrations**

```bash
alembic upgrade head
```

- [ ] **Step 5: Iniciar o dashboard**

```bash
streamlit run dashboard/app.py
```
Expected: dashboard abre no browser em `http://localhost:8501`

- [ ] **Step 6: Smoke test manual**
  - Adicionar 1 perfil concorrente na Tab 1
  - Adicionar seu próprio perfil (tipo "Meu perfil") na Tab 1
  - Rodar coleta manual no terminal: `python -c "from src.scheduler import run_daily_collection; run_daily_collection()"`
  - Verificar posts aparecendo na Tab 2
  - Gerar um carrossel de teste na Tab 5

- [ ] **Step 7: Commit final**

```bash
git add .
git commit -m "feat: complete instagram competitor intelligence tool v1"
```
