from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_current_user_optional, require_workspace_role
from app.api.schemas import (
    WorkspaceCreateRequest,
    WorkspaceInviteDetailsResponse,
    WorkspaceInviteRequest,
    WorkspaceInviteResponse,
    WorkspaceMemberResponse,
    WorkspaceMemberUpdateRequest,
    WorkspaceResponse,
)
from app.db import get_db_session
from app.domain.entities import User
from app.workspaces.invites import accept_invite, create_invite, get_invite_details
from app.workspaces.repository import WorkspaceRepository

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    payload: WorkspaceCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
) -> WorkspaceResponse:
    ws_repo = WorkspaceRepository(session)
    ws = ws_repo.create(name=payload.name.strip(), owner_id=current_user.id)
    return WorkspaceResponse(
        id=ws.id,
        name=ws.name,
        owner_id=ws.owner_id,
        created_at=ws.created_at,
        my_role="owner",
    )


@router.get("", response_model=list[WorkspaceResponse])
def list_workspaces(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
) -> list[WorkspaceResponse]:
    ws_repo = WorkspaceRepository(session)
    workspaces = ws_repo.get_for_user(current_user.id)
    res = []
    for ws in workspaces:
        role = ws_repo.get_member_role(ws.id, current_user.id)
        res.append(
            WorkspaceResponse(
                id=ws.id,
                name=ws.name,
                owner_id=ws.owner_id,
                created_at=ws.created_at,
                my_role=role,
            )
        )
    return res


@router.post("/{id}/invites", response_model=WorkspaceInviteResponse, status_code=status.HTTP_201_CREATED)
def invite_to_workspace(
    id: str,
    payload: WorkspaceInviteRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
    _: Annotated[str, Depends(require_workspace_role("owner"))],
) -> WorkspaceInviteResponse:
    invite = create_invite(
        session=session,
        workspace_id=id,
        email=payload.email,
        role=payload.role,
        invited_by=current_user.id,
    )
    return WorkspaceInviteResponse(
        id=invite.id,
        workspace_id=invite.workspace_id,
        email=invite.email,
        role=invite.role,
        token=invite.token,
        status=invite.status,
        expires_at=invite.expires_at,
        created_at=invite.created_at,
    )


@router.get("/invites/{token}", response_model=WorkspaceInviteDetailsResponse)
def inspect_workspace_invite(
    token: str,
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> WorkspaceInviteDetailsResponse:
    try:
        user_id = current_user.id if current_user else None
        details = get_invite_details(session=session, token=token, user_id=user_id)
        return WorkspaceInviteDetailsResponse(**details)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post("/invites/{token}/accept", response_model=WorkspaceMemberResponse)
def accept_workspace_invite(
    token: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
) -> WorkspaceMemberResponse:
    try:
        member = accept_invite(session=session, token=token, user_id=current_user.id)
        return WorkspaceMemberResponse(
            user_id=current_user.id,
            email=current_user.email,
            name=current_user.name,
            role=member.role,
            joined_at=member.joined_at,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete("/{id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_workspace(
    id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
) -> None:
    ws_repo = WorkspaceRepository(session)
    ws = ws_repo.get_by_id(id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    if ws.owner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace owner cannot leave their workspace. Delete workspace or transfer ownership instead.",
        )

    success = ws_repo.remove_member(id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are not a member of this workspace")


@router.get("/{id}/members", response_model=list[WorkspaceMemberResponse])
def list_workspace_members(
    id: str,
    session: Annotated[Session, Depends(get_db_session)],
    _: Annotated[str, Depends(require_workspace_role("owner", "member", "viewer"))],
) -> list[WorkspaceMemberResponse]:
    ws_repo = WorkspaceRepository(session)
    members_with_users = ws_repo.list_members(id)
    return [
        WorkspaceMemberResponse(
            user_id=u.id,
            email=u.email,
            name=u.name,
            role=mem.role,
            joined_at=mem.joined_at,
        )
        for mem, u in members_with_users
    ]


@router.delete("/{id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_workspace_member(
    id: str,
    user_id: str,
    session: Annotated[Session, Depends(get_db_session)],
    _: Annotated[str, Depends(require_workspace_role("owner"))],
) -> None:
    ws_repo = WorkspaceRepository(session)
    ws = ws_repo.get_by_id(id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    if user_id == ws.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the workspace owner without transferring ownership first",
        )

    success = ws_repo.remove_member(id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")


@router.patch("/{id}/members/{user_id}", response_model=WorkspaceMemberResponse)
def update_workspace_member_role(
    id: str,
    user_id: str,
    payload: WorkspaceMemberUpdateRequest,
    session: Annotated[Session, Depends(get_db_session)],
    _: Annotated[str, Depends(require_workspace_role("owner"))],
) -> WorkspaceMemberResponse:
    ws_repo = WorkspaceRepository(session)
    ws = ws_repo.get_by_id(id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    if user_id == ws.owner_id and payload.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote the workspace owner without transferring ownership first",
        )

    updated_mem = ws_repo.update_member_role(id, user_id, payload.role)
    if not updated_mem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    # Load user
    from app.auth.repository import UserRepository
    u = UserRepository(session).get_by_id(user_id)
    return WorkspaceMemberResponse(
        user_id=user_id,
        email=u.email if u else "",
        name=u.name if u else "",
        role=updated_mem.role,
        joined_at=updated_mem.joined_at,
    )
