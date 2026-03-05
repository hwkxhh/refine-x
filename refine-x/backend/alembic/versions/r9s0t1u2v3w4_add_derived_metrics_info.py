"""add derived_metrics_info to cleaned_datasets

Revision ID: r9s0t1u2v3w4
Revises: q8r9s0t1u2v3
Create Date: 2026-03-05
"""
from alembic import op
import sqlalchemy as sa

revision = "r9s0t1u2v3w4"
down_revision = "q8r9s0t1u2v3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cleaned_datasets",
        sa.Column("derived_metrics_info", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cleaned_datasets", "derived_metrics_info")
