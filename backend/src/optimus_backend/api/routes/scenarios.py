from fastapi import APIRouter, Depends, HTTPException

from optimus_backend.api.dependencies import get_current_user, get_list_execution_use_case, get_start_execution_use_case, get_repositories
from optimus_backend.application.use_cases.run_scenario import RunScenarioUseCase
from optimus_backend.schemas.scenario import ScenarioDetailResponse, ScenarioRunRequest, ScenarioRunResponse

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


def ensure_role(user: dict[str, str], allowed: set[str]) -> None:
    if user["role"] not in allowed:
        raise HTTPException(status_code=403, detail="insufficient role")


@router.post("/run", response_model=ScenarioRunResponse)
def run_scenario(payload: ScenarioRunRequest, user: dict[str, str] = Depends(get_current_user)) -> ScenarioRunResponse:
    ensure_role(user, {"admin", "operator"})
    executions, _, _, _, _, _, _, _, _ = get_repositories()
    use_case = RunScenarioUseCase(get_start_execution_use_case(), executions)
    result = use_case.execute(payload.project_id, payload.scenario_id, payload.objective)
    return ScenarioRunResponse(execution_id=result.execution_id, status=result.status, reused=result.reused)


@router.get("/{execution_id}", response_model=ScenarioDetailResponse)
def scenario_detail(execution_id: str, user: dict[str, str] = Depends(get_current_user)) -> ScenarioDetailResponse:
    ensure_role(user, {"admin", "operator", "viewer"})
    executions, _, _, _, _, _, _, _, _ = get_repositories()
    execution = executions.get(execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="execution not found")
    return ScenarioDetailResponse(
        execution_id=execution.id,
        project_id=execution.project_id,
        scenario_id="default",
        status=execution.status,
        summary=execution.summary,
        max_steps=execution.max_steps,
        max_tool_calls=execution.max_tool_calls,
        max_duration_ms=execution.max_duration_ms,
        created_at=execution.created_at,
    )


@router.get("/{execution_id}/timeline")
def scenario_timeline(execution_id: str, user: dict[str, str] = Depends(get_current_user)) -> list[dict]:
    ensure_role(user, {"admin", "operator", "viewer"})
    events = get_list_execution_use_case().timeline(execution_id)
    return [{"event_type": e.event_type, "message": e.message, "created_at": e.created_at.isoformat()} for e in events]
