"""add formula_id global_flags pii_tags htype_map

Revision ID: b7d3e9f1c2a4
Revises: 1f4b0266dfbd
Create Date: 2026-03-01 00:00:00.000000

Adds:
  cleaning_logs.formula_id          VARCHAR  nullable
  cleaning_logs.was_auto_applied    BOOLEAN  nullable default True
  cleaned_datasets.global_flags     JSON     nullable
  cleaned_datasets.htype_map        JSON     nullable
  cleaned_datasets.pii_tags         JSON     nullable
"""
from alembic import op
import sqlalchemy as sa

revision = "b7d3e9f1c2a4"
down_revision = "1f4b0266dfbd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── cleaning_logs ────────────────────────────────────────────────
    op.add_column(
        "cleaning_logs",
        sa.Column("formula_id", sa.String(), nullable=True),
    )
    op.add_column(
        "cleaning_logs",
        sa.Column("was_auto_applied", sa.Boolean(), nullable=True, server_default=sa.true()),
    )
    op.create_index(
        "ix_cleaning_logs_formula_id",
        "cleaning_logs",
        ["formula_id"],
        unique=False,
    )

    # ── cleaned_datasets ─────────────────────────────────────────────
    op.add_column(
        "cleaned_datasets",
        sa.Column("global_flags", sa.JSON(), nullable=True),
    )
    op.add_column(
        "cleaned_datasets",
        sa.Column("htype_map", sa.JSON(), nullable=True),
    )
    op.add_column(
        "cleaned_datasets",
        sa.Column("pii_tags", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_index("ix_cleaning_logs_formula_id", table_name="cleaning_logs")
    op.drop_column("cleaning_logs", "was_auto_applied")
    op.drop_column("cleaning_logs", "formula_id")
    op.drop_column("cleaned_datasets", "pii_tags")
    op.drop_column("cleaned_datasets", "htype_map")
    op.drop_column("cleaned_datasets", "global_flags")
