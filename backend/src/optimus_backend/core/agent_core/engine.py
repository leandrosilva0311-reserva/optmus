from dataclasses import dataclass
from uuid import uuid4

from optimus_backend.core.context_builder.builder import ContextBuilder
from optimus_backend.core.execution_guard.guard import ExecutionGuard
from optimus_backend.core.orchestrator.service import Orchestrator
from optimus_backend.core.telemetry.sink import TelemetryEvent, TelemetrySink


@dataclass(slots=True)
class ExecutionResult:
    execution_id: str
    status: str
    summary: str


class AgentEngine:
    def __init__(
        self,
        context_builder: ContextBuilder,
        guard: ExecutionGuard,
        orchestrator: Orchestrator,
        telemetry: TelemetrySink,
    ) -> None:
        self._context_builder = context_builder
        self._guard = guard
        self._orchestrator = orchestrator
        self._telemetry = telemetry

    def execute(self, objective: str, agent: str, project_id: str = "default") -> ExecutionResult:
        execution_id = str(uuid4())
        context = self._context_builder.build(project_id=project_id, objective=objective)
        context_reason = "; ".join(item.reason for item in context.items[:3])
        self._telemetry.emit(TelemetryEvent(execution_id, agent, "start", context_reason))

        self._guard.assert_iteration(1)
        self._guard.assert_non_destructive(objective)

        specialist_result = self._orchestrator.run(agent, context.objective)
        summary = f"agent={specialist_result.agent} result={specialist_result.output}"

        self._telemetry.emit(TelemetryEvent(execution_id, agent, "finish", summary))
        return ExecutionResult(execution_id=execution_id, status="completed", summary=summary)
