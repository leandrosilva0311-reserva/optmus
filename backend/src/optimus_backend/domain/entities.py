from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class ExecutionRecord:
    id: str
    project_id: str
    objective: str
    agent: str
    scenario_id: str
    status: str
    summary: str | None
    error: str | None
    duration_ms: int | None
    created_at: datetime
    updated_at: datetime
    idempotency_key: str = ""
    max_steps: int = 25
    max_tool_calls: int = 50
    max_duration_ms: int = 120000
    steps_used: int = 0
    tool_calls_used: int = 0


@dataclass(slots=True)
class AuditEventRecord:
    id: str
    execution_id: str
    event_type: str
    message: str
    created_at: datetime


@dataclass(slots=True)
class UserRecord:
    id: str
    email: str
    password_hash: str
    role: str


@dataclass(slots=True)
class TenantRecord:
    id: str
    name: str
    plan: str
    is_active: bool = True


@dataclass(slots=True)
class APIKeyRecord:
    id: str
    tenant_id: str
    key_hash: str
    label: str
    is_active: bool = True


@dataclass(slots=True)
class MemoryEntry:
    id: str
    project_id: str
    entry_type: str
    source: str
    confidence: float
    content: str
    status: str  # pending|approved|deprecated
    created_at: datetime
    version: int = 1
    supersedes_id: str | None = None


@dataclass(slots=True)
class SubtaskRecord:
    id: str
    execution_id: str
    agent: str
    title: str
    depends_on: list[str]
    status: str
    result_summary: str | None
    created_at: datetime
    updated_at: datetime
    handoff_reason: str | None = None
    attempt: int = 1


@dataclass(slots=True)
class ScenarioDefinition:
    scenario_id: str
    name: str
    steps: list[str]
    success_criteria: list[str]
    failure_criteria: list[str]
