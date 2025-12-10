"""add status to videos

Revision ID: a1b2c3d4e5f6
Revises: 83ab30652ad1
Create Date: 2025-12-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '83ab30652ad1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 因为 SQLite 不支持为已有行添加 NOT NULL 且无默认值的列，
    # 这里先创建可为空的列，填充默认值后再（概念上）视为非空。
    # 某些开发环境中该列可能已经存在，这里加检查避免重复添加。
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col["name"] for col in inspector.get_columns("videos")]
    if "status" not in columns:
        op.add_column(
            "videos",
            sa.Column("status", sa.String(), nullable=True, server_default="uploading", comment="状态: uploading/ready/failed"),
        )
        # 为现有行设置默认值
        op.execute("UPDATE videos SET status = 'uploading' WHERE status IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("videos", "status")

