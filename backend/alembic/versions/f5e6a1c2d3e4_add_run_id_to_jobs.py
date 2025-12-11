"""add run_id to jobs

Revision ID: f5e6a1c2d3e4
Revises: 68b0e07075e7
Create Date: 2025-12-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5e6a1c2d3e4'
down_revision: Union[str, Sequence[str], None] = '68b0e07075e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('jobs', sa.Column('run_id', sa.String(), nullable=True, comment="上游工作流 runId"))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('jobs', 'run_id')

