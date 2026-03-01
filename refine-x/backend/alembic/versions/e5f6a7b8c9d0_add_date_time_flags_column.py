"""add date_time_flags column to cleaned_datasets

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-01 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add date_time_flags column for Session 5 Date & Time rules
    op.add_column('cleaned_datasets', sa.Column('date_time_flags', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('cleaned_datasets', 'date_time_flags')
