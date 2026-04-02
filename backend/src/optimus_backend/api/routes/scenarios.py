import json

from fastapi import APIRouter, Depends, Header, HTTPException, Response

from optimus_backend.api.authz import ensure_access
from optimus_backend.api.dependencies import (
    get_billing_read_model,
    get_current_user,
    get_git_local_source_connector_factory,
    get_list_execution_use_case,
    get_repositories,
    get_scenario_catalog,
    get_start_execution_use_case,
    get_usage_meter,
)
from optimus_backend.application.use_cases.run_scenario import RunScenarioUseCase
from optimus_backend.core.auth_scopes import ADMIN_READ, SCENARIOS_RUN
from optimus_backend.schemas.scenario import (
    ScenarioCatalogItemResponse,
    ScenarioDefinitionOfDoneResponse,
    ScenarioDetailResponse,
    ScenarioEngineeringReportResponse,
    ScenarioFinalBusinessBlockResponse,
    ScenarioRunRequest,
    ScenarioRunResponse,
    UsageSnapshotResponse,
)

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("/catalog", response_model=list[ScenarioCatalogItemResponse])
def scenario_catalog(user: dict[str, str] = Depends(get_current_user)) -> list[ScenarioCatalogItemResponse]:
    ensure_access(user, {"admin", "operator", "viewer"}, {ADMIN_READ}, "/scenarios/catalog")
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
def run_scenario(
    payload: ScenarioRunRequest,
    response: Response,
    user: dict[str, str] = Depends(get_current_user),
    x_request_id: str = Header(default="", alias="X-Request-Id"),
) -> ScenarioRunResponse:
    ensure_access(user, {"admin", "operator"}, {SCENARIOS_RUN}, "/scenarios/run")
    executions, _, audit, _, _, _, _, _, _ = get_repositories()
    use_case = RunScenarioUseCase(
        get_start_execution_use_case(),
        executions,
        get_scenario_catalog(),
        audit,
        get_usage_meter(),
        get_billing_read_model(),
        get_git_local_source_connector_factory(),
    )
    try:
        result = use_case.execute(payload.project_id, payload.scenario_id, payload.objective, payload.inputs, payload.plan_id)
    except ValueError as exc:
        if str(exc).startswith("usage_limit_exceeded"):
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if x_request_id:
        response.headers["X-Request-Id"] = x_request_id
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
        request_id=x_request_id or None,
        scenario_id=result.scenario_id,
        deprecated_alias_used=result.deprecated_alias_used,
    )


@router.get("/{execution_id}", response_model=ScenarioDetailResponse)
def scenario_detail(execution_id: str, user: dict[str, str] = Depends(get_current_user)) -> ScenarioDetailResponse:
    ensure_access(user, {"admin", "operator", "viewer"}, {ADMIN_READ}, f"/scenarios/{execution_id}")
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
    ensure_access(user, {"admin", "operator", "viewer"}, {ADMIN_READ}, f"/scenarios/{execution_id}/timeline")
    events = get_list_execution_use_case().timeline(execution_id)
    return [{"event_type": e.event_type, "message": e.message, "created_at": e.created_at.isoformat()} for e in events]


@router.get("/{execution_id}/engineering-report", response_model=ScenarioEngineeringReportResponse)
def scenario_engineering_report(
    execution_id: str,
    user: dict[str, str] = Depends(get_current_user),
) -> ScenarioEngineeringReportResponse:
    ensure_access(user, {"admin", "operator", "viewer"}, {ADMIN_READ}, f"/scenarios/{execution_id}/engineering-report")
    executions, _, audit, memory, _, _, _, _, _ = get_repositories()
    execution = executions.get(execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="execution not found")

    project_entries = memory.list_for_project(execution.project_id)
    artifact_entries = [
        entry
        for entry in project_entries
        if entry.entry_type == "engineering_report" and entry.source == execution_id
    ]
    if artifact_entries:
        latest_entry = sorted(artifact_entries, key=lambda item: item.version, reverse=True)[0]
        try:
            payload = json.loads(latest_entry.content)
            return ScenarioEngineeringReportResponse(**payload)
        except Exception:
            pass

    events = audit.list_by_execution(execution_id)
    for event in reversed(events):
        if event.event_type != "engineering_report":
            continue
        try:
            payload = json.loads(event.message)
            return ScenarioEngineeringReportResponse(**payload)
        except Exception:
            continue

    raise HTTPException(status_code=404, detail="engineering report not found")
