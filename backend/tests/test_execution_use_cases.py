from optimus_backend.application.use_cases.start_execution import FinalizeExecutionUseCase, StartExecutionUseCase
from optimus_backend.infrastructure.persistence.in_memory import InMemoryAuditRepository, InMemoryExecutionRepository
from optimus_backend.infrastructure.queue.in_memory_queue import InMemoryJobQueue


def test_start_execution_enqueues_job() -> None:
    executions = InMemoryExecutionRepository()
    audit = InMemoryAuditRepository()
    queue = InMemoryJobQueue()

    use_case = StartExecutionUseCase(executions=executions, audit=audit, queue=queue)
    record = use_case.execute(project_id="p1", objective="Analisar falha de deploy", agent="ops")

    assert record.status == "queued"
    assert queue.enqueued == [record.id]
    events = audit.list_by_execution(record.id)
    assert [event.event_type for event in events] == ["queued", "enqueued"]


def test_finalize_execution_complete() -> None:
    executions = InMemoryExecutionRepository()
    audit = InMemoryAuditRepository()
    queue = InMemoryJobQueue()

    starter = StartExecutionUseCase(executions=executions, audit=audit, queue=queue)
    record = starter.execute(project_id="p1", objective="Validar regressão", agent="qa")

    finalize = FinalizeExecutionUseCase(executions=executions, audit=audit)
    finalize.mark_running(record.id)
    finalize.complete(record.id, summary="ok", duration_ms=120)

    updated = executions.get(record.id)
    assert updated is not None
    assert updated.status == "completed"
    assert updated.summary == "ok"

    event_types = [event.event_type for event in audit.list_by_execution(record.id)]
    assert "started" in event_types
    assert "completed" in event_types
