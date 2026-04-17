# FastAPI Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Streamlit dashboard with a FastAPI REST API that exposes the existing Python business logic as HTTP endpoints callable by the Next.js frontend.

**Architecture:** A new `api/` directory at repo root wraps existing `src/` modules with FastAPI route handlers. Each router is a thin adapter — no business logic moves, only JSON serialization is added. The `altagrocontent` Railway service switches from `streamlit run` to `uvicorn api.main:app`.

**Tech Stack:** FastAPI 0.111, Uvicorn 0.30, Pydantic v2 (bundled with FastAPI), pytest + httpx for testing, existing SQLAlchemy sessions via `src/database.py`.

---

## File Structure

```
api/
  __init__.py          (empty)
  main.py              FastAPI app instance, mounts routers, CORS
  deps.py              get_db() generator for FastAPI DI
  routers/
    __init__.py        (empty)
    competitors.py     GET/POST/DELETE /competitors, POST /competitors/sync, GET /competitors/gap
    carousel.py        GET /carousel, POST /carousel/generate
    news.py            GET /news, POST /news/refresh
    reports.py         GET /reports, POST /reports/generate
    voice.py           GET /voice, POST /voice/analyze
    studio.py          GET /studio/posts, POST /studio/generate

tests/
  test_api_competitors.py
  test_api_carousel.py
  test_api_news.py
  test_api_reports.py
  test_api_voice.py
  test_api_studio.py

requirements.txt       add fastapi, uvicorn[standard], httpx; remove streamlit
start.sh               change streamlit run → uvicorn api.main:app
```

---

### Task 1: Update dependencies and start script

**Files:**
- Modify: `requirements.txt`
- Modify: `start.sh`

- [ ] **Step 1: Update requirements.txt**

Replace `streamlit==1.35.0` with the three new dependencies:

```
sqlalchemy==2.0.30
alembic==1.13.1
psycopg2-binary==2.9.9
apify-client==1.7.1
instaloader==4.13.1
openai==1.30.1
httpx<0.28
apscheduler==3.10.4
fastapi==0.111.0
uvicorn[standard]==0.30.1
python-dotenv==1.0.1
pytest==8.2.0
pytest-mock==3.14.0
feedparser==6.0.11
```

- [ ] **Step 2: Update start.sh**

```bash
#!/bin/bash
set -e

export PYTHONPATH=/app:$PYTHONPATH

echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI..."
uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}
```

- [ ] **Step 3: Verify local install**

```bash
pip install fastapi==0.111.0 uvicorn[standard]==0.30.1
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt start.sh
git commit -m "chore: replace streamlit with fastapi + uvicorn"
```

---

### Task 2: Create api/deps.py and api/main.py

**Files:**
- Create: `api/__init__.py`
- Create: `api/deps.py`
- Create: `api/routers/__init__.py`
- Create: `api/main.py`

- [ ] **Step 1: Write a failing test for the health endpoint**

Create `tests/test_api_main.py`:

```python
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run to confirm it fails**

```bash
pytest tests/test_api_main.py -v
```

Expected: `ModuleNotFoundError: No module named 'api'`

- [ ] **Step 3: Create the files**

`api/__init__.py` — empty file.

`api/routers/__init__.py` — empty file.

`api/deps.py`:

```python
from typing import Generator
from sqlalchemy.orm import Session
from src.database import get_session


def get_db() -> Generator[Session, None, None]:
    session = get_session()
    try:
        yield session
    finally:
        session.close()
```

`api/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Agro Intel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Run test to confirm it passes**

```bash
pytest tests/test_api_main.py -v
```

Expected: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add api/ tests/test_api_main.py
git commit -m "feat: FastAPI app skeleton with health endpoint"
```

---

### Task 3: Competitors router

**Files:**
- Create: `api/routers/competitors.py`
- Create: `tests/test_api_competitors.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_api_competitors.py`:

```python
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, Profile, Post
from api.main import app
from api.deps import get_db

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)


def override_db():
    with Session(engine) as s:
        yield s

app.dependency_overrides[get_db] = override_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


def test_list_competitors_empty():
    response = client.get("/competitors")
    assert response.status_code == 200
    assert response.json() == []


