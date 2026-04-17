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
