"""add visual transcript to post intelligence

Revision ID: 009
Revises: 008
Create Date: 2026-04-23 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("post_intelligence", sa.Column("visual_transcript", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("post_intelligence", "visual_transcript")