def test_add_competitor():
    response = client.post("/competitors", json={"handle": "agro123", "type": "competitor"})
    assert response.status_code == 200
    data = response.json()
    assert data["handle"] == "agro123"
    assert data["type"] == "competitor"
    assert "id" in data


def test_add_own_profile():
    response = client.post("/competitors", json={"handle": "myprofile", "type": "own"})
    assert response.status_code == 200
    assert response.json()["type"] == "own"


def test_delete_competitor():
    add = client.post("/competitors", json={"handle": "todelete", "type": "competitor"})
    profile_id = add.json()["id"]
    response = client.delete(f"/competitors/{profile_id}")
    assert response.status_code == 200
    listed = client.get("/competitors")
    assert all(p["id"] != profile_id for p in listed.json())


def test_list_competitors_returns_post_count():
    with Session(engine) as s:
        p = Profile(handle="withposts", type="competitor")
        s.add(p)
        s.flush()
        from datetime import datetime, timezone
        post = Post(
            profile_id=p.id,
            instagram_id="ig1",
            image_url="http://x.com/img.jpg",
            post_type="feed",
            published_at=datetime.now(timezone.utc),
        )
        s.add(post)
        s.commit()
    response = client.get("/competitors")
    profile = next(p for p in response.json() if p["handle"] == "withposts")
    assert profile["post_count"] == 1
```

- [ ] **Step 2: Run to confirm they fail**

```bash
pytest tests/test_api_competitors.py -v
```

Expected: `ImportError` or `404`

- [ ] **Step 3: Implement the router**

Create `api/routers/competitors.py`:

```python
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.models import Profile, Post, PostAnalysis
from api.deps import get_db
import os

router = APIRouter(prefix="/competitors", tags=["competitors"])


class ProfileIn(BaseModel):
    handle: str
    type: str  # "competitor" | "own"


class ProfileOut(BaseModel):
    id: int
    handle: str
    type: str
    follower_count: Optional[int]
    post_count: int
    last_sync: Optional[datetime]


@router.get("", response_model=List[ProfileOut])
def list_competitors(db: Session = Depends(get_db)):
    profiles = db.query(Profile).filter_by(active=True).order_by(Profile.handle).all()
    result = []
    for p in profiles:
        post_count = db.query(Post).filter_by(profile_id=p.id).count()
        last_post = (
            db.query(Post)
            .filter_by(profile_id=p.id)
            .order_by(Post.collected_at.desc())
            .first()
        )
        result.append(ProfileOut(
            id=p.id,
            handle=p.handle,
            type=p.type,
            follower_count=p.follower_count,
            post_count=post_count,
            last_sync=last_post.collected_at if last_post else None,
        ))
    return result


@router.post("", response_model=ProfileOut)
def add_profile(body: ProfileIn, db: Session = Depends(get_db)):
    existing = db.query(Profile).filter_by(handle=body.handle).first()
    if existing:
        existing.active = True
        existing.type = body.type
        db.commit()
        profile = existing
    else:
        profile = Profile(handle=body.handle, type=body.type)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return ProfileOut(id=profile.id, handle=profile.handle, type=profile.type,
                      follower_count=profile.follower_count, post_count=0, last_sync=None)


