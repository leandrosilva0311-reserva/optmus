import os
import uuid
from datetime import UTC, datetime

import pytest

from optimus_backend.domain.entities import ExecutionRecord
from optimus_backend.infrastructure.cache.redis_locks import RedisLockManager
from optimus_backend.infrastructure.cache.redis_sessions import RedisSessionRepository
from optimus_backend.infrastructure.persistence.postgres import PostgresExecutionRepository, PostgresUserRepository
from optimus_backend.infrastructure.queue.arq_queue import ArqJobQueue


pytestmark = pytest.mark.integration


@pytest.mark.skipif(not os.getenv("INTEGRATION_REAL"), reason="Set INTEGRATION_REAL=1 to run with PostgreSQL+Redis+ARQ")
def test_real_postgres_redis_arq_flow() -> None:
    database_url = os.environ["DATABASE_URL"]
    redis_url = os.environ["REDIS_URL"]
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("REDIS_PORT", "6379"))

    users = PostgresUserRepository(database_url)
    user = users.find_by_email("admin@optimus.local")
    assert user is not None

    sessions = RedisSessionRepository(redis_url)
    session_id = str(uuid.uuid4())
    sessions.save(session_id, user.id, 10)
    assert sessions.get_user_id(session_id) == user.id

    locks = RedisLockManager(redis_url)
    assert locks.acquire("execution:test", ttl_seconds=5) is True
    locks.release("execution:test")

    executions = PostgresExecutionRepository(database_url)
    execution_id = str(uuid.uuid4())
    record = ExecutionRecord(
        id=execution_id,
        project_id="integration",
        objective="integration test",
        agent="ops",
        status="queued",
        summary=None,
        error=None,
        duration_ms=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    executions.create(record)
    loaded = executions.get(execution_id)
    assert loaded is not None

    queue = ArqJobQueue(redis_host, redis_port)
    queue.enqueue_execution(execution_id)
