from datetime import UTC, datetime
from functools import lru_cache

from fastapi import Header, HTTPException

from optimus_backend.application.use_cases.authenticate import AuthenticateUserUseCase
from optimus_backend.application.use_cases.list_executions import ListExecutionsUseCase
from optimus_backend.application.use_cases.start_execution import FinalizeExecutionUseCase, StartExecutionUseCase
from optimus_backend.core.agent_core.engine import AgentEngine
from optimus_backend.core.context_builder.builder import ContextBuilder
from optimus_backend.core.execution_guard.guard import ExecutionGuard
from optimus_backend.core.memory.store import MemoryStore
from optimus_backend.core.orchestrator.service import Orchestrator
from optimus_backend.core.provider.base import MockProvider
from optimus_backend.core.specialists.agents import AnalystAgent, DevAgent, OpsAgent, QAAgent
from optimus_backend.core.telemetry.sink import TelemetrySink
from optimus_backend.domain.entities import UserRecord
from optimus_backend.infrastructure.auth.security import hash_password
from optimus_backend.infrastructure.cache.redis_locks import RedisLockManager
from optimus_backend.infrastructure.cache.redis_sessions import RedisSessionRepository
from optimus_backend.infrastructure.persistence.in_memory import (
    InMemoryAuditRepository,
    InMemoryExecutionRepository,
    InMemoryLockManager,
    InMemorySessionRepository,
    InMemoryUserRepository,
)
from optimus_backend.infrastructure.persistence.postgres import PostgresAuditRepository, PostgresExecutionRepository
from optimus_backend.infrastructure.queue.arq_queue import ArqJobQueue
from optimus_backend.infrastructure.queue.in_memory_queue import InMemoryJobQueue
from optimus_backend.settings.config import config


@lru_cache(maxsize=1)
def get_engine() -> AgentEngine:
    provider = MockProvider()
    specialists = {
        "dev": DevAgent(provider),
        "qa": QAAgent(provider),
        "ops": OpsAgent(provider),
        "analyst": AnalystAgent(provider),
    }
    return AgentEngine(
        context_builder=ContextBuilder(MemoryStore()),
        guard=ExecutionGuard(),
        orchestrator=Orchestrator(specialists),
        telemetry=TelemetrySink(),
    )


@lru_cache(maxsize=1)
def get_repositories() -> tuple[object, object, object, object, object, object]:
    users = InMemoryUserRepository(
        [
            UserRecord(
                id="u-admin",
                email="admin@optimus.local",
                password_hash=hash_password("admin12345"),
                role="admin",
            )
        ]
    )
    if config.app_env == "test":
        return (
            InMemoryExecutionRepository(),
            InMemoryAuditRepository(),
            InMemorySessionRepository(),
            users,
            InMemoryJobQueue(),
            InMemoryLockManager(),
        )

    return (
        PostgresExecutionRepository(config.database_url),
        PostgresAuditRepository(config.database_url),
        RedisSessionRepository(config.redis_url),
        users,
        ArqJobQueue(config.redis_host, config.redis_port),
        RedisLockManager(config.redis_url),
    )


def get_auth_use_case() -> AuthenticateUserUseCase:
    _, _, sessions, users, _, _ = get_repositories()
    return AuthenticateUserUseCase(users=users, sessions=sessions)


def get_start_execution_use_case() -> StartExecutionUseCase:
    executions, audit, _, _, queue, _ = get_repositories()
    return StartExecutionUseCase(executions=executions, audit=audit, queue=queue)


def get_finalize_execution_use_case() -> FinalizeExecutionUseCase:
    executions, audit, _, _, _, _ = get_repositories()
    return FinalizeExecutionUseCase(executions=executions, audit=audit)


def get_list_execution_use_case() -> ListExecutionsUseCase:
    executions, audit, _, _, _, _ = get_repositories()
    return ListExecutionsUseCase(executions=executions, audit=audit)


def get_current_user(x_session_id: str = Header(default="", alias="X-Session-Id")) -> dict[str, str]:
    if not x_session_id:
        raise HTTPException(status_code=401, detail="missing session")
    _, _, sessions, _, _, _ = get_repositories()
    user_id = sessions.get_user_id(x_session_id)
    if not user_id:
        raise HTTPException(status_code=401, detail="invalid session")
    return {"user_id": user_id, "session_id": x_session_id, "checked_at": datetime.now(UTC).isoformat()}
