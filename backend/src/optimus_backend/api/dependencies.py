from datetime import UTC, datetime
from functools import lru_cache

from fastapi import Header, HTTPException

from optimus_backend.application.use_cases.authenticate import AuthenticateUserUseCase, LogoutUseCase
from optimus_backend.application.use_cases.list_executions import ListExecutionsUseCase
from optimus_backend.application.use_cases.resolve_tenant import ResolveTenantByApiKeyUseCase
from optimus_backend.application.use_cases.start_execution import FinalizeExecutionUseCase, StartExecutionUseCase
from optimus_backend.core.agent_core.engine import AgentEngine
from optimus_backend.core.context_builder.builder import ContextBuilder
from optimus_backend.core.execution_guard.guard import ExecutionGuard
from optimus_backend.core.orchestrator.service import Orchestrator
from optimus_backend.core.policy.engine import PolicyEngine
from optimus_backend.core.provider.base import MockProvider
from optimus_backend.core.scenarios.catalog import ScenarioCatalog
from optimus_backend.core.specialists.agents import AnalystAgent, BugHunterAgent, DevArchitectAgent, OpsSentinelAgent, QAAgent
from optimus_backend.core.telemetry.sink import TelemetrySink
from optimus_backend.core.tenancy.security import hash_api_key
from optimus_backend.core.tooling.executor import ToolExecutor
from optimus_backend.domain.entities import APIKeyRecord, TenantRecord, UserRecord
from optimus_backend.domain.ports import APIKeyRepository, TenantRateLimiter, TenantRepository
from optimus_backend.infrastructure.cache.redis_locks import RedisLockManager
from optimus_backend.infrastructure.cache.redis_rate_limiter import RedisRateLimiter
from optimus_backend.infrastructure.cache.redis_sessions import RedisSessionRepository
from optimus_backend.infrastructure.persistence.in_memory import (
    InMemoryAuditRepository,
    InMemoryExecutionRepository,
    InMemoryLockManager,
    InMemoryMemoryRepository,
    InMemoryRateLimiter,
    InMemorySessionRepository,
    InMemorySubtaskRepository,
    InMemoryUserRepository,
)
from optimus_backend.infrastructure.tenancy.in_memory import (
    InMemoryAPIKeyRepository,
    InMemoryTenantRateLimiter,
    InMemoryTenantRepository,
)
from optimus_backend.infrastructure.persistence.postgres import (
    PostgresAuditRepository,
    PostgresExecutionRepository,
    PostgresMemoryRepository,
    PostgresSubtaskRepository,
    PostgresUserRepository,
)
from optimus_backend.infrastructure.queue.arq_queue import ArqJobQueue
from optimus_backend.infrastructure.queue.in_memory_queue import InMemoryJobQueue
from optimus_backend.infrastructure.auth.security import hash_password
from optimus_backend.infrastructure.tools.filesystem_tool import FilesystemTool
from optimus_backend.infrastructure.tools.http_tool import HttpTool
from optimus_backend.infrastructure.tools.kaiso_log_correlation_tool import (
    InMemoryKaisoLogCorrelationProvider,
    KaisoLogCorrelationTool,
)
from optimus_backend.infrastructure.tools.kaiso_queue_inspection_tool import (
    InMemoryKaisoQueueInspectionProvider,
    KaisoQueueInspectionTool,
)
from optimus_backend.infrastructure.tools.terminal_tool import TerminalTool
from optimus_backend.settings.config import config


@lru_cache(maxsize=1)
def get_orchestrator() -> Orchestrator:
    provider = MockProvider()
    specialists = {
        "dev_architect": DevArchitectAgent(provider),
        "bug_hunter": BugHunterAgent(provider),
        "qa": QAAgent(provider),
        "ops_sentinel": OpsSentinelAgent(provider),
        "analyst": AnalystAgent(provider),
    }
    return Orchestrator(specialists)


@lru_cache(maxsize=1)
def get_tool_executor() -> ToolExecutor:
    _, _, _, _, _, _, _, _, rate_limiter = get_repositories()
    tools = {
        "filesystem": FilesystemTool(config.project_root),
        "terminal": TerminalTool(timeout_seconds=4),
        "http": HttpTool(),
        "kaiso_log_correlation": KaisoLogCorrelationTool(InMemoryKaisoLogCorrelationProvider()),
        "kaiso_queue_inspection": KaisoQueueInspectionTool(InMemoryKaisoQueueInspectionProvider()),
    }
    return ToolExecutor(
        tools=tools,
        policy=PolicyEngine(),
        guard=ExecutionGuard(),
        rate_limiter=rate_limiter,
        project_limit=config.rate_limit_project_per_minute,
        tool_limit=config.rate_limit_tool_per_minute,
    )


