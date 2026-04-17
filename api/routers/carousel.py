from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.models import Carousel
from src.carousel.generator import generate_carousel
from api.deps import get_db

router = APIRouter(prefix="/carousel", tags=["carousel"])


class CarouselGenerateIn(BaseModel):
    theme: str


class CarouselOut(BaseModel):
    id: int
    theme: str
    slides: list
    generated_at: datetime


@router.get("", response_model=List[CarouselOut])
def list_carousels(db: Session = Depends(get_db)):
    rows = db.query(Carousel).order_by(Carousel.generated_at.desc()).limit(10).all()
    return [CarouselOut(id=r.id, theme=r.theme, slides=r.slides, generated_at=r.generated_at) for r in rows]


@router.post("/generate", response_model=CarouselOut)
def generate(body: CarouselGenerateIn, db: Session = Depends(get_db)):
    carousel = generate_carousel(theme=body.theme, session=db)
    return CarouselOut(id=carousel.id, theme=carousel.theme, slides=carousel.slides, generated_at=carousel.generated_at)
