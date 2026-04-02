from datetime import UTC, datetime, timedelta
import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query

from optimus_backend.api.authz import ensure_access
from optimus_backend.api.dependencies import (
    get_billing_cycle_closer,
    get_billing_command_model,
    get_billing_read_model,
    get_billing_scheduler,
    get_current_user,
    get_usage_meter,
)
from optimus_backend.core.auth_scopes import ADMIN_READ, BILLING_READ, USAGE_READ
from optimus_backend.core.usage.metering import warning_for_ratio
from optimus_backend.domain.entities import BillingSchedulerRunRecord
from optimus_backend.schemas.billing import (
    BillingAdminOverviewResponse,
    BillingCycleCloseRequest,
    BillingCycleRunDueRequest,
    BillingCycleHistoryItemResponse,
    BillingCycleHistoryResponse,
    BillingCycleRunDueResponse,
    BillingCycleSchedulerConfigResponse,
    BillingSchedulerRunResponse,
    BillingSchedulerRunHistoryItemResponse,
    BillingSchedulerRunHistoryResponse,
    BillingInvoiceDetailResponse,
    BillingInvoiceHistoryEntryResponse,
    BillingInvoiceHistoryResponse,
    BillingInvoiceItemResponse,
    BillingInvoiceStatusChangeRequest,
    BillingInvoiceStatusTransitionResponse,
    BillingInvoiceResponse,
    BillingPlanChangeRequest,
    BillingPlanChangeHistoryResponse,
    BillingPlanChangeResponse,
    BillingPlanResponse,
    BillingSubscriptionActivateRequest,
    BillingSubscriptionCreateRequest,
    BillingSubscriptionResponse,
    BillingUsageCurrentResponse,
    BillingUsageHistoryResponse,
)

router = APIRouter(prefix="/billing", tags=["billing"])
logger = logging.getLogger(__name__)


def _raise_billing_error(status_code: int, code: str, message: str) -> None:
    raise HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _log_billing_event(event_type: str, user: dict[str, str], **extra: str) -> None:
    payload = {"execution_id": "billing-api", "agent_id": user.get("user_id") or user.get("api_key_id", "integration"), "event_type": event_type, **extra}
    logger.info("billing_event", extra=payload)


def ensure_role(
    user: dict[str, str],
    allowed: set[str],
    required_scopes: set[str] | None = None,
    route_path: str = "/billing",
) -> None:
    try:
        ensure_access(user, allowed, required_scopes or {BILLING_READ}, route_path)
    except HTTPException as exc:
        _raise_billing_error(exc.status_code, "billing_forbidden", str(exc.detail))


@router.get("/plans", response_model=list[BillingPlanResponse])
def list_plans(user: dict[str, str] = Depends(get_current_user)) -> list[BillingPlanResponse]:
    ensure_role(user, {"admin", "operator", "viewer"})
    plans = get_billing_read_model().list_active_plans()
    return [
        BillingPlanResponse(
            plan_id=plan.plan_id,
            name=plan.name,
            daily_scenario_limit=plan.daily_scenario_limit,
            monthly_price_cents=plan.monthly_price_cents,
            usage_unit_price_cents=plan.usage_unit_price_cents,
        )
        for plan in plans
    ]


@router.post("/subscription", response_model=BillingSubscriptionResponse)
def create_or_activate_subscription(
    payload: BillingSubscriptionCreateRequest,
    user: dict[str, str] = Depends(get_current_user),
) -> BillingSubscriptionResponse:
    ensure_role(user, {"admin", "operator"})
    try:
        sub = get_billing_command_model().create_or_activate_subscription(payload.project_id, payload.plan_id, actor_id=user.get("user_id", "api-key"))
    except KeyError as exc:
        _raise_billing_error(404, "billing_not_found", str(exc))
    except ValueError as exc:
        _raise_billing_error(400, "billing_validation_error", str(exc))
    _log_billing_event("subscription_activated", user, project_id=payload.project_id, plan_id=payload.plan_id)
    return BillingSubscriptionResponse(
        id=sub.id,
        project_id=sub.project_id,
        plan_id=sub.plan_id,
        status=sub.status,
        started_at=sub.started_at,
        renews_at=sub.renews_at,
    )


