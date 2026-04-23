import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import case
from sqlalchemy.orm import Session, joinedload

from api.deps import get_db
from src.models import ArgumentBank, Post, PostIntelligence, Profile
from src.workflows.intelligence_jobs import (
    create_analysis_job,
    get_analysis_job,
    intelligence_analysis_workflow,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/intelligence", tags=["intelligence"])


class PostIntelligenceOut(BaseModel):
    post_id: int
    handle: str
    profile_type: str
    post_type: str
    likes: int
    virality_score: Optional[float]
    slides_count: int
    agro_topic_cluster: Optional[str]
    agro_segment: Optional[str]
    technical_depth: Optional[str]
    core_argument: Optional[str]
    argument_structure: Optional[str]
    technical_claims: list
    data_points: list
    sources_referenced: list
    knowledge_assumptions: Optional[str]
    content_gaps: Optional[str]
    replication_template: Optional[str]
    slide_breakdown: list
    carousel_complexity: dict
    analyzed_at: datetime


class ArgumentBankOut(BaseModel):
    id: int
    text: str
    topic_cluster: Optional[str]
    agro_segment: Optional[str]
    quality_score: float
    virality_weight: float
    times_seen: int
    source_post_count: int
    origin: str


class AnalyzeResponse(BaseModel):
    processed: int


class LiveAnalyzeJobIn(BaseModel):
    handle: Optional[str] = None
    force: bool = False
    sync_before: bool = False
    limit: int = 50


class AnalyzeJobOut(BaseModel):
    job_id: str
    status: str
    phase: str
    handle: Optional[str]
    force: bool
    sync_before: bool
    limit: int
    message: str
    phase_total: int
    phase_completed: int
    total_profiles: int
    completed_profiles: int
    total_posts: int
    completed_posts: int
    successful_posts: int
    failed_posts: int
    current_handle: Optional[str]
    current_post_id: Optional[int]
    errors: list[str]
    started_at: Optional[datetime]
    updated_at: datetime
    finished_at: Optional[datetime]


def _intel_to_out(intel: PostIntelligence) -> PostIntelligenceOut:
    post = intel.post
    return PostIntelligenceOut(
        post_id=post.id,
        handle=post.profile.handle,
        profile_type=post.profile.type,
        post_type=post.post_type,
        likes=post.likes,
        virality_score=post.analysis.virality_score if post.analysis else None,
        slides_count=len(post.slides or []),
        agro_topic_cluster=intel.agro_topic_cluster,
        agro_segment=intel.agro_segment,
        technical_depth=intel.technical_depth,
        core_argument=intel.core_argument,
        argument_structure=intel.argument_structure,
        technical_claims=intel.technical_claims or [],
        data_points=intel.data_points or [],
        sources_referenced=intel.sources_referenced or [],
        knowledge_assumptions=intel.knowledge_assumptions,
        content_gaps=intel.content_gaps,
        replication_template=intel.replication_template,
        slide_breakdown=intel.slide_breakdown or [],
        carousel_complexity=intel.carousel_complexity or {},
        analyzed_at=intel.analyzed_at,
    )


@router.get("/posts", response_model=List[PostIntelligenceOut])
def list_intelligence(
    page: int = Query(1, ge=1),
    handle: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * 20
    q = (
        db.query(PostIntelligence)
        .join(PostIntelligence.post)
        .join(Post.profile)
        .options(
            joinedload(PostIntelligence.post).joinedload(Post.profile),
            joinedload(PostIntelligence.post).joinedload(Post.analysis),
        )
        .order_by(
            case(
                (Profile.type == "competitor", 0),
                (Profile.type == "own", 1),
                else_=2,
            ),
            PostIntelligence.analyzed_at.desc(),
        )
    )
    if handle:
        q = q.filter(Profile.handle == handle)
    rows = q.offset(offset).limit(20).all()
    return [_intel_to_out(r) for r in rows]


@router.get("/posts/{post_id}", response_model=PostIntelligenceOut)
def get_intelligence(post_id: int, db: Session = Depends(get_db)):
    intel = (
        db.query(PostIntelligence)
        .options(
            joinedload(PostIntelligence.post).joinedload(Post.profile),
            joinedload(PostIntelligence.post).joinedload(Post.analysis),
        )
        .filter_by(post_id=post_id)
        .first()
    )
    if not intel:
        raise HTTPException(status_code=404, detail="Not analyzed yet")
    return _intel_to_out(intel)


@router.get("/arguments", response_model=List[ArgumentBankOut])
def list_arguments(
    topic_cluster: Optional[str] = Query(None),
    agro_segment: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(ArgumentBank)
    if topic_cluster:
        q = q.filter(ArgumentBank.topic_cluster == topic_cluster)
    if agro_segment:
        q = q.filter(ArgumentBank.agro_segment == agro_segment)
    rows = q.order_by(
        (ArgumentBank.virality_weight * ArgumentBank.quality_score).desc()
    ).limit(100).all()
    return [
        ArgumentBankOut(
            id=r.id,
            text=r.text,
            topic_cluster=r.topic_cluster,
            agro_segment=r.agro_segment,
            quality_score=r.quality_score,
            virality_weight=r.virality_weight,
            times_seen=r.times_seen,
            source_post_count=len(r.source_post_ids or []),
            origin=r.origin,
        )
        for r in rows
    ]


@router.post("/analyze", response_model=AnalyzeResponse)
def trigger_analysis(
    handle: Optional[str] = Query(None),
    force: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    result = intelligence_analysis_workflow(db, handle=handle, force=force, limit=limit)
    return AnalyzeResponse(processed=result["processed"])


@router.post("/jobs", response_model=AnalyzeJobOut, status_code=202)
def start_analysis_job(body: LiveAnalyzeJobIn):
    return AnalyzeJobOut(**create_analysis_job(
        handle=body.handle,
        force=body.force,
        sync_before=body.sync_before,
        limit=body.limit,
    ))


@router.get("/jobs/{job_id}", response_model=AnalyzeJobOut)
def get_analysis_job_status(job_id: str):
    job = get_analysis_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return AnalyzeJobOut(**job)
