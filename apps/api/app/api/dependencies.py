from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.auth.repository import UserRepository
from app.db import get_db_session
from app.domain.entities import User


import logging

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[Session, Depends(get_db_session)],
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing sub claim")
    except Exception as exc:
        logger.error(f"JWT token verification failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
        ) from exc

    user = UserRepository(session).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[Session, Depends(get_db_session)],
) -> User | None:
    if credentials is None:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        return UserRepository(session).get_by_id(user_id)
    except Exception:
        return None


def require_workspace_role(*allowed_roles: str):
    from fastapi import Request
    from app.workspaces.repository import WorkspaceRepository
    from app.conversations.repository import ConversationRepository
    from app.retrieval.repository import RetrievalRepository

    def dependency(
        request: Request,
        current_user: Annotated[User, Depends(get_current_user)],
        session: Annotated[Session, Depends(get_db_session)],
    ) -> str:
        workspace_id: str | None = None
        path_params = request.path_params
        query_params = request.query_params

        if "workspace_id" in path_params:
            workspace_id = path_params["workspace_id"]
        elif "id" in path_params and "/workspaces/" in request.url.path:
            workspace_id = path_params["id"]
        elif "workspace_id" in query_params:
            workspace_id = query_params["workspace_id"]
        elif "conversation_id" in path_params:
            conv_id = path_params["conversation_id"]
            conv = ConversationRepository(session).get_by_id(conv_id)
            if not conv:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
            workspace_id = conv.workspace_id
        elif "document_id" in path_params:
            doc_id = path_params["document_id"]
            doc = RetrievalRepository(session).get_document(doc_id)
            if not doc:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
            workspace_id = doc.workspace_id

        ws_repo = WorkspaceRepository(session)
        if not workspace_id:
            personal_ws = ws_repo.get_personal_workspace(current_user.id)
            if personal_ws:
                workspace_id = personal_ws.id
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing workspace context")

        member_role = ws_repo.get_member_role(workspace_id, current_user.id)
        if not member_role:
            # Not a member or workspace doesn't exist — return 404 to avoid leaking existence
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        if member_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{member_role}' lacks required permissions for this action",
            )

        return workspace_id

    return dependency

