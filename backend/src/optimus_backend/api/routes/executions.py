from fastapi import APIRouter, Depends

from optimus_backend.api.authz import ensure_access
from optimus_backend.api.dependencies import get_current_user, get_list_execution_use_case, get_start_execution_use_case
from optimus_backend.application.use_cases.list_executions import ListExecutionsUseCase
from optimus_backend.application.use_cases.start_execution import StartExecutionUseCase
from optimus_backend.core.auth_scopes import ADMIN_READ, SCENARIOS_RUN
from optimus_backend.schemas.execution import AuditEventView, ExecutionView, QueueTaskResponse, SubtaskView, TaskRequest

router = APIRouter(prefix="/executions", tags=["executions"])


@router.post("/run", response_model=QueueTaskResponse)
def run_execution(
    payload: TaskRequest,
    start: StartExecutionUseCase = Depends(get_start_execution_use_case),
    user: dict[str, str] = Depends(get_current_user),
) -> QueueTaskResponse:
    ensure_access(user, {"admin", "operator"}, {SCENARIOS_RUN}, "/executions/run")
    record = start.execute(project_id=payload.project_id, objective=payload.objective, agent=payload.agent)
    return QueueTaskResponse(execution_id=record.id, status=record.status)


@router.get("/", response_model=list[ExecutionView])
def list_executions(
    use_case: ListExecutionsUseCase = Depends(get_list_execution_use_case),
    user: dict[str, str] = Depends(get_current_user),
) -> list[ExecutionView]:
    ensure_access(user, {"admin", "operator", "viewer"}, {ADMIN_READ}, "/executions")
    records = use_case.list_recent(limit=100)
    return [
        ExecutionView(
            id=r.id,
            project_id=r.project_id,
            objective=r.objective,
            agent=r.agent,
            status=r.status,
            summary=r.summary,
            error=r.error,
            duration_ms=r.duration_ms,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.get("/{execution_id}/subtasks", response_model=list[SubtaskView])
def get_subtasks(
    execution_id: str,
    use_case: ListExecutionsUseCase = Depends(get_list_execution_use_case),
    user: dict[str, str] = Depends(get_current_user),
) -> list[SubtaskView]:
    ensure_access(user, {"admin", "operator", "viewer"}, {ADMIN_READ}, f"/executions/{execution_id}/subtasks")
    subtasks = use_case.subtasks(execution_id)
    return [
        SubtaskView(
            id=s.id,
            execution_id=s.execution_id,
            agent=s.agent,
            title=s.title,
            depends_on=s.depends_on,
            status=s.status,
            result_summary=s.result_summary,
            handoff_reason=s.handoff_reason,
            attempt=s.attempt,
            created_at=s.created_at,
        )
        for s in subtasks
    ]


@router.get("/{execution_id}/timeline", response_model=list[AuditEventView])
def get_timeline(
    execution_id: str,
    use_case: ListExecutionsUseCase = Depends(get_list_execution_use_case),
    user: dict[str, str] = Depends(get_current_user),
) -> list[AuditEventView]:
    ensure_access(user, {"admin", "operator", "viewer"}, {ADMIN_READ}, f"/executions/{execution_id}/timeline")
    events = use_case.timeline(execution_id)
    return [
        AuditEventView(
            id=e.id,
            execution_id=e.execution_id,
            event_type=e.event_type,
            message=e.message,
            created_at=e.created_at,
        )
        for e in events
    ]
