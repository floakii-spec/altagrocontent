# Post Intelligence & Argument Bank Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add professional-grade per-post content intelligence (technical depth, arguments, data, agro knowledge) and a cross-post Argument Bank that feeds content generation — built on top of existing collected posts without touching the existing PostAnalysis layer.

**Architecture:** Two new DB tables (`post_intelligence`, `argument_bank`) fed by a second GPT-4o pass per post (caption-only, no image re-fetch). A daily APScheduler job processes unanalyzed posts. The Argument Bank feeds the Carousel Generator. A new "Análise" group in the orbital tree exposes two drawers: Deep Dive per post and the browsable Argument Bank.

**Tech Stack:** Python/FastAPI/SQLAlchemy 2.0, Alembic, GPT-4o (text only), Next.js 16/React 19, APScheduler 3, pytest

---

## File Structure

```
src/models.py                                    MODIFY — PostIntelligence + ArgumentBank models, Post.intelligence relationship
alembic/versions/005_post_intelligence.py        CREATE — migration for 2 new tables
src/analyzer/post_intelligence.py                CREATE — analyze_post_intelligence()
src/analyzer/argument_extractor.py               CREATE — upsert_arguments()
api/routers/intelligence.py                      CREATE — 4 endpoints
api/main.py                                      MODIFY — _run_daily_intelligence + scheduler job
src/carousel/generator.py                        MODIFY — inject top ArgumentBank entries into prompt
web/lib/tree-data.ts                             MODIFY — add Análise group with 2 children
web/components/drawers/DrawerInteligenciaPosts.tsx     CREATE
web/components/drawers/DrawerInteligenciaArgumentos.tsx CREATE
web/components/drawers/ModuleDrawer.tsx          MODIFY — register 2 new drawers
tests/test_post_intelligence.py                  CREATE
tests/test_argument_extractor.py                 CREATE
tests/test_api_intelligence.py                   CREATE
```

---

## Task 1: Models + Migration

**Files:**
- Modify: `src/models.py`
- Create: `alembic/versions/005_post_intelligence.py`
- Test: `tests/test_models.py` (existing — run to verify nothing broke)

- [ ] **Step 1: Add PostIntelligence and ArgumentBank to `src/models.py`**

Open `src/models.py`. After the `CarouselSuggestion` class (end of file), append both new models. Also add `intelligence` relationship to the existing `Post` class.

In the `Post` class, add this line after the existing `analysis` relationship:
```python
intelligence: Mapped[Optional["PostIntelligence"]] = relationship(back_populates="post", uselist=False)
```

