try:
    from arq import create_pool
    from arq.connections import RedisSettings
except Exception:  # pragma: no cover
    create_pool = None
    RedisSettings = None


class ArqJobQueue:
    def __init__(self, redis_host: str, redis_port: int, queue_name: str = "arq:queue") -> None:
        self._redis_host = redis_host
        self._redis_port = redis_port
        self._queue_name = queue_name

    def enqueue_execution(self, execution_id: str) -> None:
        if create_pool is None or RedisSettings is None:
            raise RuntimeError("arq package not installed")
        import asyncio

        async def _enqueue() -> None:
            redis = await create_pool(RedisSettings(host=self._redis_host, port=self._redis_port))
            await redis.enqueue_job("run_execution_job", execution_id, _queue_name=self._queue_name)

        asyncio.run(_enqueue())
