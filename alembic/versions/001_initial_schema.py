"""initial_schema

Revision ID: 001
Revises:
Create Date: 2026-04-14 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("handle", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("niche", sa.String(length=100), nullable=True),
        sa.Column("follower_count", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("handle"),
    )

    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("instagram_id", sa.String(length=100), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("hashtags", sa.JSON(), nullable=False),
        sa.Column("likes", sa.Integer(), nullable=False),
        sa.Column("comments", sa.Integer(), nullable=False),
        sa.Column("post_type", sa.String(length=20), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("instagram_id"),
    )

    op.create_table(
        "post_analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("visual_theme", sa.String(length=50), nullable=True),
        sa.Column("visual_format", sa.String(length=50), nullable=True),
        sa.Column("emotional_tone", sa.String(length=50), nullable=True),
        sa.Column("trigger", sa.String(length=50), nullable=True),
        sa.Column("virality_score", sa.Float(), nullable=True),
        sa.Column("raw_analysis", sa.JSON(), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id"),
    )

    op.create_table(
        "profile_voice",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("vocabulary", sa.JSON(), nullable=False),
        sa.Column("tone", sa.String(length=100), nullable=True),
        sa.Column("dominant_themes", sa.JSON(), nullable=False),
        sa.Column("competitor_comparison", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "weekly_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("top_formats", sa.JSON(), nullable=False),
        sa.Column("top_themes", sa.JSON(), nullable=False),
        sa.Column("language_patterns", sa.JSON(), nullable=False),
        sa.Column("top_hashtags", sa.JSON(), nullable=False),
        sa.Column("viral_posts", sa.JSON(), nullable=False),
        sa.Column("report_text", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "carousels",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("theme", sa.Text(), nullable=False),
        sa.Column("slides", sa.JSON(), nullable=False),
        sa.Column("based_on_reports", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("carousels")
    op.drop_table("weekly_reports")
    op.drop_table("profile_voice")
    op.drop_table("post_analyses")
    op.drop_table("posts")
    op.drop_table("profiles")
