"""add_user_preferred_model

Revision ID: 0011_user_preferred_model
Revises: 0010_message_user_id
Create Date: 2026-08-31 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0011_user_preferred_model'
down_revision: Union[str, None] = '0010_message_user_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    user_cols = [c['name'] for c in inspector.get_columns('user')]
    if 'preferred_model' not in user_cols:
        op.add_column('user', sa.Column('preferred_model', sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column('user', 'preferred_model')
