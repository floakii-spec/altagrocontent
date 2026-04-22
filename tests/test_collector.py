import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from src.collector.apify_client import fetch_posts_apify


MOCK_APIFY_ITEMS = [
    {
        "id": "IG001",
        "displayUrl": "https://example.com/img1.jpg",
        "caption": "Safra recorde de soja!",
        "hashtags": ["agro", "soja"],
        "likesCount": 500,
        "commentsCount": 30,
        "type": "Image",
        "timestamp": "2026-04-10T10:00:00.000Z",
    },
    {
        "id": "IG002",
        "displayUrl": "https://example.com/img2.jpg",
        "caption": "Maquinário moderno",
        "hashtags": ["maquinas"],
        "likesCount": 200,
        "commentsCount": 10,
        "type": "Video",
        "timestamp": "2026-04-11T12:00:00.000Z",
    },
    {
        "id": "IG003",
        "displayUrl": "https://example.com/cover.jpg",
        "caption": "Carrossel completo",
        "hashtags": ["carrossel"],
        "likesCount": 900,
        "commentsCount": 45,
        "type": "Sidecar",
        "timestamp": "2026-04-12T12:00:00.000Z",
        "images": ["https://example.com/cover.jpg", "https://example.com/slide2.jpg"],
        "childPosts": [
            {"displayUrl": "https://example.com/cover.jpg", "images": []},
            {"displayUrl": "https://example.com/slide2.jpg", "images": []},
            {"displayUrl": "https://example.com/slide3.jpg", "images": []},
        ],
    },
]


def test_fetch_posts_apify_returns_normalized_posts():
    mock_dataset = MagicMock()
    mock_dataset.iterate_items.return_value = iter(MOCK_APIFY_ITEMS)

    mock_actor = MagicMock()
    mock_actor.call.return_value = {"defaultDatasetId": "test-dataset-id"}

    mock_client = MagicMock()
    mock_client.actor.return_value = mock_actor
    mock_client.dataset.return_value = mock_dataset

    with patch("src.collector.apify_client.ApifyClient", return_value=mock_client):
        posts = fetch_posts_apify(handle="agro_example", token="fake-token", months_back=6)

    assert len(posts) == 3
    assert posts[0]["instagram_id"] == "IG001"
    assert posts[0]["image_url"] == "https://example.com/img1.jpg"
    assert posts[0]["caption"] == "Safra recorde de soja!"
    assert posts[0]["hashtags"] == ["agro", "soja"]
    assert posts[0]["likes"] == 500
    assert posts[0]["comments"] == 30
    assert posts[0]["post_type"] == "feed"
    assert isinstance(posts[0]["published_at"], datetime)


def test_fetch_posts_apify_maps_video_to_reel():
    mock_dataset = MagicMock()
    mock_dataset.iterate_items.return_value = iter([MOCK_APIFY_ITEMS[1]])

    mock_actor = MagicMock()
    mock_actor.call.return_value = {"defaultDatasetId": "test-dataset-id"}

    mock_client = MagicMock()
    mock_client.actor.return_value = mock_actor
    mock_client.dataset.return_value = mock_dataset

    with patch("src.collector.apify_client.ApifyClient", return_value=mock_client):
        posts = fetch_posts_apify(handle="agro_example", token="fake-token", months_back=6)

    assert posts[0]["post_type"] == "reel"


def test_fetch_posts_apify_extracts_carousel_slides():
    mock_dataset = MagicMock()
    mock_dataset.iterate_items.return_value = iter([MOCK_APIFY_ITEMS[2]])

    mock_actor = MagicMock()
    mock_actor.call.return_value = {"defaultDatasetId": "test-dataset-id"}

    mock_client = MagicMock()
    mock_client.actor.return_value = mock_actor
    mock_client.dataset.return_value = mock_dataset

    with patch("src.collector.apify_client.ApifyClient", return_value=mock_client):
        posts = fetch_posts_apify(handle="agro_example", token="fake-token", months_back=6)

    assert posts[0]["post_type"] == "carousel"
    assert posts[0]["slides"] == [
        "https://example.com/cover.jpg",
        "https://example.com/slide2.jpg",
        "https://example.com/slide3.jpg",
    ]


from src.collector.instaloader_client import fetch_posts_instaloader


def test_fetch_posts_instaloader_returns_normalized_posts():
    mock_post = MagicMock()
    mock_post.shortcode = "SC001"
    mock_post.url = "https://example.com/img.jpg"
    mock_post.caption = "Plantio direto"
    mock_post.caption_hashtags = ["plantio", "agro"]
    mock_post.likes = 300
    mock_post.comments = 20
    mock_post.is_video = False
    mock_post.typename = "GraphImage"
    mock_post.date_utc = datetime(2026, 4, 10, tzinfo=timezone.utc)

    mock_profile = MagicMock()
    mock_profile.get_posts.return_value = [mock_post]

    with patch("src.collector.instaloader_client.instaloader.Profile.from_username", return_value=mock_profile):
        with patch("src.collector.instaloader_client.instaloader.Instaloader"):
            posts = fetch_posts_instaloader(handle="agro_example", months_back=6)

    assert len(posts) == 1
    assert posts[0]["instagram_id"] == "SC001"
    assert posts[0]["post_type"] == "feed"
    assert posts[0]["likes"] == 300


