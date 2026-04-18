"""post_intelligence and argument_bank tables

Revision ID: 005
Revises: 004
Create Date: 2026-04-17 00:00:00.000000

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "post_intelligence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("posts.id"), unique=True, nullable=False),
        sa.Column("agro_topic_cluster", sa.String(50), nullable=True),
        sa.Column("agro_segment", sa.String(50), nullable=True),
        sa.Column("technical_depth", sa.String(20), nullable=True),
        sa.Column("core_argument", sa.Text(), nullable=True),
        sa.Column("argument_structure", sa.Text(), nullable=True),
        sa.Column("technical_claims", sa.JSON(), nullable=False, server_default="'[]'"),
        sa.Column("data_points", sa.JSON(), nullable=False, server_default="'[]'"),
        sa.Column("sources_referenced", sa.JSON(), nullable=False, server_default="'[]'"),
        sa.Column("knowledge_assumptions", sa.Text(), nullable=True),
        sa.Column("content_gaps", sa.Text(), nullable=True),
        sa.Column("replication_template", sa.Text(), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "argument_bank",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("topic_cluster", sa.String(50), nullable=True),
        sa.Column("agro_segment", sa.String(50), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("virality_weight", sa.Float(), nullable=False),
        sa.Column("source_post_ids", sa.JSON(), nullable=False, server_default="'[]'"),
        sa.Column("times_seen", sa.Integer(), nullable=False),
        sa.Column("origin", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("text", name="uq_argument_bank_text"),
    )


def downgrade() -> None:
    op.drop_table("argument_bank")
    op.drop_table("post_intelligence")
