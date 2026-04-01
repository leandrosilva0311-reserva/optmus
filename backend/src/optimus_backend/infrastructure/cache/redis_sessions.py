try:
    from redis import Redis
except Exception:  # pragma: no cover
    Redis = None


class RedisSessionRepository:
    def __init__(self, redis_url: str) -> None:
        if Redis is None:
            raise RuntimeError("redis package not installed")
        self._client = Redis.from_url(redis_url, decode_responses=True)

    def save(self, session_id: str, user_id: str, ttl_seconds: int) -> None:
        self._client.setex(f"session:{session_id}", ttl_seconds, user_id)

    def get_user_id(self, session_id: str) -> str | None:
        return self._client.get(f"session:{session_id}")

    def delete(self, session_id: str) -> None:
        self._client.delete(f"session:{session_id}")
