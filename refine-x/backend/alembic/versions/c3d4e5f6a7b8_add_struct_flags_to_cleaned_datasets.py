"""add struct_flags to cleaned_datasets

Revision ID: c3d4e5f6a7b8
Revises: b7d3e9f1c2a4
Create Date: 2026-03-01 00:01:00.000000

Adds:
  cleaned_datasets.struct_flags   JSON  nullable
"""
from alembic import op
import sqlalchemy as sa

revision = "c3d4e5f6a7b8"
down_revision = "b7d3e9f1c2a4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cleaned_datasets",
        sa.Column("struct_flags", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cleaned_datasets", "struct_flags")
