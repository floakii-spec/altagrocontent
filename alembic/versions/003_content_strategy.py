"""content_strategy_engine

Revision ID: 003
Revises: 002
Create Date: 2026-04-17 00:00:00.000000

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extend posts
    op.add_column("posts", sa.Column("slides", sa.JSON(), nullable=True))

    # Extend post_analyses
    op.add_column("post_analyses", sa.Column("carousel_narrative", sa.JSON(), nullable=True))

    # Extend generated_posts
    op.add_column("generated_posts", sa.Column("funnel_stage", sa.String(length=20), nullable=True))
    op.add_column("generated_posts", sa.Column("format", sa.String(length=20), nullable=True))
    op.add_column("generated_posts", sa.Column("hook_variations", sa.JSON(), nullable=True))
    op.add_column("generated_posts", sa.Column("news_item_ids", sa.JSON(), nullable=True))

    # New tables
    op.create_table(
        "news_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )

    op.create_table(
        "content_calendars",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("week_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("entries", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("content_calendars")
    op.drop_table("news_items")
    op.drop_column("generated_posts", "news_item_ids")
    op.drop_column("generated_posts", "hook_variations")
    op.drop_column("generated_posts", "format")
    op.drop_column("generated_posts", "funnel_stage")
    op.drop_column("post_analyses", "carousel_narrative")
    op.drop_column("posts", "slides")
