from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from app.api.deps_providers import get_redis_cache
from app.cache.redis_client import RedisCache
from app.main import app
from tests.test_conversations import FakeUpstashRedisClient


def test_share_flow(
    client: TestClient,
    auth_headers: dict[str, str],
    db_session: Session,
) -> None:
    fake_redis = FakeUpstashRedisClient()
    fake_cache = RedisCache("http://fake", "fake")
    fake_cache.client = fake_redis
    
    app.dependency_overrides[get_redis_cache] = lambda: fake_cache
    try:
        # 1. Create a conversation
        create = client.post("/conversations", headers=auth_headers, json={"title": "Share test session"})
        assert create.status_code == 201
        conversation_id = create.json()["id"]

        # 2. Add a message manually using repo
        from app.conversations.repository import ConversationRepository
        repo = ConversationRepository(db_session)
        repo.add_message(conversation_id=conversation_id, role="user", content="Hello sharing world")
        repo.add_message(conversation_id=conversation_id, role="assistant", content="Shared response")

        # 3. Share the conversation
        share = client.post(f"/conversations/{conversation_id}/share", headers=auth_headers)
        assert share.status_code == 200
        share_data = share.json()
        assert "share_id" in share_data
        share_id = share_data["share_id"]
        assert share_data["title"] == "Share test session"

        # 4. Fetch the share snapshot (unauthenticated)
        snapshot = client.get(f"/conversations/share/{share_id}")
        assert snapshot.status_code == 200
        snap_data = snapshot.json()
        assert snap_data["title"] == "Share test session"
        assert len(snap_data["messages"]) == 2
        assert snap_data["messages"][0]["content"] == "Hello sharing world"
        assert snap_data["messages"][1]["content"] == "Shared response"

        # 5. Import the shared conversation (authenticated)
        imported = client.post(f"/conversations/share/{share_id}/import", headers=auth_headers)
        assert imported.status_code == 200
        imported_data = imported.json()
        assert imported_data["title"] == "Share test session"
        new_id = imported_data["id"]
        assert new_id != conversation_id

        # Verify imported messages
        imported_messages = client.get(f"/conversations/{new_id}/messages", headers=auth_headers)
        assert imported_messages.status_code == 200
        imp_msgs = imported_messages.json()
        assert len(imp_msgs) == 2
        assert imp_msgs[0]["content"] == "Hello sharing world"
        assert imp_msgs[1]["content"] == "Shared response"
        
    finally:
        app.dependency_overrides.pop(get_redis_cache, None)
