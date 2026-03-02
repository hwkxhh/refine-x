"""Add medical_flags column to cleaned_datasets

Revision ID: o5p6q7r8s9t0
Revises: n4o5p6q7r8s9
Create Date: 2025-01-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'o5p6q7r8s9t0'
down_revision: Union[str, None] = 'n4o5p6q7r8s9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add medical_flags column to store DIAG and PHYS validation results
    op.add_column('cleaned_datasets', sa.Column('medical_flags', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('cleaned_datasets', 'medical_flags')
