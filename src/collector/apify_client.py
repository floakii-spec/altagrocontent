from datetime import datetime, timezone, timedelta
from typing import Optional
from apify_client import ApifyClient


_TYPE_MAP = {
    "Image": "feed",
    "Sidecar": "carousel",
    "Video": "reel",
}


def fetch_posts_apify(
    handle: str,
    token: str,
    months_back: int = 1,
    since_date: Optional[datetime] = None,
) -> list[dict]:
    """
    Busca posts de um perfil via Apify Instagram Scraper.
    Se since_date for fornecido, busca apenas posts mais recentes que essa data.
    Retorna lista de dicts normalizados prontos para inserção no banco.
    """
    client = ApifyClient(token)
    cutoff = since_date or (datetime.now(timezone.utc) - timedelta(days=months_back * 30))

    run_input = {
        "directUrls": [f"https://www.instagram.com/{handle}/"],
        "resultsType": "posts",
        "resultsLimit": 100 if since_date is None else 20,
    }
    if since_date:
        run_input["onlyPostsNewerThan"] = since_date.strftime("%Y-%m-%d")

    run = client.actor("apify/instagram-scraper").call(run_input=run_input)
    if not run:
        raise RuntimeError("Apify run returned None")

    dataset_id = run["defaultDatasetId"]

    posts = []
    for item in client.dataset(dataset_id).iterate_items():
        post_type = _TYPE_MAP.get(item.get("type", ""), "feed")
        timestamp = item.get("timestamp", "")
        if not timestamp:
            continue
        published_at = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        if published_at < cutoff:
            continue
        posts.append({
            "instagram_id": item.get("id", ""),
            "image_url": item.get("displayUrl", ""),
            "caption": item.get("caption", "") or "",
            "hashtags": item.get("hashtags", []),
            "likes": item.get("likesCount", 0),
            "comments": item.get("commentsCount", 0),
            "post_type": post_type,
            "published_at": published_at,
        })

    return posts
