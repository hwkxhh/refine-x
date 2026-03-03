"""Add column_relevance_result and confirmed_columns to upload_jobs

Revision ID: p7q8r9s0t1u2
Revises: o5p6q7r8s9t0
Create Date: 2026-03-03 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "p7q8r9s0t1u2"
down_revision = "o5p6q7r8s9t0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("upload_jobs", sa.Column("column_relevance_result", sa.JSON(), nullable=True))
    op.add_column("upload_jobs", sa.Column("confirmed_columns", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("upload_jobs", "confirmed_columns")
    op.drop_column("upload_jobs", "column_relevance_result")