@router.post("/subscription/create", response_model=BillingSubscriptionResponse)
def create_subscription(
    payload: BillingSubscriptionCreateRequest,
    user: dict[str, str] = Depends(get_current_user),
) -> BillingSubscriptionResponse:
    ensure_role(user, {"admin", "operator"})
    try:
        sub = get_billing_command_model().create_subscription(payload.project_id, payload.plan_id, actor_id=user.get("user_id", "api-key"))
    except KeyError as exc:
        _raise_billing_error(404, "billing_not_found", str(exc))
    except ValueError as exc:
        _raise_billing_error(400, "billing_validation_error", str(exc))
    _log_billing_event("subscription_created", user, project_id=payload.project_id, plan_id=payload.plan_id)
    return BillingSubscriptionResponse(
        id=sub.id,
        project_id=sub.project_id,
        plan_id=sub.plan_id,
        status=sub.status,
        started_at=sub.started_at,
        renews_at=sub.renews_at,
    )


@router.post("/subscription/activate", response_model=BillingSubscriptionResponse)
def activate_subscription(
    payload: BillingSubscriptionActivateRequest,
    user: dict[str, str] = Depends(get_current_user),
) -> BillingSubscriptionResponse:
    ensure_role(user, {"admin", "operator"})
    try:
        sub = get_billing_command_model().activate_subscription(payload.project_id, actor_id=user.get("user_id", "api-key"))
    except KeyError as exc:
        _raise_billing_error(404, "billing_not_found", str(exc))
    except ValueError as exc:
        _raise_billing_error(400, "billing_validation_error", str(exc))
    _log_billing_event("subscription_activated_manual", user, project_id=payload.project_id)
    return BillingSubscriptionResponse(
        id=sub.id,
        project_id=sub.project_id,
        plan_id=sub.plan_id,
        status=sub.status,
        started_at=sub.started_at,
        renews_at=sub.renews_at,
    )


@router.post("/subscription/change-plan", response_model=BillingPlanChangeResponse)
def change_plan(
    payload: BillingPlanChangeRequest,
    user: dict[str, str] = Depends(get_current_user),
) -> BillingPlanChangeResponse:
    ensure_role(user, {"admin", "operator"})
    try:
        change = get_billing_command_model().change_plan(payload.project_id, payload.new_plan_id)
    except KeyError as exc:
        _raise_billing_error(404, "billing_not_found", str(exc))
    _log_billing_event("subscription_plan_changed", user, project_id=payload.project_id, new_plan_id=payload.new_plan_id)
    return BillingPlanChangeResponse(
        id=change.id,
        project_id=change.project_id,
        from_plan_id=change.from_plan_id,
        to_plan_id=change.to_plan_id,
        effective_at=change.effective_at,
        status=change.status,
    )


@router.post("/subscription/cancel", response_model=BillingSubscriptionResponse)
def cancel_subscription(
    project_id: str = Query(...),
    user: dict[str, str] = Depends(get_current_user),
) -> BillingSubscriptionResponse:
    ensure_role(user, {"admin", "operator"})
    try:
        sub = get_billing_command_model().cancel_subscription(project_id)
    except KeyError as exc:
        _raise_billing_error(404, "billing_not_found", str(exc))
    _log_billing_event("subscription_cancelled", user, project_id=project_id)
    return BillingSubscriptionResponse(
        id=sub.id,
        project_id=sub.project_id,
        plan_id=sub.plan_id,
        status=sub.status,
        started_at=sub.started_at,
        renews_at=sub.renews_at,
    )


@router.get("/subscription", response_model=BillingSubscriptionResponse)
def current_subscription(
    project_id: str = Query(...),
    user: dict[str, str] = Depends(get_current_user),
) -> BillingSubscriptionResponse:
    ensure_role(user, {"admin", "operator", "viewer"}, {BILLING_READ}, "/billing/subscription")
    sub = get_billing_read_model().get_active_subscription(project_id)
    if sub is None:
        _raise_billing_error(404, "billing_not_found", "active subscription not found")
    return BillingSubscriptionResponse(
        id=sub.id,
        project_id=sub.project_id,
        plan_id=sub.plan_id,
        status=sub.status,
        started_at=sub.started_at,
        renews_at=sub.renews_at,
    )


