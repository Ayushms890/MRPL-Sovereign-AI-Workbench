"""add_workspace_rbac_schema

Revision ID: 0009_workspace_rbac
Revises: 0008_custom_jwt_auth
Create Date: 2026-07-26 07:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0009_workspace_rbac'
down_revision: Union[str, None] = '0008_custom_jwt_auth'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "workspaces" not in tables:
        op.execute("""
            CREATE TABLE workspaces (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                owner_id TEXT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        """)

    if "workspace_members" not in tables:
        op.execute("""
            CREATE TABLE workspace_members (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                user_id TEXT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK (role IN ('owner', 'member', 'viewer')),
                joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                UNIQUE (workspace_id, user_id)
            );
        """)

    if "workspace_invites" not in tables:
        op.execute("""
            CREATE TABLE workspace_invites (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                email TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('member', 'viewer')),
                token TEXT NOT NULL UNIQUE,
                invited_by TEXT NOT NULL REFERENCES "user"(id),
                status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'expired', 'revoked')),
                expires_at TIMESTAMPTZ NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        """)

    conv_cols = [c['name'] for c in inspector.get_columns('conversations')]
    if 'workspace_id' not in conv_cols:
        op.add_column('conversations', sa.Column('workspace_id', sa.Text(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True))

    doc_cols = [c['name'] for c in inspector.get_columns('documents')]
    if 'workspace_id' not in doc_cols:
        op.add_column('documents', sa.Column('workspace_id', sa.Text(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True))

    # Data migration: create personal workspace for every existing user and backfill workspace_id
    op.execute("""
        DO $$
        DECLARE
            u RECORD;
            ws_id TEXT;
            mem_id TEXT;
        BEGIN
            FOR u IN SELECT id, email FROM "user" LOOP
                SELECT id INTO ws_id FROM workspaces WHERE owner_id = u.id LIMIT 1;
                IF ws_id IS NULL THEN
                    ws_id := md5(random()::text || clock_timestamp()::text);
                    mem_id := md5(random()::text || clock_timestamp()::text);
                    INSERT INTO workspaces (id, name, owner_id, created_at)
                    VALUES (ws_id, COALESCE(u.email, 'Personal'), u.id, now());

                    INSERT INTO workspace_members (id, workspace_id, user_id, role, joined_at)
                    VALUES (mem_id, ws_id, u.id, 'owner', now());
                END IF;

                UPDATE conversations SET workspace_id = ws_id WHERE user_id = u.id AND workspace_id IS NULL;
                UPDATE documents SET workspace_id = ws_id WHERE user_id = u.id AND workspace_id IS NULL;
            END LOOP;
        END $$;
    """)


def downgrade() -> None:
    op.drop_column('documents', 'workspace_id')
    op.drop_column('conversations', 'workspace_id')
    op.drop_table('workspace_invites')
    op.drop_table('workspace_members')
    op.drop_table('workspaces')
