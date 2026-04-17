from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.models import WeeklyReport
from src.reporter.weekly_report import generate_weekly_report
from api.deps import get_db

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportOut(BaseModel):
    id: int
    period_start: datetime
    period_end: datetime
    top_formats: Optional[dict]
    top_themes: Optional[dict]
    top_hashtags: Optional[list]
    language_patterns: Optional[dict]
    report_text: Optional[str]
    generated_at: datetime


@router.get("", response_model=List[ReportOut])
def list_reports(db: Session = Depends(get_db)):
    rows = db.query(WeeklyReport).order_by(WeeklyReport.period_start.desc()).all()
    return [
        ReportOut(
            id=r.id, period_start=r.period_start, period_end=r.period_end,
            top_formats=r.top_formats, top_themes=r.top_themes,
            top_hashtags=r.top_hashtags, language_patterns=r.language_patterns,
            report_text=r.report_text, generated_at=r.generated_at,
        )
        for r in rows
    ]


@router.post("/generate", response_model=ReportOut)
def generate_report(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=7)
    report = generate_weekly_report(db, period_start=period_start, period_end=now)
    return ReportOut(
        id=report.id, period_start=report.period_start, period_end=report.period_end,
        top_formats=report.top_formats, top_themes=report.top_themes,
        top_hashtags=report.top_hashtags, language_patterns=report.language_patterns,
        report_text=report.report_text, generated_at=report.generated_at,
    )