@router.get("/usage/current", response_model=BillingUsageCurrentResponse)
def usage_current(
    project_id: str = Query(...),
    user: dict[str, str] = Depends(get_current_user),
) -> BillingUsageCurrentResponse:
    ensure_role(user, {"admin", "operator", "viewer"}, {USAGE_READ}, "/billing/usage/current")
    sub = get_billing_read_model().get_active_subscription(project_id)
    if sub is None:
        _raise_billing_error(404, "billing_not_found", "active subscription not found")
    consumed, limit = get_usage_meter().current(project_id, sub.plan_id)
    return BillingUsageCurrentResponse(
        project_id=project_id,
        plan_id=sub.plan_id,
        consumed_today=consumed,
        daily_limit=limit,
        remaining_today=max(0, limit - consumed),
        warning_level=warning_for_ratio(consumed, limit),
    )


@router.get("/usage/history", response_model=BillingUsageHistoryResponse)
def usage_history(
    project_id: str = Query(...),
    days: int = Query(default=30, ge=1, le=120),
    user: dict[str, str] = Depends(get_current_user),
) -> BillingUsageHistoryResponse:
    ensure_role(user, {"admin", "operator", "viewer"}, {USAGE_READ}, "/billing/usage/history")
    now = datetime.now(UTC)
    date_from = now - timedelta(days=days)
    history = get_billing_read_model().usage_history(project_id, date_from, now)
    return BillingUsageHistoryResponse(
        project_id=project_id,
        items=[{"event_date": i.event_date.isoformat(), "units": i.units} for i in history],
    )


@router.get("/usage/period", response_model=BillingUsageHistoryResponse)
def usage_history_period(
    project_id: str = Query(...),
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    user: dict[str, str] = Depends(get_current_user),
) -> BillingUsageHistoryResponse:
    ensure_role(user, {"admin", "operator", "viewer"}, {USAGE_READ}, "/billing/usage/period")
    if period_start >= period_end:
        _raise_billing_error(400, "billing_validation_error", "period_start must be before period_end")
    history = get_billing_read_model().usage_history(project_id, period_start, period_end)
    return BillingUsageHistoryResponse(
        project_id=project_id,
        items=[{"event_date": i.event_date.isoformat(), "units": i.units} for i in history],
    )


@router.post("/cycle/close", response_model=BillingInvoiceResponse)
def close_cycle(
    payload: BillingCycleCloseRequest,
    user: dict[str, str] = Depends(get_current_user),
) -> BillingInvoiceResponse:
    ensure_role(user, {"admin", "operator"})
    try:
        invoice = get_billing_command_model().close_billing_cycle(
            payload.project_id,
            payload.period_start,
            payload.period_end,
            actor_id=user.get("user_id", "api-key"),
        )
    except ValueError as exc:
        _raise_billing_error(400, "billing_validation_error", str(exc))
    except KeyError as exc:
        _raise_billing_error(404, "billing_not_found", str(exc))
    _log_billing_event("billing_cycle_closed", user, project_id=payload.project_id)
    return BillingInvoiceResponse(
        id=invoice.id,
        project_id=invoice.project_id,
        period_start=invoice.period_start,
        period_end=invoice.period_end,
        status=invoice.status,
        total_cents=invoice.total_cents,
        created_at=invoice.created_at,
    )


@router.get("/invoices", response_model=list[BillingInvoiceResponse])
def list_invoices(
    project_id: str = Query(...),
    period_start: datetime | None = Query(default=None),
    period_end: datetime | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: dict[str, str] = Depends(get_current_user),
) -> list[BillingInvoiceResponse]:
    ensure_role(user, {"admin", "operator", "viewer"})
    try:
        invoices = get_billing_read_model().list_invoices(project_id)
    except KeyError as exc:
        _raise_billing_error(404, "billing_not_found", str(exc))
    filtered = [
        inv
        for inv in invoices
        if (period_start is None or inv.period_start >= period_start)
        and (period_end is None or inv.period_end <= period_end)
        and (status is None or inv.status == status)
    ]
    return [
        BillingInvoiceResponse(
            id=inv.id,
            project_id=inv.project_id,
            period_start=inv.period_start,
            period_end=inv.period_end,
            status=inv.status,
            total_cents=inv.total_cents,
            created_at=inv.created_at,
        )
        for inv in filtered[offset : offset + limit]
    ]


