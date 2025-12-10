"""drop backgrounds and calibrations tables

Revision ID: d1e2f3a4b5c6
Revises: a1b2c3d4e5f6
Create Date: 2025-12-10 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 检查表是否存在，如果存在则删除
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()
    
    # 删除 backgrounds 表
    if 'backgrounds' in existing_tables:
        # 先删除索引
        try:
            op.drop_index(op.f('ix_backgrounds_id'), table_name='backgrounds')
        except Exception:
            pass  # 索引可能不存在
        op.drop_table('backgrounds')
    
    # 删除 calibrations 表
    if 'calibrations' in existing_tables:
        # 先删除索引
        try:
            op.drop_index(op.f('ix_calibrations_id'), table_name='calibrations')
        except Exception:
            pass  # 索引可能不存在
        op.drop_table('calibrations')


def downgrade() -> None:
    """Downgrade schema."""
    # 重新创建 backgrounds 表
    op.create_table(
        'backgrounds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('camera_count', sa.Integer(), nullable=False),
        sa.Column('tos_path', sa.String(), nullable=False),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='uploading'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_backgrounds_id'), 'backgrounds', ['id'], unique=False)
    
    # 重新创建 calibrations 表
    op.create_table(
        'calibrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('camera_count', sa.Integer(), nullable=False),
        sa.Column('tos_path', sa.String(), nullable=False),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calibrations_id'), 'calibrations', ['id'], unique=False)