@lru_cache(maxsize=1)
def get_scenario_catalog() -> ScenarioCatalog:
    return ScenarioCatalog()


@lru_cache(maxsize=1)
def get_engine() -> AgentEngine:
    return AgentEngine(
        context_builder=ContextBuilder(get_repositories()[3]),
        guard=ExecutionGuard(),
        orchestrator=get_orchestrator(),
        telemetry=TelemetrySink(),
    )


@lru_cache(maxsize=1)
def get_repositories() -> tuple[object, object, object, object, object, object, object, object, object]:
    if config.app_env == "test":
        users: list[UserRecord] = []
        if config.enable_dev_seed_user:
            users.append(
                UserRecord(
                    id="u-dev-seed",
                    email=config.dev_seed_user_email,
                    password_hash=hash_password(config.dev_seed_user_password),
                    role=config.dev_seed_user_role,
                )
            )
        return (
            InMemoryExecutionRepository(),
            InMemorySubtaskRepository(),
            InMemoryAuditRepository(),
            InMemoryMemoryRepository(),
            InMemorySessionRepository(),
            InMemoryUserRepository(users),
            InMemoryJobQueue(),
            InMemoryLockManager(),
            InMemoryRateLimiter(),
        )

    return (
        PostgresExecutionRepository(config.database_url),
        PostgresSubtaskRepository(config.database_url),
        PostgresAuditRepository(config.database_url),
        PostgresMemoryRepository(config.database_url),
        RedisSessionRepository(config.redis_url),
        PostgresUserRepository(config.database_url),
        ArqJobQueue(config.redis_host, config.redis_port),
        RedisLockManager(config.redis_url),
        RedisRateLimiter(config.redis_url),
    )


@lru_cache(maxsize=1)
def get_tenant_repositories() -> tuple[TenantRepository, APIKeyRepository]:
    return (
        InMemoryTenantRepository(
            tenants=[
                TenantRecord(id="tenant-dev", name="Tenant Development", plan="pro", is_active=True),
            ]
        ),
        InMemoryAPIKeyRepository(
            api_keys=[
                APIKeyRecord(
                    id="key-dev-1",
                    tenant_id="tenant-dev",
                    key_hash=hash_api_key(config.default_tenant_api_key),
                    label="default development key",
                    is_active=True,
                )
            ],
        ),
    )


@lru_cache(maxsize=1)
def get_tenant_rate_limiter() -> TenantRateLimiter:
    return InMemoryTenantRateLimiter()


def get_tenant_resolver_use_case() -> ResolveTenantByApiKeyUseCase:
    tenants, api_keys = get_tenant_repositories()
    return ResolveTenantByApiKeyUseCase(api_keys=api_keys, tenants=tenants)


def get_auth_use_case() -> AuthenticateUserUseCase:
    _, _, _, _, sessions, users, _, _, _ = get_repositories()
    return AuthenticateUserUseCase(users=users, sessions=sessions)


def get_logout_use_case() -> LogoutUseCase:
    _, _, _, _, sessions, _, _, _, _ = get_repositories()
    return LogoutUseCase(sessions=sessions)


def get_start_execution_use_case() -> StartExecutionUseCase:
    executions, subtasks, audit, _, _, _, queue, _, _ = get_repositories()
    return StartExecutionUseCase(
        executions=executions,
        subtasks=subtasks,
        audit=audit,
        queue=queue,
        orchestrator=get_orchestrator(),
        idempotency_window_minutes=config.idempotency_window_minutes,
    )


def get_finalize_execution_use_case() -> FinalizeExecutionUseCase:
    executions, subtasks, audit, memory, _, _, _, _, _ = get_repositories()
    return FinalizeExecutionUseCase(executions=executions, subtasks=subtasks, audit=audit, memory=memory)


def get_list_execution_use_case() -> ListExecutionsUseCase:
    executions, subtasks, audit, _, _, _, _, _, _ = get_repositories()
    return ListExecutionsUseCase(executions=executions, subtasks=subtasks, audit=audit)


def get_current_user(x_session_id: str = Header(default="", alias="X-Session-Id")) -> dict[str, str]:
    if not x_session_id:
        raise HTTPException(status_code=401, detail="missing session")
    _, _, _, _, sessions, users, _, _, _ = get_repositories()
    user_id = sessions.get_user_id(x_session_id)
    if not user_id:
        raise HTTPException(status_code=401, detail="invalid session")
    user = users.find_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="unknown user")
    return {
        "user_id": user_id,
        "session_id": x_session_id,
        "role": user.role,
        "checked_at": datetime.now(UTC).isoformat(),
    }