@router.get("/invoices/history", response_model=BillingInvoiceHistoryResponse)
def invoice_history(
    project_id: str = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: dict[str, str] = Depends(get_current_user),
) -> BillingInvoiceHistoryResponse:
    ensure_role(user, {"admin", "operator", "viewer"})
    invoices = get_billing_read_model().list_invoices(project_id)
    items = []
    for invoice in invoices[offset : offset + limit]:
        transitions = get_billing_read_model().list_invoice_status_transitions(invoice.id)
        entries = [
            BillingInvoiceStatusTransitionResponse(
                id=t.id,
                invoice_id=t.invoice_id,
                from_status=t.from_status,
                to_status=t.to_status,
                changed_by=t.changed_by,
                changed_at=t.changed_at,
            )
            for t in transitions
        ]
        items.append(
            BillingInvoiceHistoryEntryResponse(
                id=invoice.id,
                project_id=invoice.project_id,
                period_start=invoice.period_start,
                period_end=invoice.period_end,
                status=invoice.status,
                total_cents=invoice.total_cents,
                created_at=invoice.created_at,
                item_count=len(get_billing_read_model().list_invoice_items(invoice.id)),
                transitions=entries,
            )
        )
    return BillingInvoiceHistoryResponse(project_id=project_id, items=items)


@router.post("/invoices/status", response_model=BillingInvoiceResponse)
def change_invoice_status(
    payload: BillingInvoiceStatusChangeRequest,
    user: dict[str, str] = Depends(get_current_user),
) -> BillingInvoiceResponse:
    ensure_role(user, {"admin", "operator"})
    try:
        invoice = get_billing_command_model().update_invoice_status(payload.invoice_id, payload.to_status, actor_id=user.get("user_id", "api-key"))
    except KeyError as exc:
        _raise_billing_error(404, "billing_not_found", str(exc))
    _log_billing_event("invoice_status_changed", user, invoice_id=payload.invoice_id, to_status=payload.to_status)
    return BillingInvoiceResponse(
        id=invoice.id,
        project_id=invoice.project_id,
        period_start=invoice.period_start,
        period_end=invoice.period_end,
        status=invoice.status,
        total_cents=invoice.total_cents,
        created_at=invoice.created_at,
    )


@router.get("/invoices/detail", response_model=BillingInvoiceDetailResponse)
def invoice_detail(
    project_id: str = Query(...),
    invoice_id: str = Query(...),
    user: dict[str, str] = Depends(get_current_user),
) -> BillingInvoiceDetailResponse:
    ensure_role(user, {"admin", "operator", "viewer"})
    models = get_billing_read_model()
    try:
        invoice = next((inv for inv in models.list_invoices(project_id=project_id) if inv.id == invoice_id), None)
    except KeyError as exc:
        _raise_billing_error(404, "billing_not_found", str(exc))
    if invoice is None:
        _raise_billing_error(404, "billing_not_found", "invoice not found")
    return BillingInvoiceDetailResponse(
        id=invoice.id,
        project_id=invoice.project_id,
        period_start=invoice.period_start,
        period_end=invoice.period_end,
        status=invoice.status,
        total_cents=invoice.total_cents,
        created_at=invoice.created_at,
        items=[
            BillingInvoiceItemResponse(
                id=item.id,
                item_type=item.item_type,
                quantity=item.quantity,
                unit_price_cents=item.unit_price_cents,
                total_cents=item.total_cents,
                description=item.description,
            )
            for item in models.list_invoice_items(invoice_id)
        ],
    )


@router.get("/subscription/history", response_model=BillingPlanChangeHistoryResponse)
def subscription_change_history(
    project_id: str = Query(...),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: dict[str, str] = Depends(get_current_user),
) -> BillingPlanChangeHistoryResponse:
    ensure_role(user, {"admin", "operator", "viewer"})
    items = get_billing_read_model().list_plan_changes(project_id)
    filtered = [item for item in items if status is None or item.status == status]
    return BillingPlanChangeHistoryResponse(
        project_id=project_id,
        items=[
            BillingPlanChangeResponse(
                id=change.id,
                project_id=change.project_id,
                from_plan_id=change.from_plan_id,
                to_plan_id=change.to_plan_id,
                effective_at=change.effective_at,
                status=change.status,
            )
            for change in filtered[offset : offset + limit]
        ],
    )


