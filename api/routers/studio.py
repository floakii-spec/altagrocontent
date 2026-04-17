from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.models import Profile, Post, PostAnalysis, ProfileVoice, GeneratedPost
from src.generator.content_generator import generate_post
from api.deps import get_db

router = APIRouter(prefix="/studio", tags=["studio"])


class CompetitorPostOut(BaseModel):
    id: int
    handle: str
    caption: Optional[str]
    post_type: str
    virality_score: Optional[float]
    published_at: datetime


class GenerateIn(BaseModel):
    post_id: int


class GeneratedPostOut(BaseModel):
    id: int
    hook: Optional[str]
    caption: Optional[str]
    cta: Optional[str]
    created_at: datetime


@router.get("/posts", response_model=List[CompetitorPostOut])
def list_competitor_posts(db: Session = Depends(get_db)):
    rows = (
        db.query(Post)
        .join(Post.profile)
        .outerjoin(Post.analysis)
        .filter(Profile.type == "competitor")
        .order_by(PostAnalysis.virality_score.desc())
        .limit(30)
        .all()
    )
    return [
        CompetitorPostOut(
            id=p.id,
            handle=p.profile.handle,
            caption=p.caption,
            post_type=p.post_type,
            virality_score=p.analysis.virality_score if p.analysis else None,
            published_at=p.published_at,
        )
        for p in rows
    ]


@router.post("/generate", response_model=GeneratedPostOut)
def generate(body: GenerateIn, db: Session = Depends(get_db)):
    post = db.query(Post).filter_by(id=body.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    voice = (
        db.query(ProfileVoice)
        .join(Profile, ProfileVoice.profile_id == Profile.id)
        .filter(Profile.type == "own")
        .order_by(ProfileVoice.generated_at.desc())
        .first()
    )
    if not voice:
        raise HTTPException(status_code=404, detail="Voice profile not configured. Run /voice/analyze first.")
    approved = (
        db.query(GeneratedPost)
        .filter_by(status="approved")
        .order_by(GeneratedPost.created_at.desc())
        .limit(3)
        .all()
    )
    generated = generate_post(source_post=post, voice=voice, approved_examples=approved, session=db)
    return GeneratedPostOut(
        id=generated.id, hook=generated.hook, caption=generated.caption,
        cta=generated.cta, created_at=generated.created_at,
    )
