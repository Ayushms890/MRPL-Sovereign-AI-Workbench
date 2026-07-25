# NOTE: This test covers the experimental, non-default streaming path.
from datetime import datetime, timezone
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.api.deps_providers import get_conversation_repository, get_planner_agent
from app.domain.entities import User
from app.main import app


def test_streaming_message_route(db_session):
    now = datetime.now(timezone.utc)
    user = User(
        id="stream-user-1",
        email="stream@example.com",
        name="Stream User",
        emailVerified=True,
        createdAt=now,
        updatedAt=now,
    )

    mock_repo = MagicMock()
    mock_repo.get_for_user.return_value = MagicMock(
        id="conv-stream-1", user_id=user.id, title="Stream Conv"
    )
    mock_repo.add_message.side_effect = lambda conversation_id, role, content, tool_name=None: MagicMock(
        id=f"msg-{role}-1", role=role, content=content, tool_name=tool_name
    )
    mock_repo.list_messages.return_value = []

    mock_agent = MagicMock()
    mock_agent.run.return_value = MagicMock(
        answer="Streaming test answer",
        tool_name="web_search",
        tool_arguments={"query": "test news"},
        agent_name="research",
        thought_process="User wants test research.",
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_conversation_repository] = lambda: mock_repo
    app.dependency_overrides[get_planner_agent] = lambda: mock_agent

    client = TestClient(app)
    response = client.post(
        "/conversations/conv-stream-1/messages/stream",
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