@router.get("/cycles/history", response_model=BillingCycleHistoryResponse)
def cycle_history(
    project_id: str = Query(...),
    period_start: datetime | None = Query(default=None),
    period_end: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: dict[str, str] = Depends(get_current_user),
) -> BillingCycleHistoryResponse:
    ensure_role(user, {"admin", "operator", "viewer"})
    items = get_billing_read_model().list_cycle_closures(project_id)
    filtered = [
        item
        for item in items
        if (period_start is None or item.period_start >= period_start)
        and (period_end is None or item.period_end <= period_end)
    ]
    return BillingCycleHistoryResponse(
        project_id=project_id,
        items=[
            BillingCycleHistoryItemResponse(
                id=item.id,
                period_start=item.period_start,
                period_end=item.period_end,
                invoice_id=item.invoice_id,
                usage_units=item.usage_units,
                closed_by=item.closed_by,
                created_at=item.created_at,
            )
            for item in filtered[offset : offset + limit]
        ],
    )


@router.post("/cycle/run-due", response_model=BillingCycleRunDueResponse)
def run_due_cycle_closure(
    payload: BillingCycleRunDueRequest,
    user: dict[str, str] = Depends(get_current_user),
) -> BillingCycleRunDueResponse:
    ensure_role(user, {"admin", "operator"})
    try:
        report = get_billing_cycle_closer().run_due_cycles(payload.as_of, actor_id=user.get("user_id", "api-key"))
    except RuntimeError as exc:
        _raise_billing_error(409, "billing_job_conflict", str(exc))
    _log_billing_event(
        "billing_cycle_due_job_run",
        user,
        as_of=payload.as_of.isoformat(),
        processed=str(report.processed_subscriptions),
        generated=str(report.generated_invoices),
        failed=str(report.failed_subscriptions),
        duration_ms=str(report.duration_ms),
    )
    return BillingCycleRunDueResponse(
        started_at=report.started_at,
        finished_at=report.finished_at,
        processed_subscriptions=report.processed_subscriptions,
        generated_invoices=report.generated_invoices,
        failed_subscriptions=report.failed_subscriptions,
        duration_ms=report.duration_ms,
        failures=report.failures,
        invoices=[
            BillingInvoiceResponse(
                id=invoice.id,
                project_id=invoice.project_id,
                period_start=invoice.period_start,
                period_end=invoice.period_end,
                status=invoice.status,
                total_cents=invoice.total_cents,
                created_at=invoice.created_at,
            )
            for invoice in report.invoices
        ],
    )


@router.get("/cycle/scheduler/config", response_model=BillingCycleSchedulerConfigResponse)
def billing_scheduler_config(user: dict[str, str] = Depends(get_current_user)) -> BillingCycleSchedulerConfigResponse:
    ensure_role(user, {"admin", "operator", "viewer"}, {ADMIN_READ}, "/billing/cycle/scheduler/config")
    return BillingCycleSchedulerConfigResponse(
        cron_expression="0 * * * *",
        retry_delays_seconds=[1, 3, 10],
        lock_window_scope="daily-window-key",
    )


@router.post("/cycle/run-due/scheduler", response_model=BillingSchedulerRunResponse)
def run_due_cycle_scheduler(
    payload: BillingCycleRunDueRequest,
    user: dict[str, str] = Depends(get_current_user),
) -> BillingSchedulerRunResponse:
    ensure_role(user, {"admin", "operator"}, {ADMIN_READ}, "/billing/cycle/run-due/scheduler")
    result = get_billing_scheduler().run_with_retry(payload.as_of, actor_id=user.get("user_id", "api-key"))
    run_record = BillingSchedulerRunRecord(
        id=str(uuid4()),
        started_at=result.report.started_at if result.report else payload.as_of,
        finished_at=result.report.finished_at if result.report else datetime.now(UTC),
        success=result.success,
        attempts=result.attempts,
        alert_required=result.alert_required,
        processed_subscriptions=result.report.processed_subscriptions if result.report else 0,
        generated_invoices=result.report.generated_invoices if result.report else 0,
        failed_subscriptions=result.report.failed_subscriptions if result.report else 0,
        duration_ms=result.report.duration_ms if result.report else 0,
        error=result.error,
        warnings=result.warnings,
    )
    get_billing_command_model().record_scheduler_run(run_record)
    if result.report is None:
        return BillingSchedulerRunResponse(
            success=result.success,
            attempts=result.attempts,
            alert_required=result.alert_required,
            error=result.error,
            warnings=result.warnings,
            retry_delays_applied=result.retry_delays_applied,
            report=None,
        )
    report = result.report
    return BillingSchedulerRunResponse(
        success=result.success,
        attempts=result.attempts,
        alert_required=result.alert_required,
        error=result.error,
        warnings=result.warnings,
        retry_delays_applied=result.retry_delays_applied,
        report=BillingCycleRunDueResponse(
            started_at=report.started_at,
            finished_at=report.finished_at,
            processed_subscriptions=report.processed_subscriptions,
            generated_invoices=report.generated_invoices,
            failed_subscriptions=report.failed_subscriptions,
            duration_ms=report.duration_ms,
            failures=report.failures,
            invoices=[
                BillingInvoiceResponse(
                    id=invoice.id,
                    project_id=invoice.project_id,
                    period_start=invoice.period_start,
                    period_end=invoice.period_end,
                    status=invoice.status,
                    total_cents=invoice.total_cents,
                    created_at=invoice.created_at,
                )
                for invoice in report.invoices
            ],
        ),
    )


