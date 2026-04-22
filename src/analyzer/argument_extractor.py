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


def _candidate_texts(intelligence: PostIntelligence) -> List[str]:
    seen: set[str] = set()
    texts: List[str] = []

    for raw_text in intelligence.technical_claims or []:
        if not raw_text or not str(raw_text).strip():
            continue
        norm = _normalize(str(raw_text))
        if norm in seen:
            continue
        seen.add(norm)
        texts.append(str(raw_text).strip())

    for dp in intelligence.data_points or []:
        if not isinstance(dp, dict):
            continue
        val = str(dp.get("value", "")).strip()
        ctx = str(dp.get("context", "")).strip()
        combined = f"{val} — {ctx}".strip(" —") if val else ctx
        if not combined:
            continue
        norm = _normalize(combined)
        if norm in seen:
            continue
        seen.add(norm)
        texts.append(combined)

    return texts


def _average_virality(post_ids: List[int], session: Session) -> float:
    if not post_ids:
        return 0.0

    scores = []
    posts = session.query(Post).filter(Post.id.in_(post_ids)).all()
    for post in posts:
        if post.analysis and post.analysis.virality_score is not None:
            scores.append(post.analysis.virality_score)
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 4)


def remove_arguments_for_post(
    intelligence: PostIntelligence,
    post: Post,
    session: Session,
    commit: bool = True,
) -> None:
    for raw_text in _candidate_texts(intelligence):
        norm = _normalize(raw_text)
        existing = session.query(ArgumentBank).filter(ArgumentBank.text == norm).first()
        if not existing:
            continue

        ids = [pid for pid in list(existing.source_post_ids or []) if pid != post.id]
        if len(ids) == len(list(existing.source_post_ids or [])):
            continue

        if not ids:
            session.delete(existing)
            continue

        existing.source_post_ids = ids
        existing.times_seen = len(ids)
        existing.virality_weight = _average_virality(ids, session)

    if commit:
        session.commit()


def upsert_arguments(
    intelligence: PostIntelligence,
    post: Post,
    session: Session,
    commit: bool = True,
) -> None:
    virality_score = 0.0
    if post.analysis:
        virality_score = post.analysis.virality_score or 0.0

    has_source = bool(intelligence.sources_referenced)

    candidates = _candidate_texts(intelligence)
    for raw_text in candidates:
        norm = _normalize(raw_text)
        existing = session.query(ArgumentBank).filter(ArgumentBank.text == norm).first()

        if existing:
            ids = list(existing.source_post_ids or [])
            if post.id in ids:
                continue
            ids.append(post.id)
            existing.source_post_ids = ids
            existing.times_seen = len(ids)
            existing.virality_weight = _average_virality(ids, session)
        else:
            quality = _compute_quality_score(raw_text, has_source)
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

    if commit:
        session.commit()
    logger.info("Upserted %d argument candidates for post %s", len(candidates), post.id)
