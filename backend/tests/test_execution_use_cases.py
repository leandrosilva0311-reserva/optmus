from optimus_backend.application.use_cases.start_execution import FinalizeExecutionUseCase, StartExecutionUseCase
from optimus_backend.core.orchestrator.service import Orchestrator
from optimus_backend.core.provider.base import MockProvider
from optimus_backend.core.specialists.agents import (
    AnalystAgent,
    BugHunterAgent,
    DevArchitectAgent,
    OpsSentinelAgent,
    QAAgent,
)
from optimus_backend.infrastructure.persistence.in_memory import (
    InMemoryAuditRepository,
    InMemoryExecutionRepository,
    InMemoryMemoryRepository,
    InMemorySubtaskRepository,
)
from optimus_backend.infrastructure.queue.in_memory_queue import InMemoryJobQueue


def _orchestrator() -> Orchestrator:
    provider = MockProvider()
    specialists = {
        "dev_architect": DevArchitectAgent(provider),
        "bug_hunter": BugHunterAgent(provider),
        "qa": QAAgent(provider),
        "ops_sentinel": OpsSentinelAgent(provider),
        "analyst": AnalystAgent(provider),
    }
    return Orchestrator(specialists)


def test_start_execution_enqueues_job_and_subtasks() -> None:
    executions = InMemoryExecutionRepository()
    subtasks = InMemorySubtaskRepository()
    audit = InMemoryAuditRepository()
    queue = InMemoryJobQueue()

    use_case = StartExecutionUseCase(
        executions=executions,
        subtasks=subtasks,
        audit=audit,
        queue=queue,
        orchestrator=_orchestrator(),
    )
    record = use_case.execute(project_id="p1", objective="Analisar falha de deploy", agent="ops_sentinel")

    assert record.status == "queued"
    assert queue.enqueued == [record.id]
    events = audit.list_by_execution(record.id)
    assert [event.event_type for event in events] == ["queued", "subtasks_created", "enqueued"]
    assert len(subtasks.list_by_execution(record.id)) >= 3


def test_finalize_execution_complete_adds_memory_entry() -> None:
    executions = InMemoryExecutionRepository()
    subtasks = InMemorySubtaskRepository()
    audit = InMemoryAuditRepository()
    queue = InMemoryJobQueue()
    memory = InMemoryMemoryRepository()

    starter = StartExecutionUseCase(
        executions=executions,
        subtasks=subtasks,
        audit=audit,
        queue=queue,
        orchestrator=_orchestrator(),
    )
    record = starter.execute(project_id="p1", objective="Validar regressão", agent="qa")

    finalize = FinalizeExecutionUseCase(executions=executions, subtasks=subtasks, audit=audit, memory=memory)
    finalize.mark_running(record.id)
    finalize.complete(record.id, summary="ok", duration_ms=120, project_id="p1")

    updated = executions.get(record.id)
    assert updated is not None
    assert updated.status == "completed"
    assert updated.summary == "ok"
    assert len(memory.list_for_project("p1")) == 1
