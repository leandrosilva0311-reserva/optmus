try:
    from redis import Redis
except Exception:  # pragma: no cover
    Redis = None


class RedisRateLimiter:
    def __init__(self, redis_url: str) -> None:
        if Redis is None:
            raise RuntimeError("redis package not installed")
        self._client = Redis.from_url(redis_url, decode_responses=True)

    def allow(self, project_id: str, tool_name: str, project_limit: int, tool_limit: int, ttl_seconds: int = 60) -> bool:
        project_key = f"rl:project:{project_id}"
        tool_key = f"rl:tool:{project_id}:{tool_name}"

        project_count = self._client.incr(project_key)
        tool_count = self._client.incr(tool_key)

        if project_count == 1:
            self._client.expire(project_key, ttl_seconds)
        if tool_count == 1:
            self._client.expire(tool_key, ttl_seconds)

        return project_count <= project_limit and tool_count <= tool_limit
