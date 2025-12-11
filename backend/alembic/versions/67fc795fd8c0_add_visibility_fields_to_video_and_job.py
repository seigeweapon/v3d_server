"""add_visibility_fields_to_video_and_job

Revision ID: 67fc795fd8c0
Revises: 68b0e07075e7
Create Date: 2025-12-11 15:55:57.356592

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67fc795fd8c0'
down_revision: Union[str, Sequence[str], None] = '68b0e07075e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 在 videos 表中添加可见性字段
    op.add_column('videos', sa.Column('is_public', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('videos', sa.Column('visible_to_user_ids', sa.Text(), nullable=True))
    
    # 在 jobs 表中添加可见性字段
    op.add_column('jobs', sa.Column('is_public', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('jobs', sa.Column('visible_to_user_ids', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # 移除 jobs 表的可见性字段
    op.drop_column('jobs', 'visible_to_user_ids')
    op.drop_column('jobs', 'is_public')
    
    # 移除 videos 表的可见性字段
    op.drop_column('videos', 'visible_to_user_ids')
    op.drop_column('videos', 'is_public')
