# alembic/versions/011_evidence_inventory.py
"""add evidence_inventory to post_intelligence and source_data_inventory to generated_posts

Revision ID: 011
Revises: 010
Create Date: 2026-04-24 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "post_intelligence",
        sa.Column("evidence_inventory", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )
    op.add_column(
        "generated_posts",
        sa.Column("source_data_inventory", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )


def downgrade() -> None:
    op.drop_column("post_intelligence", "evidence_inventory")
    op.drop_column("generated_posts", "source_data_inventory")
