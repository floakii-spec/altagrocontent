import logging
from sqlalchemy.orm import Session
from src.models import Profile, Post
from src.collector.apify_client import fetch_posts_apify
from src.collector.instaloader_client import fetch_posts_instaloader

logger = logging.getLogger(__name__)


def _merge_post(existing: Post, raw: dict) -> bool:
    changed = False

    incoming_slides = list(raw.get("slides") or [])
    existing_slides = list(existing.slides or [])
    if incoming_slides and len(incoming_slides) > len(existing_slides):
        existing.slides = incoming_slides
        changed = True

    incoming_caption = raw.get("caption") or ""
    if incoming_caption and len(incoming_caption) > len(existing.caption or ""):
        existing.caption = incoming_caption
        changed = True

    incoming_hashtags = list(raw.get("hashtags") or [])
    if incoming_hashtags and len(incoming_hashtags) > len(existing.hashtags or []):
        existing.hashtags = incoming_hashtags
        changed = True

    incoming_image = raw.get("image_url") or ""
    if incoming_image and incoming_image != existing.image_url:
        existing.image_url = incoming_image
        changed = True

    if raw.get("published_at") and raw["published_at"] != existing.published_at:
        existing.published_at = raw["published_at"]
        changed = True

    if raw.get("post_type") and raw["post_type"] != existing.post_type:
        existing.post_type = raw["post_type"]
        changed = True

    likes = raw.get("likes", existing.likes)
    if likes != existing.likes:
        existing.likes = likes
        changed = True

    comments = raw.get("comments", existing.comments)
    if comments != existing.comments:
        existing.comments = comments
        changed = True

    return changed


def collect_profile(profile: Profile, session: Session, apify_token: str, months_back: int = 1) -> int:
    """
    Coleta posts novos de um perfil. Tenta Apify primeiro, cai para Instaloader em caso de falha.
    Se o perfil já tem posts, busca apenas a partir do post mais recente (economiza créditos Apify).
    Retorna número de novos posts salvos.
    """
    existing_post_rows = session.query(Post).filter_by(profile_id=profile.id).all()
    needs_slide_backfill = any(p.post_type == "carousel" and not (p.slides or []) for p in existing_post_rows)
    latest = None
    if not needs_slide_backfill:
        latest = (
            session.query(Post.published_at)
            .filter_by(profile_id=profile.id)
            .order_by(Post.published_at.desc())
            .first()
        )
    since_date = latest[0] if latest else None

    try:
        raw_posts = fetch_posts_apify(
            handle=profile.handle,
            token=apify_token,
            months_back=months_back,
            since_date=since_date,
        )
    except Exception as exc:
        logger.warning("Apify collection failed for %s, falling back to Instaloader: %s", profile.handle, exc)
        raw_posts = fetch_posts_instaloader(handle=profile.handle, months_back=months_back)

    existing_posts = {row.instagram_id: row for row in existing_post_rows}

    new_posts = []
    updated_count = 0
    for raw in raw_posts:
        existing = existing_posts.get(raw["instagram_id"])
        if existing:
            if _merge_post(existing, raw):
                updated_count += 1
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
            slides=raw.get("slides", []),
        ))

    if new_posts:
        session.add_all(new_posts)
    if new_posts or updated_count:
        session.commit()
        logger.info("Profile %s synced: %d new posts, %d updated posts", profile.handle, len(new_posts), updated_count)
    return len(new_posts)
