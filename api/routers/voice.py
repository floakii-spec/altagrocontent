from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.models import Profile, ProfileVoice
from src.reporter.voice_profiler import generate_voice_profile
from api.deps import get_db

router = APIRouter(prefix="/voice", tags=["voice"])


class VoiceOut(BaseModel):
    id: int
    tone: Optional[str]
    dominant_themes: list
    vocabulary: dict
    competitor_comparison: dict
    voice_summary: Optional[str]
    generated_at: datetime


@router.get("", response_model=VoiceOut)
def get_voice(db: Session = Depends(get_db)):
    own = db.query(Profile).filter_by(type="own", active=True).first()
    if not own:
        raise HTTPException(status_code=404, detail="No own profile configured")
    voice = (
        db.query(ProfileVoice)
        .filter_by(profile_id=own.id)
        .order_by(ProfileVoice.generated_at.desc())
        .first()
    )
    if not voice:
        raise HTTPException(status_code=404, detail="Voice profile not generated yet")
    return VoiceOut(
        id=voice.id, tone=voice.tone, dominant_themes=voice.dominant_themes,
        vocabulary=voice.vocabulary, competitor_comparison=voice.competitor_comparison,
        voice_summary=voice.voice_summary, generated_at=voice.generated_at,
    )


@router.post("/analyze", response_model=VoiceOut)
def analyze_voice(db: Session = Depends(get_db)):
    from src.models import Post
    own = db.query(Profile).filter_by(type="own", active=True).first()
    if not own:
        raise HTTPException(status_code=404, detail="No own profile configured")
    post_count = db.query(Post).filter_by(profile_id=own.id).count()
    if post_count == 0:
        raise HTTPException(status_code=422, detail="Nenhum post coletado ainda. Colete posts na aba Concorrentes primeiro.")
    voice = generate_voice_profile(own, db)
    return VoiceOut(
        id=voice.id, tone=voice.tone, dominant_themes=voice.dominant_themes,
        vocabulary=voice.vocabulary, competitor_comparison=voice.competitor_comparison,
        voice_summary=voice.voice_summary, generated_at=voice.generated_at,
    )
