from datetime import datetime, timezone, timedelta
import instaloader


_TYPE_MAP = {
    "GraphImage": "feed",
    "GraphVideo": "reel",
    "GraphSidecar": "carousel",
}


def fetch_posts_instaloader(handle: str, months_back: int = 6) -> list:
    """
    Fallback: busca posts via Instaloader (sem token, mas mais lento e com risco de bloqueio).
    Retorna lista de dicts normalizados.
    """
    loader = instaloader.Instaloader()
    profile = instaloader.Profile.from_username(loader.context, handle)
    cutoff = datetime.now(timezone.utc) - timedelta(days=months_back * 30)

    posts = []
    for post in profile.get_posts():
        published_at = post.date_utc.replace(tzinfo=timezone.utc)
        if published_at < cutoff:
            break
        posts.append({
            "instagram_id": post.shortcode,
            "image_url": post.url,
            "caption": post.caption or "",
            "hashtags": list(post.caption_hashtags),
            "likes": post.likes,
            "comments": post.comments,
            "post_type": _TYPE_MAP.get(post.typename, "feed"),
            "published_at": published_at,
        })

    return posts
