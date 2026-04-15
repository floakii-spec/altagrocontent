# src/models.py
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    handle: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # competitor | own
    niche: Mapped[Optional[str]] = mapped_column(String(100))
    follower_count: Mapped[Optional[int]] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    posts: Mapped[list["Post"]] = relationship(back_populates="profile")
    voices: Mapped[list["ProfileVoice"]] = relationship(back_populates="profile")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), nullable=False)
    instagram_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    caption: Mapped[Optional[str]] = mapped_column(Text)
    hashtags: Mapped[list] = mapped_column(JSON, default=list)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    post_type: Mapped[str] = mapped_column(String(20))  # feed | reel | carousel
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    profile: Mapped["Profile"] = relationship(back_populates="posts")
    analysis: Mapped[Optional["PostAnalysis"]] = relationship(back_populates="post", uselist=False)


class PostAnalysis(Base):
    __tablename__ = "post_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), unique=True, nullable=False)
    visual_theme: Mapped[Optional[str]] = mapped_column(String(50))
    visual_format: Mapped[Optional[str]] = mapped_column(String(50))
    emotional_tone: Mapped[Optional[str]] = mapped_column(String(50))
    trigger: Mapped[Optional[str]] = mapped_column(String(50))
    virality_score: Mapped[Optional[float]] = mapped_column(Float)
    raw_analysis: Mapped[dict] = mapped_column(JSON, default=dict)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    post: Mapped["Post"] = relationship(back_populates="analysis")


class ProfileVoice(Base):
    __tablename__ = "profile_voice"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), nullable=False)
    vocabulary: Mapped[dict] = mapped_column(JSON, default=dict)
    tone: Mapped[Optional[str]] = mapped_column(String(100))
    dominant_themes: Mapped[list] = mapped_column(JSON, default=list)
    competitor_comparison: Mapped[dict] = mapped_column(JSON, default=dict)
    voice_summary: Mapped[Optional[str]] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    profile: Mapped["Profile"] = relationship(back_populates="voices")


class GeneratedPost(Base):
    __tablename__ = "generated_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), nullable=False)
    hook: Mapped[Optional[str]] = mapped_column(Text)
    caption: Mapped[Optional[str]] = mapped_column(Text)
    cta: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="generated")  # generated | approved | discarded
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    source_post: Mapped["Post"] = relationship()


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    top_formats: Mapped[dict] = mapped_column(JSON, default=dict)
    top_themes: Mapped[dict] = mapped_column(JSON, default=dict)
    language_patterns: Mapped[dict] = mapped_column(JSON, default=dict)
    top_hashtags: Mapped[list] = mapped_column(JSON, default=list)
    viral_posts: Mapped[list] = mapped_column(JSON, default=list)
    report_text: Mapped[Optional[str]] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Carousel(Base):
    __tablename__ = "carousels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    theme: Mapped[str] = mapped_column(Text, nullable=False)
    slides: Mapped[list] = mapped_column(JSON, default=list)
    based_on_reports: Mapped[list] = mapped_column(JSON, default=list)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
