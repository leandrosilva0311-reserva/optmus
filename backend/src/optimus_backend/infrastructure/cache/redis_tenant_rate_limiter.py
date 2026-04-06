try:
    from redis import Redis
except Exception:  # pragma: no cover
    Redis = None  # type: ignore[assignment]


class RedisTenantRateLimiter:
    """Distributed tenant rate limiter backed by Redis — safe for multi-instance deploys."""

    def __init__(self, redis_url: str) -> None:
        if Redis is None:
            raise RuntimeError("redis package not installed")
        self._client = Redis.from_url(redis_url, decode_responses=True)

    def allow(self, tenant_id: str, limit: int, ttl_seconds: int = 60) -> bool:
        key = f"rl:tenant:{tenant_id}"
        count = self._client.incr(key)
        if count == 1:
            self._client.expire(key, ttl_seconds)
        return count <= limit
