"""Add boolean_category_flags column

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-03-01

Session 8: Boolean, Category & Status Rules
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'h8i9j0k1l2m3'
down_revision = 'g7h8i9j0k1l2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('cleaned_datasets', sa.Column(
        'boolean_category_flags',
        sa.JSON(),
        nullable=True,
        comment='Flags from Boolean, Category, Status, Survey & Multi-Value cleaning (Session 8)'
    ))


def downgrade() -> None:
    op.drop_column('cleaned_datasets', 'boolean_category_flags')
