from datetime import datetime, timezone, timedelta
from apify_client import ApifyClient


_TYPE_MAP = {
    "Image": "feed",
    "Sidecar": "carousel",
    "Video": "reel",
}


def fetch_posts_apify(handle: str, token: str, months_back: int = 1) -> list[dict]:
    """
    Busca posts de um perfil via Apify Instagram Scraper.
    Retorna lista de dicts normalizados prontos para inserção no banco.
    """
    client = ApifyClient(token)
    cutoff = datetime.now(timezone.utc) - timedelta(days=months_back * 30)

    run = client.actor("apify/instagram-scraper").call(run_input={
        "directUrls": [f"https://www.instagram.com/{handle}/"],
        "resultsType": "posts",
        "resultsLimit": 30,
    })
    if not run:
        raise RuntimeError("Apify run returned None")

    dataset_id = run["defaultDatasetId"]

    posts = []
    for item in client.dataset(dataset_id).iterate_items():
        post_type = _TYPE_MAP.get(item.get("type", ""), "feed")
        published_at = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
        if published_at < cutoff:
            continue
        posts.append({
            "instagram_id": item["id"],
            "image_url": item.get("displayUrl", ""),
            "caption": item.get("caption", ""),
            "hashtags": item.get("hashtags", []),
            "likes": item.get("likesCount", 0),
            "comments": item.get("commentsCount", 0),
            "post_type": post_type,
            "published_at": published_at,
        })

    return posts
