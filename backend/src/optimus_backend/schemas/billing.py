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
