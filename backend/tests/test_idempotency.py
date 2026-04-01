from optimus_backend.application.use_cases.start_execution import StartExecutionUseCase
from optimus_backend.core.orchestrator.service import Orchestrator
from optimus_backend.core.provider.base import MockProvider
from optimus_backend.core.specialists.agents import AnalystAgent, BugHunterAgent, DevArchitectAgent, OpsSentinelAgent, QAAgent
from optimus_backend.infrastructure.persistence.in_memory import InMemoryAuditRepository, InMemoryExecutionRepository, InMemorySubtaskRepository
from optimus_backend.infrastructure.queue.in_memory_queue import InMemoryJobQueue


def _orchestrator() -> Orchestrator:
    provider = MockProvider()
    return Orchestrator(
        {
            "dev_architect": DevArchitectAgent(provider),
            "bug_hunter": BugHunterAgent(provider),
            "qa": QAAgent(provider),
            "ops_sentinel": OpsSentinelAgent(provider),
            "analyst": AnalystAgent(provider),
        }
    )


def test_idempotency_reuses_execution_within_window() -> None:
    use_case = StartExecutionUseCase(
        executions=InMemoryExecutionRepository(),
        subtasks=InMemorySubtaskRepository(),
        audit=InMemoryAuditRepository(),
        queue=InMemoryJobQueue(),
        orchestrator=_orchestrator(),
        idempotency_window_minutes=30,
    )
    first = use_case.execute(project_id="p1", objective="run health", agent="dev_architect", scenario_id="health")
    second = use_case.execute(project_id="p1", objective="run health", agent="dev_architect", scenario_id="health")
    assert first.id == second.id
