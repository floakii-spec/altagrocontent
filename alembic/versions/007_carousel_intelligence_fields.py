"""add carousel intelligence fields

Revision ID: 007
Revises: 006
Create Date: 2026-04-22 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "post_intelligence",
        sa.Column("slide_breakdown", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )
    op.add_column(
        "post_intelligence",
        sa.Column("carousel_complexity", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )


def downgrade() -> None:
    op.drop_column("post_intelligence", "carousel_complexity")
    op.drop_column("post_intelligence", "slide_breakdown")
