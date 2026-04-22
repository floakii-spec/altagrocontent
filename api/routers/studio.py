from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session, joinedload
from src.models import Profile, Post, PostAnalysis, PostIntelligence, ProfileVoice, GeneratedPost
from src.generator.content_generator import generate_post
from api.deps import get_db
from src.slide_utils import normalize_carousel_slides

router = APIRouter(prefix="/studio", tags=["studio"])


class CompetitorPostOut(BaseModel):
    id: int
    handle: str
    caption: Optional[str]
    post_type: str
    virality_score: Optional[float]
    published_at: datetime
    core_argument: Optional[str]
    technical_depth: Optional[str]
    agro_topic_cluster: Optional[str]


class GenerateIn(BaseModel):
    post_id: int


class SlideOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    slide_number: int
    slide_type: str
    title: str
    body: str = Field(alias="copy", serialization_alias="copy")
    cta: str


class GeneratedPostOut(BaseModel):
    id: int
    hook: Optional[str]
    caption: Optional[str]
    cta: Optional[str]
    slides: List[SlideOut]
    funnel_stage: Optional[str]
    format: Optional[str]
    created_at: datetime


@router.get("/posts", response_model=List[CompetitorPostOut])
def list_competitor_posts(db: Session = Depends(get_db)):
    rows = (
        db.query(Post)
        .join(Post.profile)
        .outerjoin(Post.intelligence)
        .outerjoin(Post.analysis)
        .options(
            joinedload(Post.profile),
            joinedload(Post.intelligence),
            joinedload(Post.analysis),
        )
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
            core_argument=p.intelligence.core_argument if p.intelligence else None,
            technical_depth=p.intelligence.technical_depth if p.intelligence else None,
            agro_topic_cluster=p.intelligence.agro_topic_cluster if p.intelligence else None,
        )
        for p in rows
    ]


@router.post("/generate", response_model=GeneratedPostOut)
def generate(body: GenerateIn, db: Session = Depends(get_db)):
    post = (
        db.query(Post)
        .options(
            joinedload(Post.profile),
            joinedload(Post.intelligence),
            joinedload(Post.analysis),
        )
        .filter_by(id=body.post_id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if not post.intelligence:
        raise HTTPException(status_code=422, detail="Post sem análise de inteligência. Execute a análise de posts primeiro.")
    voice = (
        db.query(ProfileVoice)
        .join(Profile, ProfileVoice.profile_id == Profile.id)
        .filter(Profile.type == "own")
        .order_by(ProfileVoice.generated_at.desc())
        .first()
    )
    if not voice:
        raise HTTPException(status_code=404, detail="Perfil de voz não configurado. Execute /voice/analyze primeiro.")
    approved = (
        db.query(GeneratedPost)
        .filter_by(status="approved")
        .order_by(GeneratedPost.created_at.desc())
        .limit(3)
        .all()
    )
    try:
        generated = generate_post(source_post=post, voice=voice, approved_examples=approved, session=db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return GeneratedPostOut(
        id=generated.id,
        hook=generated.hook,
        caption=generated.caption,
        cta=generated.cta,
        slides=normalize_carousel_slides(generated.slides),
        funnel_stage=generated.funnel_stage,
        format=generated.format,
        created_at=generated.created_at,
    )
