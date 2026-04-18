"""fix profile_voice tone column from VARCHAR(100) to TEXT

Revision ID: 006
Revises: 005
Create Date: 2026-04-18 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "profile_voice",
        "tone",
        type_=sa.Text(),
        existing_type=sa.String(100),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        "profile_voice",
        "tone",
        type_=sa.String(100),
        existing_type=sa.Text(),
        existing_nullable=True,
    )
