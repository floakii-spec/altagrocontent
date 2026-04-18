import logging
from sqlalchemy.orm import Session
from src.models import Profile, Post
from src.collector.apify_client import fetch_posts_apify
from src.collector.instaloader_client import fetch_posts_instaloader

logger = logging.getLogger(__name__)


def collect_profile(profile: Profile, session: Session, apify_token: str, months_back: int = 1) -> int:
    """
    Coleta posts novos de um perfil. Tenta Apify primeiro, cai para Instaloader em caso de falha.
    Se o perfil já tem posts, busca apenas a partir do post mais recente (economiza créditos Apify).
    Retorna número de novos posts salvos.
    """
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
