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
            "url": "https://example.com/existing",
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
