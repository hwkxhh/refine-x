"""Add personal_identity_flags to cleaned_datasets

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2025-01-15 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add personal_identity_flags column for Session 4 outputs
    op.add_column(
        'cleaned_datasets',
        sa.Column('personal_identity_flags', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('cleaned_datasets', 'personal_identity_flags')
