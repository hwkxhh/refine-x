"""add is_ai_generated and model_name to insights

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-06 00:00:00.000000

Adds:
  insights.is_ai_generated  Boolean  nullable  (True = GPT, False = statistical fallback)
  insights.model_name       String   nullable  ("gpt-4o" | "statistical_fallback")
"""
from alembic import op
import sqlalchemy as sa

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "insights",
        sa.Column("is_ai_generated", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "insights",
        sa.Column("model_name", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("insights", "model_name")
    op.drop_column("insights", "is_ai_generated")