Then append at the end of the file:
```python
class PostIntelligence(Base):
    __tablename__ = "post_intelligence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), unique=True, nullable=False)
    agro_topic_cluster: Mapped[Optional[str]] = mapped_column(String(50))
    agro_segment: Mapped[Optional[str]] = mapped_column(String(50))
    technical_depth: Mapped[Optional[str]] = mapped_column(String(20))
    core_argument: Mapped[Optional[str]] = mapped_column(Text)
    argument_structure: Mapped[Optional[str]] = mapped_column(Text)
    technical_claims: Mapped[list] = mapped_column(JSON, default=list)
    data_points: Mapped[list] = mapped_column(JSON, default=list)
    sources_referenced: Mapped[list] = mapped_column(JSON, default=list)
    knowledge_assumptions: Mapped[Optional[str]] = mapped_column(Text)
    content_gaps: Mapped[Optional[str]] = mapped_column(Text)
    replication_template: Mapped[Optional[str]] = mapped_column(Text)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    post: Mapped["Post"] = relationship(back_populates="intelligence")


class ArgumentBank(Base):
    __tablename__ = "argument_bank"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    topic_cluster: Mapped[Optional[str]] = mapped_column(String(50))
    agro_segment: Mapped[Optional[str]] = mapped_column(String(50))
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    virality_weight: Mapped[float] = mapped_column(Float, default=0.0)
    source_post_ids: Mapped[list] = mapped_column(JSON, default=list)
    times_seen: Mapped[int] = mapped_column(Integer, default=1)
    origin: Mapped[str] = mapped_column(String(20), default="extracted")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 2: Run existing model tests to confirm no regressions**

```bash
pytest tests/test_models.py -v
```
Expected: all existing tests PASS.

- [ ] **Step 3: Create migration `alembic/versions/005_post_intelligence.py`**

```python
"""post_intelligence and argument_bank tables

Revision ID: 005
Revises: 004
Create Date: 2026-04-17 00:00:00.000000

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "post_intelligence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("posts.id"), unique=True, nullable=False),
        sa.Column("agro_topic_cluster", sa.String(50), nullable=True),
        sa.Column("agro_segment", sa.String(50), nullable=True),
        sa.Column("technical_depth", sa.String(20), nullable=True),
        sa.Column("core_argument", sa.Text(), nullable=True),
        sa.Column("argument_structure", sa.Text(), nullable=True),
        sa.Column("technical_claims", sa.JSON(), nullable=False),
        sa.Column("data_points", sa.JSON(), nullable=False),
        sa.Column("sources_referenced", sa.JSON(), nullable=False),
        sa.Column("knowledge_assumptions", sa.Text(), nullable=True),
        sa.Column("content_gaps", sa.Text(), nullable=True),
        sa.Column("replication_template", sa.Text(), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "argument_bank",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("topic_cluster", sa.String(50), nullable=True),
        sa.Column("agro_segment", sa.String(50), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("virality_weight", sa.Float(), nullable=False),
        sa.Column("source_post_ids", sa.JSON(), nullable=False),
        sa.Column("times_seen", sa.Integer(), nullable=False),
        sa.Column("origin", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("argument_bank")
    op.drop_table("post_intelligence")
```

- [ ] **Step 4: Commit**

```bash
git add src/models.py alembic/versions/005_post_intelligence.py
git commit -m "feat: PostIntelligence and ArgumentBank models + migration 005"
```

---

## Task 2: PostIntelligence Analyzer

**Files:**
- Create: `src/analyzer/post_intelligence.py`
- Create: `tests/test_post_intelligence.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_post_intelligence.py`:

```python
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session
from src.models import Base, Post, Profile, PostIntelligence

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


def _make_post(session):
    profile = Profile(handle="test_user", type="competitor", follower_count=10000)
    session.add(profile)
    session.flush()
    post = Post(
        profile_id=profile.id,
        instagram_id="post_001",
        image_url="https://example.com/img.jpg",
        caption="Soja transgênica aumenta produtividade em 20% segundo Embrapa 2023.",
        hashtags=["#soja", "#agro"],
        likes=500,
        comments=30,
        post_type="feed",
        published_at=datetime.now(timezone.utc),
    )
    session.add(post)
    session.commit()
    return post


def _mock_gpt(data: dict):
    msg = MagicMock()
    msg.content = json.dumps(data)
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


_SAMPLE_RESPONSE = {
    "agro_topic_cluster": "soja",
    "agro_segment": "grãos",
    "technical_depth": "especialista",
    "core_argument": "Soja transgênica reduz custos e aumenta produtividade.",
    "argument_structure": "dado chocante → causa técnica → solução → prova",
    "technical_claims": ["Aumento de 20% na produtividade com soja RR"],
    "data_points": [{"value": "20%", "context": "aumento de produtividade", "source": "Embrapa 2023"}],
    "sources_referenced": ["Embrapa"],
    "knowledge_assumptions": "Produtor já conhece soja convencional",
    "content_gaps": "Não mencionou impacto ambiental",
    "replication_template": "[DADO] + [CAUSA] + [SOLUÇÃO] + [CTA]",
}


def test_analyze_stores_all_fields():
    from src.analyzer.post_intelligence import analyze_post_intelligence
    with Session(engine) as s:
        post = _make_post(s)
        with patch("src.analyzer.post_intelligence.openai_client.chat.completions.create",
                   return_value=_mock_gpt(_SAMPLE_RESPONSE)):
            with patch("src.analyzer.post_intelligence.upsert_arguments"):
                result = analyze_post_intelligence(post, s)
    assert result.agro_topic_cluster == "soja"
    assert result.technical_depth == "especialista"
    assert result.core_argument == "Soja transgênica reduz custos e aumenta produtividade."
    assert result.technical_claims == ["Aumento de 20% na produtividade com soja RR"]
    assert len(result.data_points) == 1
    assert result.sources_referenced == ["Embrapa"]


def test_analyze_skips_if_already_done():
    from src.analyzer.post_intelligence import analyze_post_intelligence
    with Session(engine) as s:
        post = _make_post(s)
        existing = PostIntelligence(
            post_id=post.id,
            technical_claims=[],
            data_points=[],
            sources_referenced=[],
            analyzed_at=datetime.now(timezone.utc),
        )
        s.add(existing)
        s.commit()
        with patch("src.analyzer.post_intelligence.openai_client.chat.completions.create") as mock_gpt:
            result = analyze_post_intelligence(post, s)
    mock_gpt.assert_not_called()
    assert result.id == existing.id


def test_analyze_persists_to_db():
    from src.analyzer.post_intelligence import analyze_post_intelligence
    with Session(engine) as s:
        post = _make_post(s)
        with patch("src.analyzer.post_intelligence.openai_client.chat.completions.create",
                   return_value=_mock_gpt(_SAMPLE_RESPONSE)):
            with patch("src.analyzer.post_intelligence.upsert_arguments"):
                analyze_post_intelligence(post, s)
    with Session(engine) as s:
        row = s.query(PostIntelligence).first()
    assert row is not None
    assert row.agro_segment == "grãos"
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_post_intelligence.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'src.analyzer.post_intelligence'`

- [ ] **Step 3: Create `src/analyzer/post_intelligence.py`**

```python
import json
import logging

from openai import OpenAI
from sqlalchemy.orm import Session

from src.config import OPENAI_API_KEY
from src.models import Post, PostIntelligence

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

_SYSTEM_PROMPT = """Você é um analista de conteúdo especialista em agronegócio brasileiro.
Analise o post fornecido com profundidade técnica e retorne APENAS um JSON:
{
  "agro_topic_cluster": "<soja|milho|pecuária|insumos|gestão|tecnologia|crédito|outro>",
  "agro_segment": "<grãos|fibras|pecuária|horticultura|cafeicultura|geral>",
  "technical_depth": "<superficial|intermediário|especialista>",
  "core_argument": "<tese central em uma frase direta>",
  "argument_structure": "<fluxo lógico: ex. dado chocante → causa → solução → prova>",
  "technical_claims": ["<afirmação técnica 1>", "<afirmação técnica 2>"],
  "data_points": [{"value": "<número>", "context": "<contexto>", "source": "<fonte ou null>"}],
  "sources_referenced": ["<Embrapa>", "<MAPA>", "<pesquisa própria>"],
  "knowledge_assumptions": "<o que assume que a audiência já sabe>",
  "content_gaps": "<o que ficou de fora e enriqueceria o conteúdo>",
  "replication_template": "<fórmula replicável: ex. [DADO] + [CAUSA] + [SOLUÇÃO] + [CTA]>"
}"""


def analyze_post_intelligence(post: Post, session: Session) -> PostIntelligence:
    existing = session.query(PostIntelligence).filter_by(post_id=post.id).first()
    if existing:
        return existing

    caption = post.caption or ""
    hashtags = ", ".join(post.hashtags) if post.hashtags else ""
    user_content = f"Legenda: {caption}\nHashtags: {hashtags}"

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        max_tokens=1000,
    )

    raw = response.choices[0].message.content or ""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rstrip("`").strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("GPT-4o returned invalid JSON for post %s: %s", post.id, exc)
        raise

    intelligence = PostIntelligence(
        post_id=post.id,
        agro_topic_cluster=data.get("agro_topic_cluster"),
        agro_segment=data.get("agro_segment"),
        technical_depth=data.get("technical_depth"),
        core_argument=data.get("core_argument"),
        argument_structure=data.get("argument_structure"),
        technical_claims=data.get("technical_claims", []),
        data_points=data.get("data_points", []),
        sources_referenced=data.get("sources_referenced", []),
        knowledge_assumptions=data.get("knowledge_assumptions"),
        content_gaps=data.get("content_gaps"),
        replication_template=data.get("replication_template"),
    )
    session.add(intelligence)
    session.commit()
    session.refresh(intelligence)

    from src.analyzer.argument_extractor import upsert_arguments
    upsert_arguments(intelligence, post, session)

    logger.info("Post %s intelligence analyzed: depth=%s, claims=%d",
                post.id, intelligence.technical_depth, len(intelligence.technical_claims))
    return intelligence
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_post_intelligence.py -v
```
Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/analyzer/post_intelligence.py tests/test_post_intelligence.py
git commit -m "feat: PostIntelligence analyzer with GPT-4o technical content extraction"
```

---

## Task 3: Argument Extractor

**Files:**
- Create: `src/analyzer/argument_extractor.py`
- Create: `tests/test_argument_extractor.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_argument_extractor.py`:

```python
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session
from src.models import Base, Post, Profile, PostAnalysis, PostIntelligence, ArgumentBank

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


def _make_post_with_analysis(session, virality=0.6):
    profile = Profile(handle="agro_user", type="competitor", follower_count=5000)
    session.add(profile)
    session.flush()
    post = Post(
        profile_id=profile.id,
        instagram_id="post_abc",
        image_url="https://example.com/img.jpg",
        caption="Test caption",
        hashtags=[],
        likes=300,
        comments=20,
        post_type="feed",
        published_at=datetime.now(timezone.utc),
    )
    session.add(post)
    session.flush()
    analysis = PostAnalysis(
        post_id=post.id,
        virality_score=virality,
        technical_claims=[],
        data_points=[],
        sources_referenced=[],
        raw_analysis={},
    )
    session.add(analysis)
    session.commit()
    return post


def _make_intelligence(session, post, claims, sources=None):
    intel = PostIntelligence(
        post_id=post.id,
        agro_topic_cluster="soja",
        agro_segment="grãos",
        technical_depth="especialista",
        technical_claims=claims,
        data_points=[],
        sources_referenced=sources or [],
        analyzed_at=datetime.now(timezone.utc),
    )
    session.add(intel)
    session.commit()
    return intel


def test_upsert_inserts_new_arguments():
    from src.analyzer.argument_extractor import upsert_arguments
    with Session(engine) as s:
        post = _make_post_with_analysis(s)
        intel = _make_intelligence(s, post, ["Soja aumenta produtividade em 20%"])
        upsert_arguments(intel, post, s)
        args = s.query(ArgumentBank).all()
    assert len(args) == 1
    assert "soja aumenta produtividade em 20%" in args[0].text


def test_upsert_deduplicates_same_argument():
    from src.analyzer.argument_extractor import upsert_arguments
    with Session(engine) as s:
        post = _make_post_with_analysis(s)
        intel = _make_intelligence(s, post, ["Soja aumenta produtividade em 20%"])
        upsert_arguments(intel, post, s)
        upsert_arguments(intel, post, s)
        args = s.query(ArgumentBank).all()
    assert len(args) == 1
    assert args[0].times_seen == 2


def test_quality_score_with_number_and_source():
    from src.analyzer.argument_extractor import upsert_arguments
    with Session(engine) as s:
        post = _make_post_with_analysis(s)
        intel = _make_intelligence(
            s, post,
            ["Produtividade aumenta 20% com rotação de cultura conforme dados técnicos compilados"],
            sources=["Embrapa"],
        )
        upsert_arguments(intel, post, s)
        arg = s.query(ArgumentBank).first()
    assert arg.quality_score == 1.0


def test_quality_score_no_number_no_source():
    from src.analyzer.argument_extractor import upsert_arguments
    with Session(engine) as s:
        post = _make_post_with_analysis(s)
        intel = _make_intelligence(s, post, ["curto"])
        upsert_arguments(intel, post, s)
        arg = s.query(ArgumentBank).first()
    assert arg.quality_score == 0.0


def test_virality_weight_set_from_post_analysis():
    from src.analyzer.argument_extractor import upsert_arguments
    with Session(engine) as s:
        post = _make_post_with_analysis(s, virality=0.75)
        intel = _make_intelligence(s, post, ["Soja RR aumenta margem em 15 pontos percentuais"])
        upsert_arguments(intel, post, s)
        arg = s.query(ArgumentBank).first()
    assert arg.virality_weight == 0.75
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_argument_extractor.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'src.analyzer.argument_extractor'`

- [ ] **Step 3: Create `src/analyzer/argument_extractor.py`**

```python
import re
import logging

from sqlalchemy.orm import Session

from src.models import ArgumentBank, Post, PostIntelligence

logger = logging.getLogger(__name__)


def _normalize(text: str) -> str:
    return text.lower().strip()


def _compute_quality_score(text: str, has_source: bool) -> float:
    score = 0.0
    if re.search(r'\d+', text):
        score += 0.4
    if has_source:
        score += 0.3
    if len(text.split()) >= 15:
        score += 0.3
    return round(score, 2)


def upsert_arguments(intelligence: PostIntelligence, post: Post, session: Session) -> None:
    virality_score = 0.0
    if post.analysis:
        virality_score = post.analysis.virality_score or 0.0

    candidates: list[str] = list(intelligence.technical_claims or [])
    for dp in intelligence.data_points or []:
        if isinstance(dp, dict):
            val = dp.get("value", "")
            ctx = dp.get("context", "")
            combined = f"{val} — {ctx}".strip(" —") if val else ctx
            if combined:
                candidates.append(combined)

    has_source = bool(intelligence.sources_referenced)

    for raw_text in candidates:
        if not raw_text or not raw_text.strip():
            continue
        norm = _normalize(raw_text)
        existing = session.query(ArgumentBank).filter(ArgumentBank.text == norm).first()

        if existing:
            existing.times_seen += 1
            ids = list(existing.source_post_ids or [])
            if post.id not in ids:
                ids.append(post.id)
            existing.source_post_ids = ids
            n = existing.times_seen
            existing.virality_weight = round(
                ((existing.virality_weight * (n - 1)) + virality_score) / n, 4
            )
        else:
            quality = _compute_quality_score(norm, has_source)
            session.add(ArgumentBank(
                text=norm,
                topic_cluster=intelligence.agro_topic_cluster,
                agro_segment=intelligence.agro_segment,
                quality_score=quality,
                virality_weight=round(virality_score, 4),
                source_post_ids=[post.id],
                times_seen=1,
                origin="extracted",
            ))

    session.commit()
    logger.info("Upserted %d argument candidates for post %s", len(candidates), post.id)
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_argument_extractor.py -v
```
Expected: 5 tests PASS.

- [ ] **Step 5: Run full suite to verify no regressions**

```bash
pytest --tb=short -q
```
Expected: all existing tests still PASS.

- [ ] **Step 6: Commit**

```bash
git add src/analyzer/argument_extractor.py tests/test_argument_extractor.py
git commit -m "feat: argument extractor with quality scoring and deduplication"
```

---

## Task 4: Intelligence API Router

**Files:**
- Create: `api/routers/intelligence.py`
- Modify: `api/main.py` (add router)
- Create: `tests/test_api_intelligence.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_api_intelligence.py`:

```python
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from src.models import Base, Post, Profile, PostAnalysis, PostIntelligence, ArgumentBank
from api.main import app
from api.deps import get_db

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(engine)


def override_db():
    with Session(engine) as s:
        yield s

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    app.dependency_overrides[get_db] = override_db
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    app.dependency_overrides.pop(get_db, None)


def _seed_intelligence(session):
    profile = Profile(handle="agro_profile", type="competitor", follower_count=8000)
    session.add(profile)
    session.flush()
    post = Post(
        profile_id=profile.id,
        instagram_id="intel_post_1",
        image_url="https://example.com/img.jpg",
        caption="Soja transgênica",
        hashtags=[],
        likes=400,
        comments=25,
        post_type="feed",
        published_at=datetime.now(timezone.utc),
    )
    session.add(post)
    session.flush()
    intel = PostIntelligence(
        post_id=post.id,
        agro_topic_cluster="soja",
        agro_segment="grãos",
        technical_depth="especialista",
        core_argument="Soja RR é mais rentável.",
        argument_structure="dado → causa → solução",
        technical_claims=["20% mais produtivo"],
        data_points=[],
        sources_referenced=["Embrapa"],
        knowledge_assumptions="Conhece soja convencional",
        content_gaps="Sem menção ao custo de licença",
        replication_template="[DADO] + [CAUSA] + [CTA]",
        analyzed_at=datetime.now(timezone.utc),
    )
    session.add(intel)
    session.commit()
    return post, intel


def test_list_intelligence_empty():
    response = client.get("/intelligence/posts")
    assert response.status_code == 200
    assert response.json() == []


def test_list_intelligence_returns_data():
    with Session(engine) as s:
        _seed_intelligence(s)
    response = client.get("/intelligence/posts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["agro_topic_cluster"] == "soja"
    assert data[0]["technical_depth"] == "especialista"


def test_get_intelligence_by_post_id():
    with Session(engine) as s:
        post, _ = _seed_intelligence(s)
    response = client.get(f"/intelligence/posts/{post.id}")
    assert response.status_code == 200
    assert response.json()["core_argument"] == "Soja RR é mais rentável."


def test_get_intelligence_not_found():
    response = client.get("/intelligence/posts/9999")
    assert response.status_code == 404


def test_list_arguments_empty():
    response = client.get("/intelligence/arguments")
    assert response.status_code == 200
    assert response.json() == []


def test_list_arguments_with_filter():
    with Session(engine) as s:
        s.add(ArgumentBank(
            text="soja rr aumenta produtividade 20%",
            topic_cluster="soja",
            agro_segment="grãos",
            quality_score=0.7,
            virality_weight=0.6,
            source_post_ids=[1],
            times_seen=1,
            origin="extracted",
            created_at=datetime.now(timezone.utc),
        ))
        s.add(ArgumentBank(
            text="milho híbrido reduz custo por saca",
            topic_cluster="milho",
            agro_segment="grãos",
            quality_score=0.4,
            virality_weight=0.3,
            source_post_ids=[2],
            times_seen=1,
            origin="extracted",
            created_at=datetime.now(timezone.utc),
        ))
        s.commit()
    response = client.get("/intelligence/arguments?topic_cluster=soja")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["topic_cluster"] == "soja"


def test_trigger_analyze_returns_count():
    with Session(engine) as s:
        profile = Profile(handle="new_profile", type="competitor", follower_count=3000)
        s.add(profile)
        s.flush()
        post = Post(
            profile_id=profile.id,
            instagram_id="unanalyzed_post",
            image_url="https://example.com/img.jpg",
            caption="Pecuária em alta no cerrado brasileiro",
            hashtags=[],
            likes=100,
            comments=5,
            post_type="feed",
            published_at=datetime.now(timezone.utc),
        )
        s.add(post)
        s.commit()

    mock_intel = MagicMock()
    with patch("api.routers.intelligence.analyze_post_intelligence", return_value=mock_intel):
        response = client.post("/intelligence/analyze")
    assert response.status_code == 200
    assert response.json()["processed"] == 1
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_api_intelligence.py -v
```
Expected: FAIL — router not registered yet.

- [ ] **Step 3: Create `api/routers/intelligence.py`**

```python
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_db
from src.analyzer.post_intelligence import analyze_post_intelligence
from src.models import ArgumentBank, Post, PostAnalysis, PostIntelligence

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/intelligence", tags=["intelligence"])


class PostIntelligenceOut(BaseModel):
    post_id: int
    handle: str
    likes: int
    virality_score: Optional[float]
    agro_topic_cluster: Optional[str]
    agro_segment: Optional[str]
    technical_depth: Optional[str]
    core_argument: Optional[str]
    argument_structure: Optional[str]
    technical_claims: list
    data_points: list
    sources_referenced: list
    knowledge_assumptions: Optional[str]
    content_gaps: Optional[str]
    replication_template: Optional[str]
    analyzed_at: datetime


class ArgumentBankOut(BaseModel):
    id: int
    text: str
    topic_cluster: Optional[str]
    agro_segment: Optional[str]
    quality_score: float
    virality_weight: float
    times_seen: int
    source_post_count: int
    origin: str


class AnalyzeResponse(BaseModel):
    processed: int


def _intel_to_out(intel: PostIntelligence) -> PostIntelligenceOut:
    post = intel.post
    return PostIntelligenceOut(
        post_id=post.id,
        handle=post.profile.handle,
        likes=post.likes,
        virality_score=post.analysis.virality_score if post.analysis else None,
        agro_topic_cluster=intel.agro_topic_cluster,
        agro_segment=intel.agro_segment,
        technical_depth=intel.technical_depth,
        core_argument=intel.core_argument,
        argument_structure=intel.argument_structure,
        technical_claims=intel.technical_claims or [],
        data_points=intel.data_points or [],
        sources_referenced=intel.sources_referenced or [],
        knowledge_assumptions=intel.knowledge_assumptions,
        content_gaps=intel.content_gaps,
        replication_template=intel.replication_template,
        analyzed_at=intel.analyzed_at,
    )


@router.get("/posts", response_model=List[PostIntelligenceOut])
def list_intelligence(page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    offset = (page - 1) * 20
    rows = (
        db.query(PostIntelligence)
        .join(PostIntelligence.post)
        .order_by(PostIntelligence.analyzed_at.desc())
        .offset(offset)
        .limit(20)
        .all()
    )
    return [_intel_to_out(r) for r in rows]


@router.get("/posts/{post_id}", response_model=PostIntelligenceOut)
def get_intelligence(post_id: int, db: Session = Depends(get_db)):
    intel = db.query(PostIntelligence).filter_by(post_id=post_id).first()
    if not intel:
        raise HTTPException(status_code=404, detail="Not analyzed yet")
    return _intel_to_out(intel)


@router.get("/arguments", response_model=List[ArgumentBankOut])
def list_arguments(
    topic_cluster: Optional[str] = Query(None),
    agro_segment: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(ArgumentBank)
    if topic_cluster:
        q = q.filter(ArgumentBank.topic_cluster == topic_cluster)
    if agro_segment:
        q = q.filter(ArgumentBank.agro_segment == agro_segment)
    rows = q.order_by(
        (ArgumentBank.virality_weight * ArgumentBank.quality_score).desc()
    ).limit(100).all()
    return [
        ArgumentBankOut(
            id=r.id,
            text=r.text,
            topic_cluster=r.topic_cluster,
            agro_segment=r.agro_segment,
            quality_score=r.quality_score,
            virality_weight=r.virality_weight,
            times_seen=r.times_seen,
            source_post_count=len(r.source_post_ids or []),
            origin=r.origin,
        )
        for r in rows
    ]


@router.post("/analyze", response_model=AnalyzeResponse)
def trigger_analysis(db: Session = Depends(get_db)):
    analyzed_ids = [r[0] for r in db.query(PostIntelligence.post_id).all()]
    q = db.query(Post)
    if analyzed_ids:
        q = q.filter(Post.id.notin_(analyzed_ids))
    posts = q.limit(50).all()

    count = 0
    for post in posts:
        try:
            analyze_post_intelligence(post, db)
            count += 1
        except Exception as exc:
            logger.error("Failed to analyze post %s: %s", post.id, exc)
    return AnalyzeResponse(processed=count)
```

- [ ] **Step 4: Register router in `api/main.py`**

Open `api/main.py`. Change the import line:
```python
from api.routers import competitors, carousel, news, reports, voice, studio
```
to:
```python
from api.routers import competitors, carousel, news, reports, voice, studio, intelligence
```

Then add after `app.include_router(studio.router)`:
```python
app.include_router(intelligence.router)
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
pytest tests/test_api_intelligence.py -v
```
Expected: 8 tests PASS.

- [ ] **Step 6: Run full suite**

```bash
pytest --tb=short -q
```
Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add api/routers/intelligence.py api/main.py tests/test_api_intelligence.py
git commit -m "feat: intelligence API router — posts deep dive and argument bank endpoints"
```

---

## Task 5: APScheduler Daily Job

**Files:**
- Modify: `api/main.py`

- [ ] **Step 1: Add `_run_daily_intelligence` to `api/main.py`**

Open `api/main.py`. After the existing `_run_daily_suggestions` function, add:

```python
def _run_daily_intelligence():
    from src.database import get_session
    from src.models import Post, PostIntelligence
    from src.analyzer.post_intelligence import analyze_post_intelligence
    session = get_session()
    try:
        analyzed_ids = [r[0] for r in session.query(PostIntelligence.post_id).all()]
        q = session.query(Post)
        if analyzed_ids:
            q = q.filter(Post.id.notin_(analyzed_ids))
        posts = q.limit(50).all()
        for post in posts:
            try:
                analyze_post_intelligence(post, session)
            except Exception as exc:
                logger.error("Daily intelligence job failed for post %s: %s", post.id, exc)
        logger.info("Daily intelligence job processed %d posts", len(posts))
    except Exception as exc:
        logger.error("Daily intelligence job failed: %s", exc)
    finally:
        session.close()
```

Then in the scheduler setup block (after the existing `scheduler.add_job` line), add:

```python
scheduler.add_job(_run_daily_intelligence, "cron", hour=7, minute=0)
```

- [ ] **Step 2: Run full test suite to confirm nothing broke**

```bash
pytest --tb=short -q
```
Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add api/main.py
git commit -m "feat: daily APScheduler job for post intelligence at 07:00 UTC"
```

---

## Task 6: Inject Arguments into Carousel Generator

**Files:**
- Modify: `src/carousel/generator.py`

- [ ] **Step 1: Update import in `src/carousel/generator.py`**

Change:
```python
from src.models import ProfileVoice, WeeklyReport, Carousel
```
to:
```python
from src.models import ArgumentBank, Carousel, ProfileVoice, WeeklyReport
```

- [ ] **Step 2: Add argument bank query before context is built**

In the `generate_carousel` function, after the `report` query and before `context = {...}`, add:

```python
    top_args = (
        session.query(ArgumentBank)
        .filter(ArgumentBank.origin == "extracted")
        .order_by((ArgumentBank.virality_weight * ArgumentBank.quality_score).desc())
        .limit(5)
        .all()
    )
    top_arg_texts = [a.text for a in top_args]
```

Then in the `context` dict, add the new key:

```python
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
        "argumentos_de_alto_desempenho": top_arg_texts,
    }
```

- [ ] **Step 3: Run carousel generator tests**

```bash
pytest tests/test_carousel_generator.py -v
```
Expected: all PASS (ArgumentBank is empty in tests → `top_arg_texts = []` → no effect on existing behaviour).

- [ ] **Step 4: Run full suite**

```bash
pytest --tb=short -q
```
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/carousel/generator.py
git commit -m "feat: inject top ArgumentBank entries into carousel generator context"
```

---

## Task 7: Frontend — DrawerInteligenciaPosts + Tree Data

**Files:**
- Modify: `web/lib/tree-data.ts`
- Create: `web/components/drawers/DrawerInteligenciaPosts.tsx`

- [ ] **Step 1: Add "Análise" group to `web/lib/tree-data.ts`**

In the `groups` array, add this new group after the `gestao` group:

```typescript
    {
      id: 'analise',
      emoji: '🧠',
      label: 'Análise',
      color: '#f59e0b',
      children: [
        {
          id: 'inteligencia-posts',
          emoji: '🔍',
          label: 'Deep Dive',
          color: '#f59e0b',
          status: 'active',
          desc: 'Análise técnica profunda por post: argumentos, dados, profundidade e lógica do conteúdo agro.',
        },
        {
          id: 'inteligencia-argumentos',
          emoji: '📚',
          label: 'Argumentos',
          color: '#f59e0b',
          status: 'active',
          desc: 'Banco de argumentos extraídos dos posts virais, pontuados por qualidade e viralidade.',
        },
      ],
    },
```

- [ ] **Step 2: Create `web/components/drawers/DrawerInteligenciaPosts.tsx`**

```tsx
'use client'

import { useEffect, useState } from 'react'

interface DataPoint {
  value: string
  context: string
  source: string | null
}

interface PostIntelligence {
  post_id: number
  handle: string
  likes: number
  virality_score: number | null
  agro_topic_cluster: string | null
  agro_segment: string | null
  technical_depth: string | null
  core_argument: string | null
  argument_structure: string | null
  technical_claims: string[]
  data_points: DataPoint[]
  sources_referenced: string[]
  knowledge_assumptions: string | null
  content_gaps: string | null
  replication_template: string | null
  analyzed_at: string
}

const DEPTH_COLORS: Record<string, string> = {
  especialista: '#16a34a',
  intermediário: '#f59e0b',
  superficial: '#6b7280',
}

export function DrawerInteligenciaPosts() {
  const [posts, setPosts] = useState<PostIntelligence[]>([])
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [expanded, setExpanded] = useState<number | null>(null)

  async function load() {
    const res = await fetch('/api/intelligence/posts')
    if (res.ok) setPosts(await res.json())
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  async function analyzeNew() {
    setAnalyzing(true)
    const res = await fetch('/api/intelligence/analyze', { method: 'POST' })
    if (res.ok) {
      await load()
    }
    setAnalyzing(false)
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
          {posts.length} posts analisados
        </p>
        <button
          onClick={analyzeNew}
          disabled={analyzing}
          className="text-[11px] px-3 py-1 rounded-lg transition-all"
          style={{
            background: 'rgba(245,158,11,0.1)',
            border: '1px solid rgba(245,158,11,0.2)',
            color: analyzing ? 'rgba(255,255,255,0.25)' : '#f59e0b',
          }}
        >
          {analyzing ? '⟳ Analisando...' : '⚡ Analisar novos'}
        </button>
      </div>

      {loading ? (
        <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.25)' }}>Carregando...</p>
      ) : posts.length === 0 ? (
        <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.25)' }}>
          Nenhum post analisado ainda. Clique em "Analisar novos".
        </p>
      ) : (
        <div className="space-y-2">
          {posts.map((p) => {
            const depthColor = DEPTH_COLORS[p.technical_depth ?? ''] ?? '#6b7280'
            const isOpen = expanded === p.post_id
            return (
              <div
                key={p.post_id}
                className="rounded-lg overflow-hidden"
                style={{ border: '1px solid rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.02)' }}
              >
                <button
                  onClick={() => setExpanded(isOpen ? null : p.post_id)}
                  className="w-full flex items-center gap-3 px-4 py-3 text-left"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-[12px] font-semibold text-white truncate">@{p.handle}</span>
                      <span
                        className="text-[9px] font-bold px-1.5 py-0.5 rounded-full shrink-0"
                        style={{ background: depthColor + '22', color: depthColor, border: `1px solid ${depthColor}44` }}
                      >
                        {p.technical_depth ?? '—'}
                      </span>
                    </div>
                    <p className="text-[11px] mt-0.5 truncate" style={{ color: 'rgba(255,255,255,0.4)' }}>
                      {p.agro_topic_cluster ?? '—'} · {p.likes.toLocaleString()} likes
                    </p>
                  </div>
                  <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: 12 }}>{isOpen ? '▲' : '▼'}</span>
                </button>

                {isOpen && (
                  <div className="px-4 pb-4 space-y-3 border-t" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
                    {p.core_argument && (
                      <div className="pt-3">
                        <p className="text-[10px] font-semibold tracking-wider uppercase mb-1" style={{ color: '#f59e0b' }}>Tese central</p>
                        <p className="text-[12px] text-white">{p.core_argument}</p>
                      </div>
                    )}
                    {p.argument_structure && (
                      <div>
                        <p className="text-[10px] font-semibold tracking-wider uppercase mb-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Estrutura</p>
                        <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.6)' }}>{p.argument_structure}</p>
                      </div>
                    )}
                    {p.technical_claims.length > 0 && (
                      <div>
                        <p className="text-[10px] font-semibold tracking-wider uppercase mb-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Afirmações técnicas</p>
                        <ul className="space-y-1">
                          {p.technical_claims.map((c, i) => (
                            <li key={i} className="text-[11px] flex gap-2" style={{ color: 'rgba(255,255,255,0.6)' }}>
                              <span style={{ color: '#f59e0b' }}>•</span>{c}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {p.data_points.length > 0 && (
                      <div>
                        <p className="text-[10px] font-semibold tracking-wider uppercase mb-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Dados citados</p>
                        {p.data_points.map((d, i) => (
                          <p key={i} className="text-[11px]" style={{ color: 'rgba(255,255,255,0.55)' }}>
                            <span className="font-semibold text-white">{d.value}</span> — {d.context}
                            {d.source && <span style={{ color: '#f59e0b' }}> · {d.source}</span>}
                          </p>
                        ))}
                      </div>
                    )}
                    {p.content_gaps && (
                      <div>
                        <p className="text-[10px] font-semibold tracking-wider uppercase mb-1" style={{ color: 'rgba(255,255,255,0.4)' }}>Lacunas</p>
                        <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.5)' }}>{p.content_gaps}</p>
                      </div>
                    )}
                    {p.replication_template && (
                      <div className="rounded-lg px-3 py-2" style={{ background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.15)' }}>
                        <p className="text-[10px] font-semibold tracking-wider uppercase mb-1" style={{ color: '#f59e0b' }}>Template replicável</p>
                        <p className="text-[11px] font-mono" style={{ color: 'rgba(255,255,255,0.7)' }}>{p.replication_template}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 3: Type-check**

```bash
cd web && npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add web/lib/tree-data.ts web/components/drawers/DrawerInteligenciaPosts.tsx
git commit -m "feat: Análise group in orbital tree + DrawerInteligenciaPosts"
```

---

## Task 8: Frontend — DrawerInteligenciaArgumentos + ModuleDrawer Wiring

**Files:**
- Create: `web/components/drawers/DrawerInteligenciaArgumentos.tsx`
- Modify: `web/components/drawers/ModuleDrawer.tsx`

- [ ] **Step 1: Create `web/components/drawers/DrawerInteligenciaArgumentos.tsx`**

```tsx
'use client'

import { useEffect, useState } from 'react'

interface ArgumentEntry {
  id: number
  text: string
  topic_cluster: string | null
  agro_segment: string | null
  quality_score: number
  virality_weight: float
  times_seen: number
  source_post_count: number
  origin: string
}

const CLUSTERS = ['soja', 'milho', 'pecuária', 'insumos', 'gestão', 'tecnologia', 'crédito', 'outro']
const SEGMENTS = ['grãos', 'fibras', 'pecuária', 'horticultura', 'cafeicultura', 'geral']

function ScoreBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className="flex-1 h-1 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.08)' }}>
        <div className="h-full rounded-full" style={{ width: `${Math.round(value * 100)}%`, background: color }} />
      </div>
      <span className="text-[10px] shrink-0" style={{ color: 'rgba(255,255,255,0.35)' }}>
        {Math.round(value * 100)}
      </span>
    </div>
  )
}

export function DrawerInteligenciaArgumentos() {
  const [args, setArgs] = useState<ArgumentEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [cluster, setCluster] = useState<string | null>(null)
  const [segment, setSegment] = useState<string | null>(null)
  const [copied, setCopied] = useState<number | null>(null)

  async function load(c: string | null, s: string | null) {
    setLoading(true)
    const params = new URLSearchParams()
    if (c) params.set('topic_cluster', c)
    if (s) params.set('agro_segment', s)
    const res = await fetch(`/api/intelligence/arguments?${params}`)
    if (res.ok) setArgs(await res.json())
    setLoading(false)
  }

  useEffect(() => { load(cluster, segment) }, [cluster, segment])

  async function copyArg(arg: ArgumentEntry) {
    await navigator.clipboard.writeText(arg.text)
    setCopied(arg.id)
    setTimeout(() => setCopied(null), 1500)
  }

  return (
    <div className="p-6 space-y-4">
      <div className="space-y-2">
        <p className="text-[10px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>Tema</p>
        <div className="flex flex-wrap gap-1">
          {CLUSTERS.map((c) => (
            <button
              key={c}
              onClick={() => setCluster(cluster === c ? null : c)}
              className="text-[10px] px-2 py-0.5 rounded-full transition-all"
              style={{
                background: cluster === c ? 'rgba(245,158,11,0.15)' : 'rgba(255,255,255,0.04)',
                border: `1px solid ${cluster === c ? '#f59e0b44' : 'rgba(255,255,255,0.08)'}`,
                color: cluster === c ? '#f59e0b' : 'rgba(255,255,255,0.45)',
              }}
            >
              {c}
            </button>
          ))}
        </div>
        <p className="text-[10px] font-semibold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>Segmento</p>
        <div className="flex flex-wrap gap-1">
          {SEGMENTS.map((s) => (
            <button
              key={s}
              onClick={() => setSegment(segment === s ? null : s)}
              className="text-[10px] px-2 py-0.5 rounded-full transition-all"
              style={{
                background: segment === s ? 'rgba(245,158,11,0.15)' : 'rgba(255,255,255,0.04)',
                border: `1px solid ${segment === s ? '#f59e0b44' : 'rgba(255,255,255,0.08)'}`,
                color: segment === s ? '#f59e0b' : 'rgba(255,255,255,0.45)',
              }}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.25)' }}>Carregando...</p>
      ) : args.length === 0 ? (
        <p className="text-[11px]" style={{ color: 'rgba(255,255,255,0.25)' }}>
          Nenhum argumento ainda. Analise posts no Deep Dive primeiro.
        </p>
      ) : (
        <div className="space-y-2">
          {args.map((a) => (
            <div
              key={a.id}
              className="px-3 py-2.5 rounded-lg space-y-2"
              style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}
            >
              <p className="text-[12px] text-white leading-snug">{a.text}</p>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] w-14 shrink-0" style={{ color: 'rgba(255,255,255,0.35)' }}>qualidade</span>
                  <ScoreBar value={a.quality_score} color="#f59e0b" />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] w-14 shrink-0" style={{ color: 'rgba(255,255,255,0.35)' }}>viralidade</span>
                  <ScoreBar value={a.virality_weight} color="#16a34a" />
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {a.topic_cluster && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded-full" style={{ background: 'rgba(245,158,11,0.1)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.2)' }}>
                      {a.topic_cluster}
                    </span>
                  )}
                  <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.3)' }}>
                    {a.times_seen}× · {a.source_post_count} posts
                  </span>
                </div>
                <button
                  onClick={() => copyArg(a)}
                  className="text-[10px] px-2 py-0.5 rounded transition-all"
                  style={{
                    background: copied === a.id ? 'rgba(22,163,74,0.15)' : 'rgba(255,255,255,0.04)',
                    color: copied === a.id ? '#16a34a' : 'rgba(255,255,255,0.4)',
                    border: `1px solid ${copied === a.id ? '#16a34a33' : 'rgba(255,255,255,0.08)'}`,
                  }}
                >
                  {copied === a.id ? '✓ Copiado' : 'Copiar'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Register both drawers in `web/components/drawers/ModuleDrawer.tsx`**

Add to the import block at the top:
```tsx
import { DrawerInteligenciaPosts } from './DrawerInteligenciaPosts'
import { DrawerInteligenciaArgumentos } from './DrawerInteligenciaArgumentos'
```

Add to the `DRAWER_MAP`:
```tsx
const DRAWER_MAP: Record<string, React.ComponentType> = {
  carrossel: DrawerCarrossel,
  concorrentes: DrawerConcorrentes,
  noticias: DrawerNoticias,
  relatorios: DrawerRelatorios,
  identidade: DrawerIdentidade,
  studio: DrawerStudio,
  'inteligencia-posts': DrawerInteligenciaPosts,
  'inteligencia-argumentos': DrawerInteligenciaArgumentos,
}
```

- [ ] **Step 3: Fix TypeScript type error in DrawerInteligenciaArgumentos**

The `virality_weight: float` type annotation is Python syntax — change it to `number` in the TypeScript interface:
```tsx
  virality_weight: number
```

- [ ] **Step 4: Type-check**

```bash
cd web && npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 5: Run full Python test suite one final time**

```bash
cd .. && pytest --tb=short -q
```
Expected: all tests PASS.

- [ ] **Step 6: Commit and push**

```bash
git add web/components/drawers/DrawerInteligenciaArgumentos.tsx \
        web/components/drawers/DrawerInteligenciaPosts.tsx \
        web/components/drawers/ModuleDrawer.tsx
git commit -m "feat: DrawerInteligenciaPosts and DrawerInteligenciaArgumentos — intelligence UI"
git push origin main
```

---

## Self-Review

**Spec coverage:**
- ✅ PostIntelligence table — Task 1
- ✅ ArgumentBank table — Task 1
- ✅ `analyze_post_intelligence()` — Task 2
- ✅ `upsert_arguments()` — Task 3
- ✅ GPT-4o prompt with all 11 fields — Task 2
- ✅ Quality score formula (+0.4 number, +0.3 source, +0.3 ≥15 words) — Task 3
- ✅ De-duplication by normalized text — Task 3
- ✅ virality_weight rolling average — Task 3
- ✅ `origin="extracted"` on insert — Task 3
- ✅ GET /intelligence/posts — Task 4
- ✅ GET /intelligence/posts/{post_id} — Task 4
- ✅ GET /intelligence/arguments with filters — Task 4
- ✅ POST /intelligence/analyze — Task 4
- ✅ APScheduler job 07:00 UTC — Task 5
- ✅ Carousel generator integration — Task 6
- ✅ Análise group in orbital tree — Task 7
- ✅ DrawerInteligenciaPosts — Task 7
- ✅ DrawerInteligenciaArgumentos — Task 8
- ✅ ModuleDrawer wiring — Task 8

**Type consistency:** `PostIntelligence` fields match between model (Task 1), analyzer (Task 2), and API Pydantic schema (Task 4). `ArgumentBank` fields match between model (Task 1), extractor (Task 3), and API schema (Task 4).