@router.get("/scheduler/runs", response_model=BillingSchedulerRunHistoryResponse)
def scheduler_run_history(
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: dict[str, str] = Depends(get_current_user),
) -> BillingSchedulerRunHistoryResponse:
    ensure_role(user, {"admin", "operator", "viewer"}, {ADMIN_READ}, "/billing/scheduler/runs")
    runs = get_billing_read_model().list_scheduler_runs(limit=limit, offset=offset)
    return BillingSchedulerRunHistoryResponse(
        items=[
            BillingSchedulerRunHistoryItemResponse(
                id=run.id,
                started_at=run.started_at,
                finished_at=run.finished_at,
                success=run.success,
                attempts=run.attempts,
                alert_required=run.alert_required,
                processed_subscriptions=run.processed_subscriptions,
                generated_invoices=run.generated_invoices,
                failed_subscriptions=run.failed_subscriptions,
                duration_ms=run.duration_ms,
                error=run.error,
                warnings=run.warnings,
            )
            for run in runs
        ]
    )


@router.get("/scheduler/runs/latest", response_model=BillingSchedulerRunHistoryItemResponse | None)
def latest_scheduler_run(
    user: dict[str, str] = Depends(get_current_user),
) -> BillingSchedulerRunHistoryItemResponse | None:
    ensure_role(user, {"admin", "operator", "viewer"}, {ADMIN_READ}, "/billing/scheduler/runs/latest")
    run = get_billing_read_model().get_latest_scheduler_run()
    if run is None:
        return None
    return BillingSchedulerRunHistoryItemResponse(
        id=run.id,
        started_at=run.started_at,
        finished_at=run.finished_at,
        success=run.success,
        attempts=run.attempts,
        alert_required=run.alert_required,
        processed_subscriptions=run.processed_subscriptions,
        generated_invoices=run.generated_invoices,
        failed_subscriptions=run.failed_subscriptions,
        duration_ms=run.duration_ms,
        error=run.error,
        warnings=run.warnings,
    )


@router.get("/admin/overview", response_model=BillingAdminOverviewResponse)
def admin_overview(
    user: dict[str, str] = Depends(get_current_user),
) -> BillingAdminOverviewResponse:
    ensure_role(user, {"admin", "operator", "viewer"}, {ADMIN_READ}, "/billing/admin/overview")
    latest = get_billing_read_model().get_latest_scheduler_run()
    alerts = get_billing_read_model().list_scheduler_alerts(limit=10)
    latest_view = (
        BillingSchedulerRunHistoryItemResponse(
            id=latest.id,
            started_at=latest.started_at,
            finished_at=latest.finished_at,
            success=latest.success,
            attempts=latest.attempts,
            alert_required=latest.alert_required,
            processed_subscriptions=latest.processed_subscriptions,
            generated_invoices=latest.generated_invoices,
            failed_subscriptions=latest.failed_subscriptions,
            duration_ms=latest.duration_ms,
            error=latest.error,
            warnings=latest.warnings,
        )
        if latest
        else None
    )
    return BillingAdminOverviewResponse(
        latest_scheduler_run=latest_view,
        recent_alerts=[
            BillingSchedulerRunHistoryItemResponse(
                id=run.id,
                started_at=run.started_at,
                finished_at=run.finished_at,
                success=run.success,
                attempts=run.attempts,
                alert_required=run.alert_required,
                processed_subscriptions=run.processed_subscriptions,
                generated_invoices=run.generated_invoices,
                failed_subscriptions=run.failed_subscriptions,
                duration_ms=run.duration_ms,
                error=run.error,
                warnings=run.warnings,
            )
            for run in alerts
        ],
    )
