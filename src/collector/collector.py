import logging
from sqlalchemy.orm import Session
from src.models import Profile, Post
from src.collector.apify_client import fetch_posts_apify
from src.collector.instaloader_client import fetch_posts_instaloader

logger = logging.getLogger(__name__)


def collect_profile(profile: Profile, session: Session, apify_token: str, months_back: int = 6) -> int:
    """
    Coleta posts novos de um perfil. Tenta Apify primeiro, cai para Instaloader em caso de falha.
    Retorna número de novos posts salvos.
    """
    try:
        raw_posts = fetch_posts_apify(handle=profile.handle, token=apify_token, months_back=months_back)
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
