from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ExecutionRecord:
    id: str
    project_id: str
    objective: str
    agent: str
    status: str
    summary: str | None
    error: str | None
    duration_ms: int | None
    created_at: datetime
    updated_at: datetime


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
class MemoryEntry:
    id: str
    project_id: str
    entry_type: str
    source: str
    confidence: float
    content: str
    status: str  # pending|approved
    created_at: datetime


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
