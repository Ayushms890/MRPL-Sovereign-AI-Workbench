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
    fake_redis = FakeRedisForSharing()
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


class FakeRedisForSharing:
    def __init__(self):
        self.db = {}
        self.sets = {}
        self.ttls = {}

    def get(self, key):
        return self.db.get(key)

    def set(self, key, value, ex=None):
        self.db[key] = value
        if ex is not None:
            self.ttls[key] = ex

    def delete(self, key):
        self.db.pop(key, None)
        self.sets.pop(key, None)
        self.ttls.pop(key, None)

    def sadd(self, key, member):
        if key not in self.sets:
            self.sets[key] = set()
        self.sets[key].add(member)
        return 1

    def smembers(self, key):
        return self.sets.get(key, set())

    def expire(self, key, ttl_seconds):
        self.ttls[key] = ttl_seconds


def test_share_ttl_and_revoke(
    client: TestClient,
    auth_headers: dict[str, str],
    db_session: Session,
) -> None:
    fake_redis = FakeRedisForSharing()
    fake_cache = RedisCache("http://fake", "fake")
    fake_cache.client = fake_redis
    
    app.dependency_overrides[get_redis_cache] = lambda: fake_cache
    try:
        create = client.post("/conversations", headers=auth_headers, json={"title": "Revoke test session"})
        assert create.status_code == 201
        conversation_id = create.json()["id"]

        share = client.post(f"/conversations/{conversation_id}/share", headers=auth_headers)
        assert share.status_code == 200
        share_id = share.json()["share_id"]

        assert fake_redis.ttls.get(f"shared_chat:{share_id}") == 2592000
        assert fake_redis.ttls.get(f"conv_shares:{conversation_id}") == 2592000

        snapshot = client.get(f"/conversations/share/{share_id}")
        assert snapshot.status_code == 200

        revoke = client.delete(f"/conversations/{conversation_id}/share", headers=auth_headers)
        assert revoke.status_code == 204

        assert fake_redis.get(f"shared_chat:{share_id}") is None
        assert f"conv_shares:{conversation_id}" not in fake_redis.sets

        snapshot_after = client.get(f"/conversations/share/{share_id}")
        assert snapshot_after.status_code == 404

    finally:
        app.dependency_overrides.pop(get_redis_cache, None)


def test_share_view_rate_limit(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import json
    from tests.test_rate_limit import FakeRateLimitRedisCache
    from app.api.deps_providers import get_redis_cache
    
    fake_cache = FakeRateLimitRedisCache()
    monkeypatch.setattr("app.api.rate_limit_dependencies.build_redis_cache", lambda: fake_cache)

    fake_redis = FakeRedisForSharing()
    fake_redis.db["shared_chat:limit-test"] = json.dumps({"title": "Test limit", "messages": []})
    
    mock_redis_cache = RedisCache("http://fake", "fake")
    mock_redis_cache.client = fake_redis
    app.dependency_overrides[get_redis_cache] = lambda: mock_redis_cache

    try:
        for i in range(30):
            res = client.get("/conversations/share/limit-test")
            assert res.status_code == 200

        res_over = client.get("/conversations/share/limit-test")
        assert res_over.status_code == 429
        assert "rate limit exceeded" in res_over.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_redis_cache, None)


def test_share_import_malformed_role(
    client: TestClient,
    auth_headers: dict[str, str],
    db_session: Session,
) -> None:
    import json
    fake_redis = FakeRedisForSharing()
    payload = {
        "title": "Import Role Test",
        "messages": [
            {
                "id": "msg-1",
                "role": "user",
                "content": "Valid user message",
            },
            {
                "id": "msg-2",
                "role": "hacker_role",
                "content": "Malformed message that should be skipped",
            },
            {
                "id": "msg-3",
                "role": "assistant",
                "content": "Valid assistant message",
            }
        ]
    }
    fake_redis.db["shared_chat:malformed-role"] = json.dumps(payload)
    fake_cache = RedisCache("http://fake", "fake")
    fake_cache.client = fake_redis
    
    app.dependency_overrides[get_redis_cache] = lambda: fake_cache
    try:
        imported = client.post("/conversations/share/malformed-role/import", headers=auth_headers)
        assert imported.status_code == 200
        new_id = imported.json()["id"]

        imported_messages = client.get(f"/conversations/{new_id}/messages", headers=auth_headers)
        assert imported_messages.status_code == 200
        imp_msgs = imported_messages.json()
        
        assert len(imp_msgs) == 2
        assert imp_msgs[0]["content"] == "Valid user message"
        assert imp_msgs[1]["content"] == "Valid assistant message"
        
    finally:
        app.dependency_overrides.pop(get_redis_cache, None)
