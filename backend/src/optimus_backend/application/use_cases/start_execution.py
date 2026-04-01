from dataclasses import replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import uuid4

from optimus_backend.core.orchestrator.service import Orchestrator
from optimus_backend.domain.entities import AuditEventRecord, ExecutionRecord, MemoryEntry, SubtaskRecord
from optimus_backend.domain.ports import AuditRepository, ExecutionRepository, JobQueue, MemoryRepository, SubtaskRepository


def build_event(execution_id: str, event_type: str, message: str) -> AuditEventRecord:
    return AuditEventRecord(
        id=str(uuid4()),
        execution_id=execution_id,
        event_type=event_type,
        message=message,
        created_at=datetime.now(UTC),
    )


def build_idempotency_key(project_id: str, scenario_id: str, objective: str) -> str:
    normalized = " ".join(objective.lower().split())
    return sha256(f"{project_id}|{scenario_id}|{normalized}".encode("utf-8")).hexdigest()


class StartExecutionUseCase:
    def __init__(
        self,
        executions: ExecutionRepository,
        subtasks: SubtaskRepository,
        audit: AuditRepository,
        queue: JobQueue,
        orchestrator: Orchestrator,
        idempotency_window_minutes: int = 30,
    ) -> None:
        self._executions = executions
        self._subtasks = subtasks
        self._audit = audit
        self._queue = queue
        self._orchestrator = orchestrator
        self._idempotency_window_minutes = idempotency_window_minutes

    def execute(self, project_id: str, objective: str, agent: str, scenario_id: str = "default") -> ExecutionRecord:
        now = datetime.now(UTC)
        idempotency_key = build_idempotency_key(project_id, scenario_id, objective)

        for candidate in self._executions.list_recent(limit=200):
            if candidate.idempotency_key != idempotency_key:
                continue
            if candidate.created_at < now - timedelta(minutes=self._idempotency_window_minutes):
                continue
            self._audit.append(build_event(candidate.id, "idempotency_reused", "Execution reused by idempotency key"))
            return candidate

        record = ExecutionRecord(
            id=str(uuid4()),
            project_id=project_id,
            objective=objective,
            agent=agent,
            scenario_id=scenario_id,
            status="queued",
            summary=None,
            error=None,
            duration_ms=None,
            created_at=now,
            updated_at=now,
            idempotency_key=idempotency_key,
        )
        self._executions.create(record)

        subtasks = self._orchestrator.plan_subtasks(record.id, objective)
        self._subtasks.create_many(subtasks)

        self._audit.append(build_event(record.id, "queued", "Execution queued by API request"))
        self._audit.append(build_event(record.id, "subtasks_created", f"{len(subtasks)} subtasks created"))
        self._queue.enqueue_execution(record.id)
        self._audit.append(build_event(record.id, "enqueued", "Execution sent to async queue"))
        return record


class FinalizeExecutionUseCase:
    def __init__(
        self,
        executions: ExecutionRepository,
        subtasks: SubtaskRepository,
        audit: AuditRepository,
        memory: MemoryRepository,
    ) -> None:
        self._executions = executions
        self._subtasks = subtasks
        self._audit = audit
        self._memory = memory

    def mark_running(self, execution_id: str) -> None:
        record = self._executions.get(execution_id)
        if record is None:
            raise KeyError("execution not found")
        updated = replace(record, status="running", updated_at=datetime.now(UTC))
        self._executions.update(updated)
        self._audit.append(build_event(execution_id, "started", "Worker started processing execution"))

    def mark_subtask_event(self, execution_id: str, subtask: SubtaskRecord, event: str, message: str) -> None:
        self._audit.append(build_event(execution_id, event, f"{subtask.agent}:{subtask.title}:{message}"))

    def complete(self, execution_id: str, summary: str, duration_ms: int, project_id: str) -> None:
        record = self._executions.get(execution_id)
        if record is None:
            raise KeyError("execution not found")
        updated = replace(
            record,
            status="completed",
            summary=summary,
            duration_ms=duration_ms,
            updated_at=datetime.now(UTC),
        )
        self._executions.update(updated)
        self._audit.append(build_event(execution_id, "completed", "Execution completed"))

        latest = self._memory.latest_by_type(project_id, "decision")
        supersedes_id = latest.id if latest else None
        version = (latest.version + 1) if latest else 1

        if latest and latest.content != summary[:500]:
            latest.status = "deprecated"

        self._memory.add(
            MemoryEntry(
                id=str(uuid4()),
                project_id=project_id,
                entry_type="decision",
                source="execution_summary",
                confidence=0.7,
                content=summary[:500],
                status="pending",
                created_at=datetime.now(UTC),
                version=version,
                supersedes_id=supersedes_id,
            )
        )

    def fail(self, execution_id: str, message: str, duration_ms: int) -> None:
        record = self._executions.get(execution_id)
        if record is None:
            raise KeyError("execution not found")
        updated = replace(
            record,
            status="failed",
            error=message,
            duration_ms=duration_ms,
            updated_at=datetime.now(UTC),
        )
        self._executions.update(updated)
        self._audit.append(build_event(execution_id, "failed", message))
