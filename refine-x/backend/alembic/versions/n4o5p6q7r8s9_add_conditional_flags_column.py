"""Add conditional_flags column to cleaned_datasets

Revision ID: n4o5p6q7r8s9
Revises: m3n4o5p6q7r8
Create Date: 2025-01-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'n4o5p6q7r8s9'
down_revision: Union[str, None] = 'm3n4o5p6q7r8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add conditional_flags column to store cross-column validation results
    op.add_column('cleaned_datasets', sa.Column('conditional_flags', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('cleaned_datasets', 'conditional_flags')
