from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.security import create_access_token
from app.auth.repository import UserRepository
from app.infrastructure.models import WorkspaceInviteModel, utc_now
from app.workspaces.repository import WorkspaceRepository


def create_user(db_session: Session, email: str, name: str) -> tuple[str, str]:
    repo = UserRepository(db_session)
    user = repo.create_user_with_password(email, "hashed_pw", name)
    token = create_access_token({"sub": user.id, "email": user.email})
    return user.id, token


def test_workspace_creation_and_listing(client: TestClient, db_session: Session):
    user_id, token = create_user(db_session, "owner1@example.com", "Owner 1")
    headers = {"Authorization": f"Bearer {token}"}

    # Verify auto-created personal workspace on signup
    res_list = client.get("/workspaces", headers=headers)
    assert res_list.status_code == 200
    data = res_list.json()
    assert len(data) >= 1
    assert data[0]["my_role"] == "owner"

    # Create a custom workspace
    res_create = client.post("/workspaces", json={"name": "Engineering Team"}, headers=headers)
    assert res_create.status_code == 201
    ws = res_create.json()
    assert ws["name"] == "Engineering Team"
    assert ws["my_role"] == "owner"


def test_workspace_rbac_authorization_matrix(client: TestClient, db_session: Session):
    owner_id, owner_token = create_user(db_session, "owner_matrix@example.com", "Owner Matrix")
    member_id, member_token = create_user(db_session, "member_matrix@example.com", "Member Matrix")
    viewer_id, viewer_token = create_user(db_session, "viewer_matrix@example.com", "Viewer Matrix")
    stranger_id, stranger_token = create_user(db_session, "stranger_matrix@example.com", "Stranger Matrix")

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    member_headers = {"Authorization": f"Bearer {member_token}"}
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
    stranger_headers = {"Authorization": f"Bearer {stranger_token}"}

    # Owner creates workspace
    ws_res = client.post("/workspaces", json={"name": "RBAC Test Workspace"}, headers=owner_headers)
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    # Add member and viewer via repository
    ws_repo = WorkspaceRepository(db_session)
    ws_repo.add_member(ws_id, member_id, "member")
    ws_repo.add_member(ws_id, viewer_id, "viewer")

    # --- 1. Non-member (Stranger) Access Checks -> Must return 404 (Not 403) ---
    res_stranger = client.get(f"/conversations?workspace_id={ws_id}", headers=stranger_headers)
    assert res_stranger.status_code == 404

    # --- 2. Viewer Role Checks ---
    # Viewer can list conversations/documents
    res_view_conv = client.get(f"/conversations?workspace_id={ws_id}", headers=viewer_headers)
    assert res_view_conv.status_code == 200

    # Viewer CANNOT create conversations -> 403 Forbidden
    res_view_create_conv = client.post(f"/conversations?workspace_id={ws_id}", json={"title": "Viewer Chat"}, headers=viewer_headers)
    assert res_view_create_conv.status_code == 403

    # Viewer CANNOT upload documents -> 403 Forbidden
    res_view_doc = client.post(f"/documents?workspace_id={ws_id}", json={"title": "Doc", "content": "Content"}, headers=viewer_headers)
    assert res_view_doc.status_code == 403

    # Viewer CANNOT invite members -> 403 Forbidden
    res_view_invite = client.post(f"/workspaces/{ws_id}/invites", json={"email": "new@example.com", "role": "member"}, headers=viewer_headers)
    assert res_view_invite.status_code == 403

    # --- 3. Member Role Checks ---
    # Member CAN create conversations
    res_mem_create_conv = client.post(f"/conversations?workspace_id={ws_id}", json={"title": "Member Chat"}, headers=member_headers)
    assert res_mem_create_conv.status_code == 201

    # Member CANNOT invite members -> 403 Forbidden
    res_mem_invite = client.post(f"/workspaces/{ws_id}/invites", json={"email": "new2@example.com", "role": "member"}, headers=member_headers)
    assert res_mem_invite.status_code == 403

    # --- 4. Owner Role Checks ---
    # Owner CAN invite members
    res_owner_invite = client.post(f"/workspaces/{ws_id}/invites", json={"email": "new3@example.com", "role": "viewer"}, headers=owner_headers)
    assert res_owner_invite.status_code == 201


def test_owner_removal_and_demotion_protection(client: TestClient, db_session: Session):
    owner_id, owner_token = create_user(db_session, "sole_owner@example.com", "Sole Owner")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    ws_res = client.post("/workspaces", json={"name": "Protected Workspace"}, headers=owner_headers)
    ws_id = ws_res.json()["id"]

    # Attempt to remove owner -> 400 Bad Request
    res_rem = client.delete(f"/workspaces/{ws_id}/members/{owner_id}", headers=owner_headers)
    assert res_rem.status_code == 400
    assert "Cannot remove the workspace owner" in res_rem.json()["detail"]

    # Attempt to demote owner to member -> 400 Bad Request
    res_dem = client.patch(f"/workspaces/{ws_id}/members/{owner_id}", json={"role": "member"}, headers=owner_headers)
    assert res_dem.status_code == 400
    assert "Cannot demote the workspace owner" in res_dem.json()["detail"]


def test_invite_acceptance_and_expiry_flow(client: TestClient, db_session: Session):
    owner_id, owner_token = create_user(db_session, "inviter_owner@example.com", "Inviter Owner")
    joiner_id, joiner_token = create_user(db_session, "invitee_joiner@example.com", "Invitee Joiner")

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    joiner_headers = {"Authorization": f"Bearer {joiner_token}"}

    ws_res = client.post("/workspaces", json={"name": "Invite Flow Workspace"}, headers=owner_headers)
    ws_id = ws_res.json()["id"]

    # Create invite
    invite_res = client.post(
        f"/workspaces/{ws_id}/invites",
        json={"email": "invitee_joiner@example.com", "role": "member"},
        headers=owner_headers,
    )
    assert invite_res.status_code == 201
    token = invite_res.json()["token"]

    # Joiner accepts invite
    accept_res = client.post(f"/workspaces/invites/{token}/accept", headers=joiner_headers)
    assert accept_res.status_code == 200
    assert accept_res.json()["role"] == "member"

    # Re-accepting already used token -> 400 Bad Request
    reaccept_res = client.post(f"/workspaces/invites/{token}/accept", headers=joiner_headers)
    assert reaccept_res.status_code == 400

    # Test expired token
    invite_expired_res = client.post(
        f"/workspaces/{ws_id}/invites",
        json={"email": "expired_test@example.com", "role": "viewer"},
        headers=owner_headers,
    )
    exp_token = invite_expired_res.json()["token"]

    # Manually expire token in DB
    invite_model = db_session.query(WorkspaceInviteModel).filter_by(token=exp_token).first()
    if invite_model:
        invite_model.expires_at = utc_now() - timedelta(days=1)
        db_session.commit()

    accept_expired_res = client.post(f"/workspaces/invites/{exp_token}/accept", headers=joiner_headers)
    assert accept_expired_res.status_code == 400
    assert "expired" in accept_expired_res.json()["detail"].lower()
