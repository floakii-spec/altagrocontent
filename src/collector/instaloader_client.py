import os
from datetime import datetime, timezone, timedelta
from typing import Optional
import instaloader


_ALLOWED_TYPES = {"GraphImage", "GraphSidecar"}

_TYPE_MAP = {
    "GraphImage": "feed",
    "GraphSidecar": "carousel",
}


def _append_unique(target: list[str], seen: set[str], value: Optional[str]) -> None:
    if not value or value in seen:
        return
    seen.add(value)
    target.append(value)


def _extract_sidecar_slide_urls(post) -> list[str]:
    if post.typename != "GraphSidecar":
        return []

    urls: list[str] = []
    seen: set[str] = set()
    try:
        nodes = post.get_sidecar_nodes()
    except Exception:
        nodes = []

    for node in nodes:
        display_url = getattr(node, "display_url", None)
        _append_unique(urls, seen, display_url)
    return urls


_loader: Optional[instaloader.Instaloader] = None


def _get_loader() -> instaloader.Instaloader:
    global _loader
    if _loader is not None:
        return _loader

    loader = instaloader.Instaloader(
        sleep=True,
        quiet=False,
        request_timeout=30,
    )
    ig_user = os.environ.get("INSTAGRAM_USER")
    ig_pass = os.environ.get("INSTAGRAM_PASS")
    session_file = os.path.join(os.path.dirname(__file__), f"../../.ig_session_{ig_user}")

    # Tenta session salva pelo CLI do instaloader (~/.config/instaloader/session-user)
    cli_session = os.path.expanduser(f"~/.config/instaloader/session-{ig_user}")
    if ig_user and os.path.exists(cli_session):
        loader.load_session_from_file(ig_user, cli_session)
    elif ig_user and os.path.exists(session_file):
        loader.load_session_from_file(ig_user, session_file)
    elif ig_user and ig_pass:
        loader.login(ig_user, ig_pass)
        loader.save_session_to_file(session_file)

    _loader = loader
    return _loader


def fetch_posts_instaloader(handle: str, months_back: int = 1) -> list[dict]:
    """
    Busca posts via Instaloader com login para evitar bloqueios.
    Retorna lista de dicts normalizados.
    """
    loader = _get_loader()
    profile = instaloader.Profile.from_username(loader.context, handle)
    cutoff = datetime.now(timezone.utc) - timedelta(days=months_back * 30)

    posts = []
    for post in profile.get_posts():
        if post.typename not in _ALLOWED_TYPES:
            continue
        published_at = post.date_utc.replace(tzinfo=timezone.utc)
        if published_at < cutoff:
            continue
        slide_urls = _extract_sidecar_slide_urls(post)
        posts.append({
            "instagram_id": post.shortcode,
            "image_url": post.url or (slide_urls[0] if slide_urls else ""),
            "caption": post.caption or "",
            "hashtags": list(post.caption_hashtags),
            "likes": post.likes,
            "comments": post.comments,
            "post_type": _TYPE_MAP.get(post.typename, "feed"),
            "published_at": published_at,
            "slides": slide_urls,
        })

    return posts
