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
