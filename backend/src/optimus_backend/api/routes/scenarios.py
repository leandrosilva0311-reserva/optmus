from fastapi import APIRouter, Depends, HTTPException

from optimus_backend.api.dependencies import (
    get_current_user,
    get_list_execution_use_case,
    get_repositories,
    get_scenario_catalog,
    get_start_execution_use_case,
)
from optimus_backend.application.use_cases.run_scenario import RunScenarioUseCase
from optimus_backend.core.scenarios.models import ScenarioFinalBusinessBlock
from optimus_backend.schemas.scenario import (
    ScenarioDefinitionOfDoneResponse,
    ScenarioDetailResponse,
    ScenarioFinalBusinessBlockResponse,
    ScenarioRunRequest,
    ScenarioRunResponse,
)

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


def ensure_role(user: dict[str, str], allowed: set[str]) -> None:
    if user["role"] not in allowed:
        raise HTTPException(status_code=403, detail="insufficient role")


@router.post("/run", response_model=ScenarioRunResponse)
def run_scenario(payload: ScenarioRunRequest, user: dict[str, str] = Depends(get_current_user)) -> ScenarioRunResponse:
    ensure_role(user, {"admin", "operator"})
    executions, _, _, _, _, _, _, _, _ = get_repositories()
    use_case = RunScenarioUseCase(get_start_execution_use_case(), executions, get_scenario_catalog())
    result = use_case.execute(payload.project_id, payload.scenario_id, payload.objective, payload.inputs)
    return ScenarioRunResponse(execution_id=result.execution_id, status=result.status, reused=result.reused)


@router.get("/{execution_id}", response_model=ScenarioDetailResponse)
def scenario_detail(execution_id: str, user: dict[str, str] = Depends(get_current_user)) -> ScenarioDetailResponse:
    ensure_role(user, {"admin", "operator", "viewer"})
    executions, _, _, _, _, _, _, _, _ = get_repositories()
    execution = executions.get(execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="execution not found")
    scenario = get_scenario_catalog().get(execution.scenario_id)
    final_block = ScenarioFinalBusinessBlock(
        operational_impact="Aguardando síntese da execução.",
        commercial_impact="Aguardando síntese da execução.",
        severity="pending",
        immediate_action="Aguardando síntese da execução.",
        suggested_owner="ops_sentinel",
    )
    return ScenarioDetailResponse(
        execution_id=execution.id,
        project_id=execution.project_id,
        scenario_id=execution.scenario_id,
        status=execution.status,
        summary=execution.summary,
        max_steps=execution.max_steps,
        max_tool_calls=execution.max_tool_calls,
        max_duration_ms=execution.max_duration_ms,
        created_at=execution.created_at,
        required_inputs=[field.name for field in scenario.required_inputs],
        definition_of_done=ScenarioDefinitionOfDoneResponse(
            success_criteria=list(scenario.done.success_criteria),
            failure_criteria=list(scenario.done.failure_criteria),
        ),
        supported_terminal_states=list(scenario.supported_terminal_states),
        final_business_block=ScenarioFinalBusinessBlockResponse(
            operational_impact=final_block.operational_impact,
            commercial_impact=final_block.commercial_impact,
            severity=final_block.severity,
            immediate_action=final_block.immediate_action,
            suggested_owner=final_block.suggested_owner,
        ),
    )


@router.get("/{execution_id}/timeline")
def scenario_timeline(execution_id: str, user: dict[str, str] = Depends(get_current_user)) -> list[dict]:
    ensure_role(user, {"admin", "operator", "viewer"})
    events = get_list_execution_use_case().timeline(execution_id)
    return [{"event_type": e.event_type, "message": e.message, "created_at": e.created_at.isoformat()} for e in events]
