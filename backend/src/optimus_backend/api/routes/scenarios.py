import json

from fastapi import APIRouter, Depends, HTTPException

from optimus_backend.api.dependencies import (
    get_current_user,
    get_list_execution_use_case,
    get_repositories,
    get_scenario_catalog,
    get_start_execution_use_case,
    get_usage_meter,
    get_billing_read_model,
)
from optimus_backend.application.use_cases.run_scenario import RunScenarioUseCase
from optimus_backend.schemas.scenario import (
    ScenarioCatalogItemResponse,
    ScenarioDefinitionOfDoneResponse,
    ScenarioDetailResponse,
    ScenarioFinalBusinessBlockResponse,
    ScenarioRunRequest,
    ScenarioRunResponse,
    UsageSnapshotResponse,
)

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


def ensure_role(user: dict[str, str], allowed: set[str]) -> None:
    if user["role"] not in allowed:
        raise HTTPException(status_code=403, detail="insufficient role")


@router.get("/catalog", response_model=list[ScenarioCatalogItemResponse])
def scenario_catalog(user: dict[str, str] = Depends(get_current_user)) -> list[ScenarioCatalogItemResponse]:
    ensure_role(user, {"admin", "operator", "viewer"})
    catalog = get_scenario_catalog().list_all()
    return [
        ScenarioCatalogItemResponse(
            scenario_id=item.scenario_id,
            name=item.name,
            required_inputs=[field.name for field in item.required_inputs],
            definition_of_done=ScenarioDefinitionOfDoneResponse(
                success_criteria=list(item.done.success_criteria),
                failure_criteria=list(item.done.failure_criteria),
            ),
            supported_terminal_states=list(item.supported_terminal_states),
            business_value=item.business_value,
            recommended_for=list(item.recommended_for),
            estimated_runtime_minutes=item.estimated_runtime_minutes,
            onboarding_steps=list(item.onboarding_steps),
        )
        for item in catalog
    ]


@router.post("/run", response_model=ScenarioRunResponse)
def run_scenario(payload: ScenarioRunRequest, user: dict[str, str] = Depends(get_current_user)) -> ScenarioRunResponse:
    ensure_role(user, {"admin", "operator"})
    executions, _, audit, _, _, _, _, _, _ = get_repositories()
    use_case = RunScenarioUseCase(
        get_start_execution_use_case(),
        executions,
        get_scenario_catalog(),
        audit,
        get_usage_meter(),
        get_billing_read_model(),
    )
    try:
        result = use_case.execute(payload.project_id, payload.scenario_id, payload.objective, payload.inputs, payload.plan_id)
    except ValueError as exc:
        if str(exc).startswith("usage_limit_exceeded"):
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ScenarioRunResponse(
        execution_id=result.execution_id,
        status=result.status,
        reused=result.reused,
        usage=UsageSnapshotResponse(
            plan_id=result.usage.plan_id,
            daily_limit=result.usage.daily_limit,
            consumed_today=result.usage.consumed_today,
            remaining_today=result.usage.remaining_today,
            warning_level=result.usage.warning_level,
        ),
    )


@router.get("/{execution_id}", response_model=ScenarioDetailResponse)
def scenario_detail(execution_id: str, user: dict[str, str] = Depends(get_current_user)) -> ScenarioDetailResponse:
    ensure_role(user, {"admin", "operator", "viewer"})
    executions, _, audit, _, _, _, _, _, _ = get_repositories()
    execution = executions.get(execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="execution not found")

    scenario = get_scenario_catalog().get(execution.scenario_id)
    events = audit.list_by_execution(execution_id)
    final_block: ScenarioFinalBusinessBlockResponse | None = None
    for event in reversed(events):
        if event.event_type != "business_block":
            continue
        try:
            payload = json.loads(event.message)
            final_block = ScenarioFinalBusinessBlockResponse(**payload)
            break
        except Exception:
            continue

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
        final_business_block=final_block,
    )


@router.get("/{execution_id}/timeline")
def scenario_timeline(execution_id: str, user: dict[str, str] = Depends(get_current_user)) -> list[dict]:
    ensure_role(user, {"admin", "operator", "viewer"})
    events = get_list_execution_use_case().timeline(execution_id)
    return [{"event_type": e.event_type, "message": e.message, "created_at": e.created_at.isoformat()} for e in events]
