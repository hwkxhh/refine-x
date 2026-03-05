"""Add reason column to charts table

Revision ID: q8r9s0t1u2v3
Revises: p7q8r9s0t1u2
Create Date: 2026-03-05 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "q8r9s0t1u2v3"
down_revision = "d67eafa7ec62"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("charts", sa.Column("reason", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("charts", "reason")
