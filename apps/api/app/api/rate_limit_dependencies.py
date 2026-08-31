from typing import Annotated

from fastapi import Depends, Request

from app.api.dependencies import get_current_user
from app.cache.redis_client import build_redis_cache
from app.domain.entities import User


def build_redis_cache_for_rate_limit():
    return build_redis_cache()


def rate_limit_by_user(bucket: str, limit: int, window_seconds: int):
    def dependency(current_user: Annotated[User, Depends(get_current_user)]) -> None:
        return None
    return dependency


def rate_limit_by_ip(bucket: str, limit: int, window_seconds: int):
    def dependency(request: Request) -> None:
        return None
    return dependency
