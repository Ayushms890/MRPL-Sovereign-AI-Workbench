import logging

from app.core.config import settings


logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self, url: str, token: str) -> None:
        self.url = url
        self.token = token
        self.client = None
        try:
            from upstash_redis import Redis  # type: ignore

            self.client = Redis(url=url, token=token)
        except Exception:
            self.client = None

    def get(self, key: str) -> str | None:
        if self.client is None:
            return None
        try:
            value = self.client.get(key)
        except Exception:
            logger.exception("Redis cache get failed for key %s", key)
            return None
        return value if isinstance(value, str) else None

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        if self.client is None:
            return
        try:
            self.client.set(key, value, ex=ttl_seconds)
        except Exception:
            logger.exception("Redis cache set failed for key %s", key)

    def delete(self, key: str) -> None:
        if self.client is None:
            return
        try:
            self.client.delete(key)
        except Exception:
            logger.exception("Redis cache delete failed for key %s", key)

    def incr(self, key: str) -> int | None:
        if self.client is None:
            return None
        try:
            return self.client.incr(key)
        except Exception:
            logger.exception("Redis cache incr failed for key %s", key)
            return None

    def expire(self, key: str, ttl_seconds: int) -> None:
        if self.client is None:
            return
        try:
            self.client.expire(key, ttl_seconds)
        except Exception:
            logger.exception("Redis cache expire failed for key %s", key)


def build_redis_cache() -> RedisCache | None:
    if not getattr(settings, "upstash_redis_rest_url", "") or not getattr(settings, "upstash_redis_rest_token", ""):
        return None
    try:
        return RedisCache(url=settings.upstash_redis_rest_url, token=settings.upstash_redis_rest_token)
    except Exception:
        logger.exception("Redis cache initialization failed")
        return None