@router.delete("/{profile_id}")
def remove_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter_by(id=profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile.active = False
    db.commit()
    return {"ok": True}


@router.post("/sync")
def sync_profiles(db: Session = Depends(get_db)):
    from src.collector.collector import collect_profile
    from src.analyzer.image_analyzer import analyze_post
    profiles = db.query(Profile).filter_by(active=True).all()
    apify_token = os.environ["APIFY_API_TOKEN"]
    errors = []
    total_new = 0
    for profile in profiles:
        try:
            collect_profile(profile, db, apify_token)
        except Exception as e:
            errors.append({"handle": profile.handle, "error": str(e)})
            continue
        new_posts = (
            db.query(Post)
            .filter_by(profile_id=profile.id)
            .filter(Post.analysis == None)
            .all()
        )
        for post in new_posts:
            try:
                analyze_post(post, db)
                total_new += 1
            except Exception as e:
                errors.append({"handle": profile.handle, "post_id": post.id, "error": str(e)})
    return {"synced": len(profiles), "new_posts_analyzed": total_new, "errors": errors}


@router.get("/gap")
def gap_analysis(db: Session = Depends(get_db)):
    from src.analyzer.gap_analyzer import compute_gaps
    gaps = compute_gaps(db)
    return gaps
```

- [ ] **Step 4: Mount the router in main.py**

Edit `api/main.py` to add:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import competitors

app = FastAPI(title="Agro Intel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(competitors.router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_api_competitors.py tests/test_api_main.py -v
```

Expected: all `PASSED`

- [ ] **Step 6: Commit**

```bash
git add api/routers/competitors.py api/main.py tests/test_api_competitors.py
git commit -m "feat: competitors REST endpoints"
```

---

### Task 4: Carousel router

**Files:**
- Create: `api/routers/carousel.py`
- Create: `tests/test_api_carousel.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_api_carousel.py`:

```python
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, Carousel
from api.main import app
from api.deps import get_db
from datetime import datetime, timezone

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)


def override_db():
    with Session(engine) as s:
        yield s

app.dependency_overrides[get_db] = override_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


def test_list_carousels_empty():
    response = client.get("/carousel")
    assert response.status_code == 200
    assert response.json() == []


def test_list_carousels_returns_history():
    with Session(engine) as s:
        c = Carousel(theme="soja", slides=[{"slide_number": 1, "title": "T", "copy": "C", "cta": ""}],
                     generated_at=datetime.now(timezone.utc))
        s.add(c)
        s.commit()
    response = client.get("/carousel")
    assert len(response.json()) == 1
    assert response.json()[0]["theme"] == "soja"


def test_generate_carousel():
    mock_carousel = Carousel(
        id=1,
        theme="gestão de safra",
        slides=[{"slide_number": 1, "title": "Hook", "copy": "Texto", "cta": ""}],
        generated_at=datetime.now(timezone.utc),
    )
    with patch("api.routers.carousel.generate_carousel", return_value=mock_carousel):
        response = client.post("/carousel/generate", json={"theme": "gestão de safra"})
    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "gestão de safra"
    assert len(data["slides"]) == 1
```

- [ ] **Step 2: Run to confirm they fail**

```bash
pytest tests/test_api_carousel.py -v
```

Expected: `ImportError` or `404`

- [ ] **Step 3: Implement the router**

Create `api/routers/carousel.py`:

```python
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.models import Carousel
from src.carousel.generator import generate_carousel
from api.deps import get_db

router = APIRouter(prefix="/carousel", tags=["carousel"])


class CarouselGenerateIn(BaseModel):
    theme: str


class CarouselOut(BaseModel):
    id: int
    theme: str
    slides: list
    generated_at: datetime


@router.get("", response_model=List[CarouselOut])
def list_carousels(db: Session = Depends(get_db)):
    rows = db.query(Carousel).order_by(Carousel.generated_at.desc()).limit(10).all()
    return [CarouselOut(id=r.id, theme=r.theme, slides=r.slides, generated_at=r.generated_at) for r in rows]


@router.post("/generate", response_model=CarouselOut)
def generate(body: CarouselGenerateIn, db: Session = Depends(get_db)):
    carousel = generate_carousel(theme=body.theme, session=db)
    return CarouselOut(id=carousel.id, theme=carousel.theme, slides=carousel.slides, generated_at=carousel.generated_at)
```

- [ ] **Step 4: Mount router in main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import competitors, carousel

app = FastAPI(title="Agro Intel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(competitors.router)
app.include_router(carousel.router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_api_carousel.py -v
```

Expected: all `PASSED`

- [ ] **Step 6: Commit**

```bash
git add api/routers/carousel.py api/main.py tests/test_api_carousel.py
git commit -m "feat: carousel REST endpoints"
```

---

### Task 5: News router

**Files:**
- Create: `api/routers/news.py`
- Create: `tests/test_api_news.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_api_news.py`:

```python
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, NewsItem
from api.main import app
from api.deps import get_db
from datetime import datetime, timezone

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)


def override_db():
    with Session(engine) as s:
        yield s

app.dependency_overrides[get_db] = override_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


def test_list_news_empty():
    response = client.get("/news")
    assert response.status_code == 200
    assert response.json() == []


def test_list_news_returns_items():
    with Session(engine) as s:
        item = NewsItem(
            source="canal_rural",
            title="Soja bate recorde",
            url="http://example.com/1",
            published_at=datetime.now(timezone.utc),
            tags=["soja"],
        )
        s.add(item)
        s.commit()
    response = client.get("/news")
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Soja bate recorde"


def test_refresh_news():
    with patch("api.routers.news.fetch_all_feeds", return_value=3):
        response = client.post("/news/refresh")
    assert response.status_code == 200
    assert response.json()["new_items"] == 3
```

- [ ] **Step 2: Run to confirm they fail**

```bash
pytest tests/test_api_news.py -v
```

Expected: `ImportError` or `404`

- [ ] **Step 3: Implement the router**

Create `api/routers/news.py`:

```python
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.models import NewsItem
from src.collector.news_monitor import get_recent_news, fetch_all_feeds
from api.deps import get_db

router = APIRouter(prefix="/news", tags=["news"])


class NewsItemOut(BaseModel):
    id: int
    source: str
    title: str
    summary: Optional[str]
    url: str
    published_at: datetime
    tags: list


@router.get("", response_model=List[NewsItemOut])
def list_news(db: Session = Depends(get_db)):
    items = get_recent_news(db, days=7)
    return [
        NewsItemOut(id=i.id, source=i.source, title=i.title, summary=i.summary,
                    url=i.url, published_at=i.published_at, tags=i.tags)
        for i in items
    ]


@router.post("/refresh")
def refresh_news(db: Session = Depends(get_db)):
    count = fetch_all_feeds(db)
    return {"new_items": count}
```

- [ ] **Step 4: Mount router in main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import competitors, carousel, news

app = FastAPI(title="Agro Intel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(competitors.router)
app.include_router(carousel.router)
app.include_router(news.router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_api_news.py -v
```

Expected: all `PASSED`

- [ ] **Step 6: Commit**

```bash
git add api/routers/news.py api/main.py tests/test_api_news.py
git commit -m "feat: news REST endpoints"
```

---

### Task 6: Reports router

**Files:**
- Create: `api/routers/reports.py`
- Create: `tests/test_api_reports.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_api_reports.py`:

```python
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, WeeklyReport
from api.main import app
from api.deps import get_db
from datetime import datetime, timezone, timedelta

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)


def override_db():
    with Session(engine) as s:
        yield s

app.dependency_overrides[get_db] = override_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


def test_list_reports_empty():
    response = client.get("/reports")
    assert response.status_code == 200
    assert response.json() == []


def test_list_reports_returns_data():
    now = datetime.now(timezone.utc)
    with Session(engine) as s:
        r = WeeklyReport(
            period_start=now - timedelta(days=7),
            period_end=now,
            top_formats={"carrossel": 5},
            top_themes={"soja": 10},
            top_hashtags=["soja"],
            language_patterns={},
            report_text="Relatório de teste.",
            generated_at=now,
        )
        s.add(r)
        s.commit()
    response = client.get("/reports")
    assert len(response.json()) == 1
    assert response.json()[0]["report_text"] == "Relatório de teste."


def test_generate_report():
    now = datetime.now(timezone.utc)
    mock_report = WeeklyReport(
        id=1,
        period_start=now - timedelta(days=7),
        period_end=now,
        top_formats={},
        top_themes={},
        top_hashtags=[],
        language_patterns={},
        report_text="GPT report",
        generated_at=now,
    )
    with patch("api.routers.reports.generate_weekly_report", return_value=mock_report):
        response = client.post("/reports/generate")
    assert response.status_code == 200
    assert response.json()["report_text"] == "GPT report"
```

- [ ] **Step 2: Run to confirm they fail**

```bash
pytest tests/test_api_reports.py -v
```

Expected: `ImportError` or `404`

- [ ] **Step 3: Implement the router**

Create `api/routers/reports.py`:

```python
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.models import WeeklyReport
from src.reporter.weekly_report import generate_weekly_report
from api.deps import get_db

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportOut(BaseModel):
    id: int
    period_start: datetime
    period_end: datetime
    top_formats: Optional[dict]
    top_themes: Optional[dict]
    top_hashtags: Optional[list]
    language_patterns: Optional[dict]
    report_text: Optional[str]
    generated_at: datetime


@router.get("", response_model=List[ReportOut])
def list_reports(db: Session = Depends(get_db)):
    rows = db.query(WeeklyReport).order_by(WeeklyReport.period_start.desc()).all()
    return [
        ReportOut(
            id=r.id, period_start=r.period_start, period_end=r.period_end,
            top_formats=r.top_formats, top_themes=r.top_themes,
            top_hashtags=r.top_hashtags, language_patterns=r.language_patterns,
            report_text=r.report_text, generated_at=r.generated_at,
        )
        for r in rows
    ]


@router.post("/generate", response_model=ReportOut)
def generate_report(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=7)
    report = generate_weekly_report(db, period_start=period_start, period_end=now)
    return ReportOut(
        id=report.id, period_start=report.period_start, period_end=report.period_end,
        top_formats=report.top_formats, top_themes=report.top_themes,
        top_hashtags=report.top_hashtags, language_patterns=report.language_patterns,
        report_text=report.report_text, generated_at=report.generated_at,
    )
```

- [ ] **Step 4: Mount router in main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import competitors, carousel, news, reports

app = FastAPI(title="Agro Intel API")

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


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_api_reports.py -v
```

Expected: all `PASSED`

- [ ] **Step 6: Commit**

```bash
git add api/routers/reports.py api/main.py tests/test_api_reports.py
git commit -m "feat: reports REST endpoints"
```

---

### Task 7: Voice router

**Files:**
- Create: `api/routers/voice.py`
- Create: `tests/test_api_voice.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_api_voice.py`:

```python
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, Profile, ProfileVoice
from api.main import app
from api.deps import get_db
from datetime import datetime, timezone

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)


def override_db():
    with Session(engine) as s:
        yield s

app.dependency_overrides[get_db] = override_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


def test_get_voice_no_profile():
    response = client.get("/voice")
    assert response.status_code == 404


def test_get_voice_returns_latest():
    with Session(engine) as s:
        p = Profile(handle="myprofile", type="own")
        s.add(p)
        s.flush()
        v = ProfileVoice(
            profile_id=p.id,
            vocabulary={"palavras_frequentes": ["safra"]},
            tone="direto",
            dominant_themes=["soja"],
            competitor_comparison={},
            voice_summary="Tom direto.",
            generated_at=datetime.now(timezone.utc),
        )
        s.add(v)
        s.commit()
    response = client.get("/voice")
    assert response.status_code == 200
    assert response.json()["tone"] == "direto"


def test_analyze_voice():
    with Session(engine) as s:
        p = Profile(handle="myprofile", type="own")
        s.add(p)
        s.commit()
        profile_id = p.id
    mock_voice = MagicMock()
    mock_voice.id = 1
    mock_voice.tone = "confiante"
    mock_voice.dominant_themes = ["tecnologia"]
    mock_voice.vocabulary = {}
    mock_voice.competitor_comparison = {}
    mock_voice.voice_summary = "Confiante."
    mock_voice.generated_at = datetime.now(timezone.utc)
    with patch("api.routers.voice.generate_voice_profile", return_value=mock_voice):
        response = client.post("/voice/analyze")
    assert response.status_code == 200
    assert response.json()["tone"] == "confiante"
```

- [ ] **Step 2: Run to confirm they fail**

```bash
pytest tests/test_api_voice.py -v
```

Expected: `ImportError` or `404`

- [ ] **Step 3: Implement the router**

Create `api/routers/voice.py`:

```python
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.models import Profile, ProfileVoice
from src.reporter.voice_profiler import generate_voice_profile
from api.deps import get_db

router = APIRouter(prefix="/voice", tags=["voice"])


class VoiceOut(BaseModel):
    id: int
    tone: Optional[str]
    dominant_themes: list
    vocabulary: dict
    competitor_comparison: dict
    voice_summary: Optional[str]
    generated_at: datetime


@router.get("", response_model=VoiceOut)
def get_voice(db: Session = Depends(get_db)):
    own = db.query(Profile).filter_by(type="own", active=True).first()
    if not own:
        raise HTTPException(status_code=404, detail="No own profile configured")
    voice = (
        db.query(ProfileVoice)
        .filter_by(profile_id=own.id)
        .order_by(ProfileVoice.generated_at.desc())
        .first()
    )
    if not voice:
        raise HTTPException(status_code=404, detail="Voice profile not generated yet")
    return VoiceOut(
        id=voice.id, tone=voice.tone, dominant_themes=voice.dominant_themes,
        vocabulary=voice.vocabulary, competitor_comparison=voice.competitor_comparison,
        voice_summary=voice.voice_summary, generated_at=voice.generated_at,
    )


@router.post("/analyze", response_model=VoiceOut)
def analyze_voice(db: Session = Depends(get_db)):
    own = db.query(Profile).filter_by(type="own", active=True).first()
    if not own:
        raise HTTPException(status_code=404, detail="No own profile configured")
    voice = generate_voice_profile(own, db)
    return VoiceOut(
        id=voice.id, tone=voice.tone, dominant_themes=voice.dominant_themes,
        vocabulary=voice.vocabulary, competitor_comparison=voice.competitor_comparison,
        voice_summary=voice.voice_summary, generated_at=voice.generated_at,
    )
```

- [ ] **Step 4: Mount router in main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import competitors, carousel, news, reports, voice

app = FastAPI(title="Agro Intel API")

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


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_api_voice.py -v
```

Expected: all `PASSED`

- [ ] **Step 6: Commit**

```bash
git add api/routers/voice.py api/main.py tests/test_api_voice.py
git commit -m "feat: voice REST endpoints"
```

---

### Task 8: Studio router

**Files:**
- Create: `api/routers/studio.py`
- Create: `tests/test_api_studio.py`

The Studio drawer adapts a competitor post using the user's voice. Instead of a URL input (mock), the real flow is: list collected competitor posts by virality score → user picks one → POST generate.

- [ ] **Step 1: Write failing tests**

Create `tests/test_api_studio.py`:

```python
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("APIFY_API_TOKEN", "apify-test")

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, Profile, Post, PostAnalysis, ProfileVoice, GeneratedPost
from api.main import app
from api.deps import get_db
from datetime import datetime, timezone

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)


def override_db():
    with Session(engine) as s:
        yield s

app.dependency_overrides[get_db] = override_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


def test_list_studio_posts_empty():
    response = client.get("/studio/posts")
    assert response.status_code == 200
    assert response.json() == []


def test_list_studio_posts_returns_competitor_posts():
    with Session(engine) as s:
        p = Profile(handle="competidor1", type="competitor")
        s.add(p)
        s.flush()
        now = datetime.now(timezone.utc)
        post = Post(profile_id=p.id, instagram_id="ig1", image_url="http://x.com/img.jpg",
                    post_type="feed", published_at=now, caption="Post do concorrente")
        s.add(post)
        s.flush()
        analysis = PostAnalysis(post_id=post.id, virality_score=0.85,
                                raw_analysis={"hook": "Hook incrível"}, analyzed_at=now)
        s.add(analysis)
        s.commit()
    response = client.get("/studio/posts")
    assert len(response.json()) == 1
    assert response.json()[0]["handle"] == "competidor1"
    assert response.json()[0]["virality_score"] == pytest.approx(0.85)


def test_generate_studio_post():
    with Session(engine) as s:
        p = Profile(handle="comp", type="competitor")
        s.add(p)
        s.flush()
        now = datetime.now(timezone.utc)
        post = Post(profile_id=p.id, instagram_id="ig2", image_url="http://x.com/img2.jpg",
                    post_type="feed", published_at=now)
        s.add(post)
        s.flush()
        post_id = post.id
        s.commit()

    mock_generated = MagicMock()
    mock_generated.id = 1
    mock_generated.caption = "Post gerado pelo GPT"
    mock_generated.hook = "Hook gerado"
    mock_generated.cta = "Siga agora"
    mock_generated.created_at = datetime.now(timezone.utc)

    with patch("api.routers.studio.generate_post", return_value=mock_generated):
        response = client.post("/studio/generate", json={"post_id": post_id})
    assert response.status_code == 200
    assert response.json()["caption"] == "Post gerado pelo GPT"
```

- [ ] **Step 2: Run to confirm they fail**

```bash
pytest tests/test_api_studio.py -v
```

Expected: `ImportError` or `404`

- [ ] **Step 3: Implement the router**

Create `api/routers/studio.py`:

```python
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.models import Profile, Post, PostAnalysis, ProfileVoice, GeneratedPost
from src.generator.content_generator import generate_post
from api.deps import get_db

router = APIRouter(prefix="/studio", tags=["studio"])


class CompetitorPostOut(BaseModel):
    id: int
    handle: str
    caption: Optional[str]
    post_type: str
    virality_score: Optional[float]
    published_at: datetime


class GenerateIn(BaseModel):
    post_id: int


class GeneratedPostOut(BaseModel):
    id: int
    hook: Optional[str]
    caption: Optional[str]
    cta: Optional[str]
    created_at: datetime


@router.get("/posts", response_model=List[CompetitorPostOut])
def list_competitor_posts(db: Session = Depends(get_db)):
    rows = (
        db.query(Post)
        .join(Post.profile)
        .outerjoin(Post.analysis)
        .filter(Profile.type == "competitor")
        .order_by(PostAnalysis.virality_score.desc().nullslast())
        .limit(30)
        .all()
    )
    return [
        CompetitorPostOut(
            id=p.id,
            handle=p.profile.handle,
            caption=p.caption,
            post_type=p.post_type,
            virality_score=p.analysis.virality_score if p.analysis else None,
            published_at=p.published_at,
        )
        for p in rows
    ]


@router.post("/generate", response_model=GeneratedPostOut)
def generate(body: GenerateIn, db: Session = Depends(get_db)):
    post = db.query(Post).filter_by(id=body.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    voice = (
        db.query(ProfileVoice)
        .join(Profile, ProfileVoice.profile_id == Profile.id)
        .filter(Profile.type == "own")
        .order_by(ProfileVoice.generated_at.desc())
        .first()
    )
    if not voice:
        raise HTTPException(status_code=404, detail="Voice profile not configured. Run /voice/analyze first.")
    approved = (
        db.query(GeneratedPost)
        .filter_by(status="approved")
        .order_by(GeneratedPost.created_at.desc())
        .limit(3)
        .all()
    )
    generated = generate_post(source_post=post, voice=voice, approved_examples=approved, session=db)
    return GeneratedPostOut(
        id=generated.id, hook=generated.hook, caption=generated.caption,
        cta=generated.cta, created_at=generated.created_at,
    )
```

- [ ] **Step 4: Mount router in main.py — final version**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import competitors, carousel, news, reports, voice, studio

app = FastAPI(title="Agro Intel API")

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

- [ ] **Step 5: Run all tests**

```bash
pytest tests/test_api_main.py tests/test_api_competitors.py tests/test_api_carousel.py tests/test_api_news.py tests/test_api_reports.py tests/test_api_voice.py tests/test_api_studio.py -v
```

Expected: all `PASSED`

- [ ] **Step 6: Commit**

```bash
git add api/routers/studio.py api/main.py tests/test_api_studio.py
git commit -m "feat: studio REST endpoints"
```

---

### Task 9: Remove Streamlit, deploy backend

**Files:**
- Delete: `dashboard/` directory
- No new files

- [ ] **Step 1: Remove the dashboard directory**

```bash
git rm -r dashboard/
```

- [ ] **Step 2: Run all API tests to confirm nothing broke**

```bash
pytest tests/test_api_main.py tests/test_api_competitors.py tests/test_api_carousel.py tests/test_api_news.py tests/test_api_reports.py tests/test_api_voice.py tests/test_api_studio.py -v
```

Expected: all `PASSED`

- [ ] **Step 3: Push to GitHub**

```bash
git add -A
git commit -m "chore: remove streamlit dashboard"
git push origin main
```

- [ ] **Step 4: Verify Railway deployment**

Railway auto-deploys on push. Check the `altagrocontent` service logs in the Railway dashboard. Look for:

```
Running database migrations...
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8080
```

- [ ] **Step 5: Smoke-test the API**

Get the `altagrocontent` Railway URL from the dashboard. Run:

```bash
curl https://<altagrocontent-url>/health
```

Expected: `{"status":"ok"}`
