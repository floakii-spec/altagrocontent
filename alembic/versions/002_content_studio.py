"""content_studio

Revision ID: 002
Revises: a1b2c3d4e5f6
Create Date: 2026-04-15 00:00:00.000000

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("profile_voice", sa.Column("voice_summary", sa.Text(), nullable=True))

    op.create_table(
        "generated_posts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_post_id", sa.Integer(), nullable=False),
        sa.Column("hook", sa.Text(), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("cta", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_post_id"], ["posts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("generated_posts")
    op.drop_column("profile_voice", "voice_summary")
