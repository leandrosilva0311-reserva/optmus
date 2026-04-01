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


@dataclass(slots=True)
class PlanDefinitionRecord:
    plan_id: str
    name: str
    daily_scenario_limit: int
    monthly_price_cents: int
    active: bool


@dataclass(slots=True)
class SubscriptionRecord:
    id: str
    project_id: str
    plan_id: str
    status: str
    started_at: datetime
    renews_at: datetime | None
    cancelled_at: datetime | None


@dataclass(slots=True)
class InvoiceRecord:
    id: str
    project_id: str
    period_start: datetime
    period_end: datetime
    status: str
    total_cents: int
    created_at: datetime


@dataclass(slots=True)
class InvoiceItemRecord:
    id: str
    invoice_id: str
    item_type: str
    quantity: int
    unit_price_cents: int
    total_cents: int
    description: str


@dataclass(slots=True)
class UsageHistoryRecord:
    event_date: datetime
    units: int


@dataclass(slots=True)
class SubscriptionPlanChangeRecord:
    id: str
    project_id: str
    from_plan_id: str
    to_plan_id: str
    effective_at: datetime
    status: str
    created_at: datetime


@dataclass(slots=True)
class BillingCycleClosureRecord:
    id: str
    project_id: str
    period_start: datetime
    period_end: datetime
    invoice_id: str
    usage_units: int
    closed_by: str
    created_at: datetime
