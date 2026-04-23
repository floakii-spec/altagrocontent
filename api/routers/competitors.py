from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload
from src.models import Profile, Post
from api.deps import get_db
from src.workflows.intelligence_jobs import sync_profiles_workflow

router = APIRouter(prefix="/competitors", tags=["competitors"])


class ProfileIn(BaseModel):
    handle: str
    type: str  # "competitor" | "own"


class ProfileOut(BaseModel):
    id: int
    handle: str
    type: str
    follower_count: Optional[int]
    post_count: int
    last_sync: Optional[datetime]


class CompetitorPostOut(BaseModel):
    id: int
    instagram_id: str
    title: str
    image_url: str
    post_type: str
    published_at: datetime
    collected_at: datetime
    status: str
    has_analysis: bool
    has_intelligence: bool


class CompetitorLibraryOut(BaseModel):
    id: int
    handle: str
    follower_count: Optional[int]
    post_count: int
    analyzed_posts: int
    pending_posts: int
    last_sync: Optional[datetime]
    posts: List[CompetitorPostOut]


class SyncError(BaseModel):
    handle: str
    error: str
    post_id: Optional[int] = None


class SyncResponse(BaseModel):
    synced: int
    new_posts_analyzed: int
    errors: List[SyncError]


def _build_post_title(post: Post) -> str:
    raw_analysis = post.analysis.raw_analysis if post.analysis and isinstance(post.analysis.raw_analysis, dict) else {}
    hook = str(raw_analysis.get("hook") or "").strip()
    if hook:
        return hook[:120]

    caption = str(post.caption or "").strip()
    if caption:
        first_line = next((line.strip() for line in caption.splitlines() if line.strip()), "")
        if first_line:
            return first_line[:120]

    post_kind = {
        "carousel": "Carrossel",
        "reel": "Reel",
        "feed": "Post",
    }.get((post.post_type or "").lower(), "Post")
    if post.published_at:
        return f"{post_kind} de {post.published_at.strftime('%d/%m/%Y')}"
    return post_kind


def _build_post_status(post: Post) -> str:
    if post.intelligence:
        return "analisado"
    if post.analysis:
        return "parcial"
    return "nao_analisado"


@router.get("", response_model=List[ProfileOut])
def list_competitors(db: Session = Depends(get_db)):
    profiles = db.query(Profile).filter_by(active=True).order_by(Profile.handle).all()
    result = []
    for p in profiles:
        post_count = db.query(Post).filter_by(profile_id=p.id).count()
        last_post = (
            db.query(Post)
            .filter_by(profile_id=p.id)
            .order_by(Post.collected_at.desc())
            .first()
        )
        result.append(ProfileOut(
            id=p.id,
            handle=p.handle,
            type=p.type,
            follower_count=p.follower_count,
            post_count=post_count,
            last_sync=last_post.collected_at if last_post else None,
        ))
    return result


@router.get("/library", response_model=List[CompetitorLibraryOut])
def list_competitor_library(db: Session = Depends(get_db)):
    profiles = (
        db.query(Profile)
        .options(
            selectinload(Profile.posts).selectinload(Post.analysis),
            selectinload(Profile.posts).selectinload(Post.intelligence),
        )
        .filter_by(active=True, type="competitor")
        .order_by(Profile.handle)
        .all()
    )

    result: list[CompetitorLibraryOut] = []
    for profile in profiles:
        posts = sorted(
            profile.posts,
            key=lambda post: post.published_at or post.collected_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        post_items: list[CompetitorPostOut] = []
        analyzed_posts = 0

        for post in posts:
            status = _build_post_status(post)
            if status == "analisado":
                analyzed_posts += 1
            post_items.append(
                CompetitorPostOut(
                    id=post.id,
                    instagram_id=post.instagram_id,
                    title=_build_post_title(post),
                    image_url=post.image_url,
                    post_type=post.post_type or "feed",
                    published_at=post.published_at,
                    collected_at=post.collected_at,
                    status=status,
                    has_analysis=post.analysis is not None,
                    has_intelligence=post.intelligence is not None,
                )
            )

        last_sync = max((post.collected_at for post in profile.posts), default=None)
        result.append(
            CompetitorLibraryOut(
                id=profile.id,
                handle=profile.handle,
                follower_count=profile.follower_count,
                post_count=len(posts),
                analyzed_posts=analyzed_posts,
                pending_posts=max(len(posts) - analyzed_posts, 0),
                last_sync=last_sync,
                posts=post_items,
            )
        )

    return result


@router.post("", response_model=ProfileOut)
def add_profile(body: ProfileIn, db: Session = Depends(get_db)):
    existing = db.query(Profile).filter_by(handle=body.handle).first()
    if existing:
        existing.active = True
        existing.type = body.type
        db.commit()
        profile = existing
    else:
        profile = Profile(handle=body.handle, type=body.type)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return ProfileOut(id=profile.id, handle=profile.handle, type=profile.type,
                      follower_count=profile.follower_count, post_count=0, last_sync=None)


@router.delete("/{profile_id}")
def remove_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter_by(id=profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile.active = False
    db.commit()
    return {"ok": True}


@router.post("/sync", response_model=SyncResponse)
def sync_profiles(
    handle: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    try:
        result = sync_profiles_workflow(db, handle=handle)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return SyncResponse(
        synced=result["synced"],
        new_posts_analyzed=result["new_posts_analyzed"],
        errors=[SyncError(**error) for error in result["errors"]],
    )


@router.get("/gap", response_model=List[dict])
def gap_analysis(db: Session = Depends(get_db)):
    from src.analyzer.gap_analyzer import compute_gaps
    gaps = compute_gaps(db)
    return gaps
