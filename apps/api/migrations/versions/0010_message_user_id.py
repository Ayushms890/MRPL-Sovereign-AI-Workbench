"""add_message_user_id

Revision ID: 0010_message_user_id
Revises: 0009_workspace_rbac
Create Date: 2026-07-26 12:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0010_message_user_id'
down_revision: Union[str, None] = '0009_workspace_rbac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    msg_cols = [c['name'] for c in inspector.get_columns('messages')]
    if 'user_id' not in msg_cols:
        op.add_column('messages', sa.Column('user_id', sa.String(length=36), sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True))


def downgrade() -> None:
    op.drop_column('messages', 'user_id')
