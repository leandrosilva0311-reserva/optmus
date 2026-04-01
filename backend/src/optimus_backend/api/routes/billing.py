from datetime import UTC, datetime, timedelta
import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from optimus_backend.api.dependencies import (
    get_billing_command_model,
    get_billing_read_model,
    get_current_user,
    get_usage_meter,
)
from optimus_backend.core.usage.metering import warning_for_ratio
from optimus_backend.schemas.billing import (
    BillingCycleCloseRequest,
    BillingInvoiceDetailResponse,
    BillingInvoiceItemResponse,
    BillingInvoiceResponse,
    BillingPlanChangeRequest,
    BillingPlanChangeHistoryResponse,
    BillingPlanChangeResponse,
    BillingPlanResponse,
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
    payload = {"execution_id": "billing-api", "agent_id": user["user_id"], "event_type": event_type, **extra}
    logger.info("billing_event", extra=payload)


def ensure_role(user: dict[str, str], allowed: set[str]) -> None:
    if user["role"] not in allowed:
        raise HTTPException(status_code=403, detail="insufficient role")


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
        )
        for plan in plans
    ]


@router.post("/subscription", response_model=BillingSubscriptionResponse)
def create_or_activate_subscription(
    payload: BillingSubscriptionCreateRequest,
    user: dict[str, str] = Depends(get_current_user),
) -> BillingSubscriptionResponse:
    ensure_role(user, {"admin", "operator"})
    sub = get_billing_command_model().create_or_activate_subscription(payload.project_id, payload.plan_id, actor_id=user["user_id"])
    _log_billing_event("subscription_activated", user, project_id=payload.project_id, plan_id=payload.plan_id)
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
    ensure_role(user, {"admin", "operator", "viewer"})
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
    ensure_role(user, {"admin", "operator", "viewer"})
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
    ensure_role(user, {"admin", "operator", "viewer"})
    now = datetime.now(UTC)
    date_from = now - timedelta(days=days)
    history = get_billing_read_model().usage_history(project_id, date_from, now)
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
            actor_id=user["user_id"],
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
    user: dict[str, str] = Depends(get_current_user),
) -> list[BillingInvoiceResponse]:
    ensure_role(user, {"admin", "operator", "viewer"})
    invoices = get_billing_read_model().list_invoices(project_id)
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
        for inv in invoices
    ]


@router.get("/invoices/detail", response_model=BillingInvoiceDetailResponse)
def invoice_detail(
    project_id: str = Query(...),
    invoice_id: str = Query(...),
    user: dict[str, str] = Depends(get_current_user),
) -> BillingInvoiceDetailResponse:
    ensure_role(user, {"admin", "operator", "viewer"})
    models = get_billing_read_model()
    invoice = next((inv for inv in models.list_invoices(project_id=project_id) if inv.id == invoice_id), None)
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
    user: dict[str, str] = Depends(get_current_user),
) -> BillingPlanChangeHistoryResponse:
    ensure_role(user, {"admin", "operator", "viewer"})
    items = get_billing_read_model().list_plan_changes(project_id)
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
            for change in items
        ],
    )
