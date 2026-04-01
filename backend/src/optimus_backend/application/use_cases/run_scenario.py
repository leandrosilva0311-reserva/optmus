from dataclasses import dataclass

from optimus_backend.application.use_cases.start_execution import StartExecutionUseCase, build_idempotency_key
from optimus_backend.core.scenarios.catalog import ScenarioCatalog
from optimus_backend.domain.ports import ExecutionRepository


@dataclass(slots=True)
class RunScenarioResult:
    execution_id: str
    status: str
    reused: bool


class RunScenarioUseCase:
    def __init__(self, start_execution: StartExecutionUseCase, executions: ExecutionRepository, catalog: ScenarioCatalog) -> None:
        self._start_execution = start_execution
        self._executions = executions
        self._catalog = catalog

    def execute(self, project_id: str, scenario_id: str, objective: str, inputs: dict[str, str]) -> RunScenarioResult:
        self._catalog.validate_inputs(scenario_id, inputs)
        key = build_idempotency_key(project_id, scenario_id, objective)
        before_ids = {e.id for e in self._executions.list_recent(200) if e.idempotency_key == key}
        execution = self._start_execution.execute(
            project_id=project_id,
            scenario_id=scenario_id,
            objective=objective,
            agent="dev_architect",
        )
        reused = execution.id in before_ids
        return RunScenarioResult(execution_id=execution.id, status=execution.status, reused=reused)
