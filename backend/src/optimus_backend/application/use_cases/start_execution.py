from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from optimus_backend.domain.entities import AuditEventRecord, ExecutionRecord
from optimus_backend.domain.ports import AuditRepository, ExecutionRepository, JobQueue


def build_event(execution_id: str, event_type: str, message: str) -> AuditEventRecord:
    return AuditEventRecord(
        id=str(uuid4()),
        execution_id=execution_id,
        event_type=event_type,
        message=message,
        created_at=datetime.now(UTC),
    )


class StartExecutionUseCase:
    def __init__(self, executions: ExecutionRepository, audit: AuditRepository, queue: JobQueue) -> None:
        self._executions = executions
        self._audit = audit
        self._queue = queue

    def execute(self, project_id: str, objective: str, agent: str) -> ExecutionRecord:
        now = datetime.now(UTC)
        record = ExecutionRecord(
            id=str(uuid4()),
            project_id=project_id,
            objective=objective,
            agent=agent,
            status="queued",
            summary=None,
            error=None,
            duration_ms=None,
            created_at=now,
            updated_at=now,
        )
        self._executions.create(record)
        self._audit.append(build_event(record.id, "queued", "Execution queued by API request"))
        self._queue.enqueue_execution(record.id)
        self._audit.append(build_event(record.id, "enqueued", "Execution sent to async queue"))
        return record


class FinalizeExecutionUseCase:
    def __init__(self, executions: ExecutionRepository, audit: AuditRepository) -> None:
        self._executions = executions
        self._audit = audit

    def mark_running(self, execution_id: str) -> None:
        record = self._executions.get(execution_id)
        if record is None:
            raise KeyError("execution not found")
        updated = replace(record, status="running", updated_at=datetime.now(UTC))
        self._executions.update(updated)
        self._audit.append(build_event(execution_id, "started", "Worker started processing execution"))

    def complete(self, execution_id: str, summary: str, duration_ms: int) -> None:
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
