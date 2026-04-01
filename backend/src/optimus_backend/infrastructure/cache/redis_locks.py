try:
    from redis import Redis
except Exception:  # pragma: no cover
    Redis = None


class RedisLockManager:
    def __init__(self, redis_url: str) -> None:
        if Redis is None:
            raise RuntimeError("redis package not installed")
        self._client = Redis.from_url(redis_url, decode_responses=True)

    def acquire(self, key: str, ttl_seconds: int) -> bool:
        return bool(self._client.set(name=f"lock:{key}", value="1", ex=ttl_seconds, nx=True))

    def release(self, key: str) -> None:
        self._client.delete(f"lock:{key}")
