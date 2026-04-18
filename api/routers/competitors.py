from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.models import Profile, Post, PostAnalysis
from api.deps import get_db
import os

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
def sync_profiles(db: Session = Depends(get_db)):
    from src.collector.collector import collect_profile
    from src.analyzer.image_analyzer import analyze_post
    from src.analyzer.post_intelligence import analyze_post_intelligence
    profiles = db.query(Profile).filter_by(active=True).all()
    apify_token = os.environ.get("APIFY_API_TOKEN")
    if not apify_token:
        raise HTTPException(status_code=400, detail="APIFY_API_TOKEN not configured")
    errors = []
    total_new = 0
    for profile in profiles:
        try:
            collect_profile(profile, db, apify_token)
        except Exception as e:
            db.rollback()
            errors.append({"handle": profile.handle, "error": str(e)})
            continue
        new_posts = (
            db.query(Post)
            .filter_by(profile_id=profile.id)
            .filter(Post.analysis == None)
            .all()
        )
        for post in new_posts:
            try:
                analyze_post(post, db)
                total_new += 1
            except Exception as e:
                db.rollback()
                errors.append({"handle": profile.handle, "post_id": post.id, "error": str(e)})
                continue
            try:
                analyze_post_intelligence(post, db)
            except Exception as e:
                db.rollback()
                errors.append({"handle": profile.handle, "post_id": post.id, "error": f"intelligence: {e}"})
    return {"synced": len(profiles), "new_posts_analyzed": total_new, "errors": errors}


@router.get("/gap", response_model=List[dict])
def gap_analysis(db: Session = Depends(get_db)):
    from src.analyzer.gap_analyzer import compute_gaps
    gaps = compute_gaps(db)
    return gaps
