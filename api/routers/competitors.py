from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
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


class SyncError(BaseModel):
    handle: str
    error: str
    post_id: Optional[int] = None


class SyncResponse(BaseModel):
    synced: int
    new_posts_analyzed: int
    errors: List[SyncError]


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
