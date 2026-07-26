import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.workspaces.invites import create_invite


def sanitize_next_url(raw_next: str | None) -> str:
    """Python reference implementation matching frontend sanitizeNextUrl."""
    if not raw_next:
        return "/chat"
    trimmed = raw_next.strip()
    if (
        trimmed.startswith("/")
        and not trimmed.startswith("//")
        and not trimmed.startswith("/\\")
        and ":" not in trimmed
    ):
        return trimmed
    return "/chat"


def test_sanitize_next_url_open_redirect_protection() -> None:
    # Valid relative paths
    assert sanitize_next_url("/join/token123") == "/join/token123"
    assert sanitize_next_url("/chat/conv-123") == "/chat/conv-123"
    assert sanitize_next_url(None) == "/chat"
    assert sanitize_next_url("") == "/chat"

    # Malicious open-redirect attempts MUST fall back to /chat
    assert sanitize_next_url("https://evil.com") == "/chat"
    assert sanitize_next_url("http://evil.com/login") == "/chat"
    assert sanitize_next_url("//evil.com") == "/chat"
    assert sanitize_next_url("/\\evil.com") == "/chat"
    assert sanitize_next_url("javascript:alert(1)") == "/chat"


def test_create_invite_and_inspect_details(db_session: Session) -> None:
    from app.auth.repository import UserRepository
    from app.workspaces.repository import WorkspaceRepository
    from app.workspaces.invites import get_invite_details

    user_repo = UserRepository(db_session)
    owner = user_repo.create_user_with_password("owner_invite@example.com", "pw123456", "Owner")

    ws_repo = WorkspaceRepository(db_session)
    ws = ws_repo.create("Test Ws", owner.id)

    invite_entity = create_invite(
        session=db_session,
        workspace_id=ws.id,
        email="invitee@example.com",
        role="member",
        invited_by=owner.id,
    )

    assert invite_entity.email == "invitee@example.com"
    assert invite_entity.role == "member"
    assert invite_entity.token is not None

    # Inspect invite details
    details = get_invite_details(db_session, invite_entity.token, owner.id)
    assert details["workspace_name"] == "Test Ws"
    assert details["already_member"] is True
    assert details["is_owner"] is True
