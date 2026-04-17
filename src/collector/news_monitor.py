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
