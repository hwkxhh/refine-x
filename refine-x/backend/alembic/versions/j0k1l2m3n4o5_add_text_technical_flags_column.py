"""Add text_technical_flags column

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2025-01-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'j0k1l2m3n4o5'
down_revision: Union[str, None] = 'i9j0k1l2m3n4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('cleaned_datasets', 
                  sa.Column('text_technical_flags', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('cleaned_datasets', 'text_technical_flags')
