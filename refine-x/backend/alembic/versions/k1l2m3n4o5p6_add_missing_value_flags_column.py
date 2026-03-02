"""Add missing_value_flags column to cleaned_datasets

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-03-02

Session 12: Missing Value Decision Matrix
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'k1l2m3n4o5p6'
down_revision = 'j0k1l2m3n4o5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('cleaned_datasets', sa.Column('missing_value_flags', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('cleaned_datasets', 'missing_value_flags')
