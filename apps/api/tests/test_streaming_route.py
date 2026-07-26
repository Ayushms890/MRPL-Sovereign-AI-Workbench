# NOTE: This test covers the experimental, non-default streaming path.
from datetime import datetime, timezone
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.deps_providers import get_conversation_repository, get_planner_agent
from app.auth.repository import UserRepository
from app.conversations.repository import ConversationRepository
from app.db import get_db_session
from app.domain.entities import User
from app.main import app
from app.workspaces.repository import WorkspaceRepository


def test_streaming_message_route(db_session: Session):
    user_repo = UserRepository(db_session)
    user_entity = user_repo.create_user_with_password("stream@example.com", "pw", "Stream User")
    
    ws_repo = WorkspaceRepository(db_session)
    ws = ws_repo.get_personal_workspace(user_entity.id)
    ws_id = ws.id if ws else "ws_test"

    conv_repo = ConversationRepository(db_session)
    conv = conv_repo.create(user_id=user_entity.id, title="Stream Conv", workspace_id=ws_id)

    mock_agent = MagicMock()
    mock_agent.run.return_value = MagicMock(
        answer="Streaming test answer",
        tool_name="web_search",
        tool_arguments={"query": "test news"},
        agent_name="research",
        thought_process="User wants test research.",
    )

    user = User(
        id=user_entity.id,
        email=user_entity.email,
        name=user_entity.name,
        emailVerified=True,
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
    )

    app.dependency_overrides[get_db_session] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_planner_agent] = lambda: mock_agent

    client = TestClient(app)
    response = client.post(
        f"/conversations/{conv.id}/messages/stream",
        json={"content": "What is the latest AI news?"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    body = response.text
    assert "event: thinking" in body
    assert "event: thought" in body
    assert "event: token" in body
    assert "event: done" in body
    assert "User wants test research." in body
    assert "Streaming test answer" in body
