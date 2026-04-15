from datetime import datetime, timezone, timedelta
from apify_client import ApifyClient


_TYPE_MAP = {
    "Image": "feed",
    "Video": "reel",
    "Sidecar": "carousel",
}


def fetch_posts_apify(handle: str, token: str, months_back: int = 6) -> list[dict]:
    """
    Busca posts de um perfil via Apify Instagram Scraper.
    Retorna lista de dicts normalizados prontos para inserção no banco.
    """
    client = ApifyClient(token)
    cutoff = datetime.now(timezone.utc) - timedelta(days=months_back * 30)

    run = client.actor("apify/instagram-scraper").call(run_input={
        "directUrls": [f"https://www.instagram.com/{handle}/"],
        "resultsType": "posts",
        "resultsLimit": 200,
    })
    if not run or run.get("status") not in ("SUCCEEDED",):
        raise RuntimeError(f"Apify run failed with status: {run.get('status') if run else 'None'}")

    posts = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
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
            "post_type": _TYPE_MAP.get(item.get("type", ""), "feed"),
            "published_at": published_at,
        })

    return posts
