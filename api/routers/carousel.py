from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from src.models import Carousel, CarouselSuggestion
from src.carousel.generator import generate_carousel
from src.carousel.theme_suggester import generate_theme_suggestions
from api.deps import get_db
from src.slide_utils import normalize_carousel_slides

router = APIRouter(prefix="/carousel", tags=["carousel"])


class CarouselGenerateIn(BaseModel):
    theme: str


class SlideOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    slide_number: int
    slide_type: str
    title: str
    body: str = Field(alias="copy", serialization_alias="copy")
    cta: str


class CarouselOut(BaseModel):
    id: int
    theme: str
    slides: List[SlideOut]
    generated_at: datetime


class SuggestionItem(BaseModel):
    title: str
    rationale: str


class CarouselSuggestionOut(BaseModel):
    id: int
    themes: List[SuggestionItem]
    generated_at: datetime


@router.get("", response_model=List[CarouselOut])
def list_carousels(db: Session = Depends(get_db)):
    rows = db.query(Carousel).order_by(Carousel.generated_at.desc()).limit(10).all()
    return [
        CarouselOut(
            id=r.id,
            theme=r.theme,
            slides=normalize_carousel_slides(r.slides),
            generated_at=r.generated_at,
        )
        for r in rows
    ]


@router.post("/generate", response_model=CarouselOut)
def generate(body: CarouselGenerateIn, db: Session = Depends(get_db)):
    carousel = generate_carousel(theme=body.theme, session=db)
    return CarouselOut(
        id=carousel.id,
        theme=carousel.theme,
        slides=normalize_carousel_slides(carousel.slides),
        generated_at=carousel.generated_at,
    )


@router.get("/suggestions")
def get_suggestions(db: Session = Depends(get_db), response: Response = None):
    row = db.query(CarouselSuggestion).order_by(CarouselSuggestion.generated_at.desc()).first()
    if not row:
        response.status_code = 204
        return None
    return CarouselSuggestionOut(id=row.id, themes=row.themes, generated_at=row.generated_at)


@router.post("/suggestions/refresh", response_model=CarouselSuggestionOut)
def refresh_suggestions(db: Session = Depends(get_db)):
    row = generate_theme_suggestions(db)
    return CarouselSuggestionOut(id=row.id, themes=row.themes, generated_at=row.generated_at)
