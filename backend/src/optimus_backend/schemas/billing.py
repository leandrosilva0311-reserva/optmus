from datetime import datetime

from pydantic import BaseModel


class BillingPlanResponse(BaseModel):
    plan_id: str
    name: str
    daily_scenario_limit: int
    monthly_price_cents: int
    usage_unit_price_cents: int


class BillingSubscriptionCreateRequest(BaseModel):
    project_id: str
    plan_id: str


class BillingSubscriptionActivateRequest(BaseModel):
    project_id: str


class BillingPlanChangeRequest(BaseModel):
    project_id: str
    new_plan_id: str


class BillingPlanChangeResponse(BaseModel):
    id: str
    project_id: str
    from_plan_id: str
    to_plan_id: str
    effective_at: datetime
    status: str


class BillingPlanChangeHistoryResponse(BaseModel):
    project_id: str
    items: list[BillingPlanChangeResponse]


class BillingSubscriptionResponse(BaseModel):
    id: str
    project_id: str
    plan_id: str
    status: str
    started_at: datetime
    renews_at: datetime | None


class BillingUsageCurrentResponse(BaseModel):
    project_id: str
    plan_id: str
    consumed_today: int
    daily_limit: int
    remaining_today: int
    warning_level: str


class BillingUsageHistoryItemResponse(BaseModel):
    event_date: str
    units: int


class BillingUsageHistoryResponse(BaseModel):
    project_id: str
    items: list[BillingUsageHistoryItemResponse]


class BillingCycleCloseRequest(BaseModel):
    project_id: str
    period_start: datetime
    period_end: datetime


class BillingCycleRunDueRequest(BaseModel):
    as_of: datetime


class BillingInvoiceResponse(BaseModel):
    id: str
    project_id: str
    period_start: datetime
    period_end: datetime
    status: str
    total_cents: int
    created_at: datetime


class BillingInvoiceItemResponse(BaseModel):
    id: str
    item_type: str
    quantity: int
    unit_price_cents: int
    total_cents: int
    description: str


class BillingInvoiceDetailResponse(BillingInvoiceResponse):
    items: list[BillingInvoiceItemResponse]


class BillingInvoiceStatusChangeRequest(BaseModel):
    invoice_id: str
    to_status: str


class BillingInvoiceStatusTransitionResponse(BaseModel):
    id: str
    invoice_id: str
    from_status: str
    to_status: str
    changed_by: str
    changed_at: datetime


class BillingInvoiceHistoryEntryResponse(BillingInvoiceResponse):
    item_count: int
    transitions: list[BillingInvoiceStatusTransitionResponse]


class BillingInvoiceHistoryResponse(BaseModel):
    project_id: str
    items: list[BillingInvoiceHistoryEntryResponse]


class BillingCycleHistoryItemResponse(BaseModel):
    id: str
    period_start: datetime
    period_end: datetime
    invoice_id: str
    usage_units: int
    closed_by: str
    created_at: datetime


class BillingCycleHistoryResponse(BaseModel):
    project_id: str
    items: list[BillingCycleHistoryItemResponse]


class BillingCycleRunDueResponse(BaseModel):
    started_at: datetime
    finished_at: datetime
    processed_subscriptions: int
    generated_invoices: int
    failed_subscriptions: int
    duration_ms: int
    failures: list[str]
    invoices: list[BillingInvoiceResponse]


class BillingCycleSchedulerConfigResponse(BaseModel):
    cron_expression: str
    retry_delays_seconds: list[int]
    lock_window_scope: str


class BillingSchedulerRunResponse(BaseModel):
    success: bool
    attempts: int
    alert_required: bool
    error: str | None
    warnings: list[str]
    retry_delays_applied: list[int]
    report: BillingCycleRunDueResponse | None


class BillingSchedulerRunHistoryItemResponse(BaseModel):
    id: str
    started_at: datetime
    finished_at: datetime
    success: bool
    attempts: int
    alert_required: bool
    processed_subscriptions: int
    generated_invoices: int
    failed_subscriptions: int
    duration_ms: int
    error: str | None
    warnings: list[str]


class BillingSchedulerRunHistoryResponse(BaseModel):
    items: list[BillingSchedulerRunHistoryItemResponse]


class BillingAdminOverviewResponse(BaseModel):
    latest_scheduler_run: BillingSchedulerRunHistoryItemResponse | None
    recent_alerts: list[BillingSchedulerRunHistoryItemResponse]
