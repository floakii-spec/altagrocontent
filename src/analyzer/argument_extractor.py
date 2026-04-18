import re
import logging
from typing import List

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

    candidates: List[str] = list(intelligence.technical_claims or [])
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