def test_fetch_posts_instaloader_extracts_sidecar_slides():
    mock_node1 = MagicMock()
    mock_node1.display_url = "https://example.com/slide1.jpg"
    mock_node2 = MagicMock()
    mock_node2.display_url = "https://example.com/slide2.jpg"

    mock_post = MagicMock()
    mock_post.shortcode = "SC002"
    mock_post.url = "https://example.com/cover.jpg"
    mock_post.caption = "Carrossel técnico"
    mock_post.caption_hashtags = ["agro"]
    mock_post.likes = 450
    mock_post.comments = 18
    mock_post.typename = "GraphSidecar"
    mock_post.date_utc = datetime(2026, 4, 10, tzinfo=timezone.utc)
    mock_post.get_sidecar_nodes.return_value = [mock_node1, mock_node2]

    mock_profile = MagicMock()
    mock_profile.get_posts.return_value = [mock_post]

    with patch("src.collector.instaloader_client.instaloader.Profile.from_username", return_value=mock_profile):
        with patch("src.collector.instaloader_client.instaloader.Instaloader"):
            posts = fetch_posts_instaloader(handle="agro_example", months_back=6)

    assert posts[0]["post_type"] == "carousel"
    assert posts[0]["slides"] == ["https://example.com/slide1.jpg", "https://example.com/slide2.jpg"]


from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, Profile, Post
from src.collector.collector import collect_profile


@pytest.fixture
def db_session():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        yield s


def test_collect_profile_saves_new_posts(db_session):
    profile = Profile(handle="agro_test", type="competitor", niche="agro", follower_count=5000)
    db_session.add(profile)
    db_session.commit()

    fake_posts = [{
        "instagram_id": "NEW001",
        "image_url": "https://example.com/img.jpg",
        "caption": "Novo post",
        "hashtags": ["agro"],
        "likes": 100,
        "comments": 5,
        "post_type": "feed",
        "published_at": datetime(2026, 4, 10, tzinfo=timezone.utc),
        "slides": [],
    }]

    with patch("src.collector.collector.fetch_posts_apify", return_value=fake_posts):
        count = collect_profile(profile=profile, session=db_session, apify_token="tok", months_back=6)
    assert count == 1

    posts = db_session.query(Post).filter_by(profile_id=profile.id).all()
    assert len(posts) == 1
    assert posts[0].instagram_id == "NEW001"


def test_collect_profile_skips_existing_posts(db_session):
    profile = Profile(handle="agro_test2", type="competitor", niche="agro", follower_count=5000)
    db_session.add(profile)
    db_session.flush()

    existing = Post(
        profile_id=profile.id, instagram_id="EXIST001",
        image_url="u", caption="c", hashtags=[], likes=10, comments=1,
        post_type="feed", published_at=datetime(2026, 4, 9, tzinfo=timezone.utc)
    )
    db_session.add(existing)
    db_session.commit()

    fake_posts = [{
        "instagram_id": "EXIST001",
        "image_url": "https://example.com/img.jpg",
        "caption": "Duplicado",
        "hashtags": [],
        "likes": 200,
        "comments": 10,
        "post_type": "feed",
        "published_at": datetime(2026, 4, 9, tzinfo=timezone.utc),
        "slides": [],
    }]

    with patch("src.collector.collector.fetch_posts_apify", return_value=fake_posts):
        count = collect_profile(profile=profile, session=db_session, apify_token="tok", months_back=6)
    assert count == 0

    posts = db_session.query(Post).filter_by(profile_id=profile.id).all()
    assert len(posts) == 1  # não duplicou


def test_collect_profile_backfills_missing_slides(db_session):
    profile = Profile(handle="agro_carousel", type="competitor", niche="agro", follower_count=5000)
    db_session.add(profile)
    db_session.flush()

    existing = Post(
        profile_id=profile.id,
        instagram_id="CAR001",
        image_url="https://example.com/cover.jpg",
        caption="Resumo",
        hashtags=[],
        likes=10,
        comments=1,
        post_type="carousel",
        published_at=datetime(2026, 4, 9, tzinfo=timezone.utc),
        slides=[],
    )
    db_session.add(existing)
    db_session.commit()

    fake_posts = [{
        "instagram_id": "CAR001",
        "image_url": "https://example.com/cover.jpg",
        "caption": "Resumo muito mais completo do carrossel",
        "hashtags": ["agro", "dados"],
        "likes": 200,
        "comments": 10,
        "post_type": "carousel",
        "published_at": datetime(2026, 4, 9, tzinfo=timezone.utc),
        "slides": ["https://example.com/cover.jpg", "https://example.com/slide2.jpg"],
    }]

    with patch("src.collector.collector.fetch_posts_apify", return_value=fake_posts):
        count = collect_profile(profile=profile, session=db_session, apify_token="tok", months_back=6)
    assert count == 0

    post = db_session.query(Post).filter_by(profile_id=profile.id, instagram_id="CAR001").first()
    assert post is not None
    assert post.slides == ["https://example.com/cover.jpg", "https://example.com/slide2.jpg"]
    assert post.likes == 200
    assert post.caption == "Resumo muito mais completo do carrossel"


def test_collect_profile_refetches_existing_when_carousel_has_no_slides(db_session):
    profile = Profile(handle="agro_refresh", type="competitor", niche="agro", follower_count=5000)
    db_session.add(profile)
    db_session.flush()

    existing = Post(
        profile_id=profile.id,
        instagram_id="CAR_REFRESH",
        image_url="https://example.com/cover.jpg",
        caption="Resumo",
        hashtags=[],
        likes=10,
        comments=1,
        post_type="carousel",
        published_at=datetime(2026, 4, 9, tzinfo=timezone.utc),
        slides=[],
    )
    db_session.add(existing)
    db_session.commit()

    with patch("src.collector.collector.fetch_posts_apify", return_value=[]) as mock_fetch:
        collect_profile(profile=profile, session=db_session, apify_token="tok", months_back=6)

    assert mock_fetch.call_args.kwargs["since_date"] is None
