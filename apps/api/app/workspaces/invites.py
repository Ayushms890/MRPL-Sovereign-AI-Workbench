from datetime import datetime, timedelta, timezone
import logging
import secrets
from typing import Any

import httpx
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.entities import WorkspaceInvite, WorkspaceMember
from app.infrastructure.models import WorkspaceInviteModel, WorkspaceModel, WorkspaceMemberModel, utc_now
from app.workspaces.repository import WorkspaceRepository

logger = logging.getLogger(__name__)


def create_invite(
    session: Session,
    workspace_id: str,
    email: str,
    role: str,
    invited_by: str,
) -> WorkspaceInvite:
    token = secrets.token_urlsafe(32)
    expires_at = utc_now() + timedelta(days=7)
    
    invite_id = f"inv_{secrets.token_hex(8)}"
    invite_model = WorkspaceInviteModel(
        id=invite_id,
        workspace_id=workspace_id,
        email=email.lower().strip(),
        role=role,
        token=token,
        invited_by=invited_by,
        status="pending",
        expires_at=expires_at,
        created_at=utc_now(),
    )
    session.add(invite_model)
    session.commit()
    session.refresh(invite_model)

    return _invite_to_entity(invite_model)


def get_invite_details(session: Session, token: str, user_id: str | None = None) -> dict[str, Any]:
    stmt = select(WorkspaceInviteModel).where(WorkspaceInviteModel.token == token)
    invite = session.scalar(stmt)
    if not invite:
        raise ValueError("Invalid or non-existent invite token")

    ws = session.get(WorkspaceModel, invite.workspace_id)
    ws_name = ws.name if ws else "Workspace"

    already_member = False
    user_role = None
    is_owner = False

    if user_id and ws:
        ws_repo = WorkspaceRepository(session)
        role = ws_repo.get_member_role(invite.workspace_id, user_id)
        if role:
            already_member = True
            user_role = role
            if ws.owner_id == user_id or role == "owner":
                is_owner = True

    return {
        "token": invite.token,
        "workspace_id": invite.workspace_id,
        "workspace_name": ws_name,
        "invited_email": invite.email,
        "role": invite.role,
        "status": invite.status,
        "already_member": already_member,
        "user_role": user_role,
        "is_owner": is_owner,
    }


def accept_invite(session: Session, token: str, user_id: str) -> WorkspaceMember:
    stmt = select(WorkspaceInviteModel).where(WorkspaceInviteModel.token == token)
    invite = session.scalar(stmt)
    if not invite:
        raise ValueError("Invalid or non-existent invite token")

    if invite.status != "pending":
        raise ValueError(f"Invite token is no longer valid (status: {invite.status})")

    # Check expiry
    now = utc_now()
    expires_at = invite.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        invite.status = "expired"
        session.commit()
        raise ValueError("Invite token has expired")

    # Add member via repository
    ws_repo = WorkspaceRepository(session)
    existing_role = ws_repo.get_member_role(invite.workspace_id, user_id)
    if existing_role:
        # Already a member, mark accepted
        invite.status = "accepted"
        session.commit()
        stmt_mem = select(WorkspaceMemberModel).where(
            and_(
                WorkspaceMemberModel.workspace_id == invite.workspace_id,
                WorkspaceMemberModel.user_id == user_id,
            )
        )
        mem = session.scalar(stmt_mem)
        return ws_repo._member_to_entity(mem)

    member = ws_repo.add_member(invite.workspace_id, user_id, invite.role)
    invite.status = "accepted"
    session.commit()
    return member





def _invite_to_entity(model: WorkspaceInviteModel) -> WorkspaceInvite:
    return WorkspaceInvite(
        id=model.id,
        workspace_id=model.workspace_id,
        email=model.email,
        role=model.role,
        token=model.token,
        invited_by=model.invited_by,
        status=model.status,
        expires_at=model.expires_at,
        created_at=model.created_at,
    )
