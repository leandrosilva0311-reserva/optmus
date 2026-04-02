from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from optimus_backend.domain.entities import (
    BillingCycleClosureRecord,
    InvoiceRecord,
    InvoiceItemRecord,
    PlanDefinitionRecord,
    SubscriptionPlanChangeRecord,
    SubscriptionRecord,
    UsageHistoryRecord,
)


class InMemoryBillingStore:
    def __init__(self) -> None:
        self._plans = {
            "starter": PlanDefinitionRecord("starter", "Starter", 50, 4900, 100, True),
            "growth": PlanDefinitionRecord("growth", "Growth", 250, 19900, 80, True),
            "enterprise": PlanDefinitionRecord("enterprise", "Enterprise", 2000, 99900, 50, True),
        }
        now = datetime.now(UTC)
        self._subscriptions: dict[str, SubscriptionRecord] = {
            "default": SubscriptionRecord(
                id="sub-default",
                project_id="default",
                plan_id="starter",
                status="active",
                started_at=now,
                renews_at=now + timedelta(days=30),
                cancelled_at=None,
            )
        }
        self._changes: list[SubscriptionPlanChangeRecord] = []
        self._invoices: list[InvoiceRecord] = []
        self._invoice_items: list[InvoiceItemRecord] = []
        self._closures: list[BillingCycleClosureRecord] = []
        self._usage: list[UsageHistoryRecord] = []

    def list_active_plans(self) -> list[PlanDefinitionRecord]:
        return [p for p in self._plans.values() if p.active]

    def get_plan(self, plan_id: str) -> PlanDefinitionRecord | None:
        return self._plans.get(plan_id)

    def get_active_subscription(self, project_id: str) -> SubscriptionRecord | None:
        sub = self._subscriptions.get(project_id)
        if sub and sub.status in {"active", "cancelling"}:
            return sub
        return None

    def list_invoices(self, project_id: str) -> list[InvoiceRecord]:
        return [i for i in self._invoices if i.project_id == project_id]

    def list_invoice_items(self, invoice_id: str) -> list[InvoiceItemRecord]:
        return [i for i in self._invoice_items if i.invoice_id == invoice_id]

    def usage_history(self, project_id: str, date_from: datetime, date_to: datetime) -> list[UsageHistoryRecord]:
        return [u for u in self._usage if u.event_date and date_from <= u.event_date <= date_to]

    def list_plan_changes(self, project_id: str) -> list[SubscriptionPlanChangeRecord]:
        return [change for change in self._changes if change.project_id == project_id]

    def list_cycle_closures(self, project_id: str) -> list[BillingCycleClosureRecord]:
        return [closure for closure in self._closures if closure.project_id == project_id]

    def list_active_subscriptions_due(self, as_of: datetime) -> list[SubscriptionRecord]:
        return [
            sub
            for sub in self._subscriptions.values()
            if sub.status in {"active", "cancelling"} and sub.renews_at is not None and sub.renews_at <= as_of
        ]

    def create_subscription(self, project_id: str, plan_id: str, actor_id: str = "system") -> SubscriptionRecord:
        _ = actor_id
        sub = SubscriptionRecord(
            id=str(uuid4()),
            project_id=project_id,
            plan_id=plan_id,
            status="pending_activation",
            started_at=datetime.now(UTC),
            renews_at=None,
            cancelled_at=None,
        )
        self._subscriptions[project_id] = sub
        return sub

    def activate_subscription(self, project_id: str, actor_id: str = "system") -> SubscriptionRecord:
        _ = actor_id
        sub = self._subscriptions.get(project_id)
        if sub is None:
            raise KeyError("subscription not found")
        if sub.status not in {"pending_activation", "active", "cancelling"}:
            raise ValueError("subscription cannot be activated")
        now = datetime.now(UTC)
        activated = replace(sub, status="active", started_at=now, renews_at=now + timedelta(days=30))
        self._subscriptions[project_id] = activated
        return activated

    def create_or_activate_subscription(self, project_id: str, plan_id: str, actor_id: str = "system") -> SubscriptionRecord:
        self.create_subscription(project_id, plan_id, actor_id=actor_id)
        return self.activate_subscription(project_id, actor_id=actor_id)

    def change_plan(self, project_id: str, new_plan_id: str) -> SubscriptionPlanChangeRecord:
        sub = self.get_active_subscription(project_id)
        if sub is None:
            raise KeyError("active subscription not found")
        old_plan = self._plans[sub.plan_id]
        new_plan = self._plans[new_plan_id]
        now = datetime.now(UTC)

        if new_plan.monthly_price_cents > old_plan.monthly_price_cents:
            self._subscriptions[project_id] = replace(sub, plan_id=new_plan_id)
            status = "applied"
            effective_at = now
        else:
            status = "scheduled"
            effective_at = sub.renews_at or (now + timedelta(days=30))

        change = SubscriptionPlanChangeRecord(
            id=str(uuid4()),
            project_id=project_id,
            from_plan_id=sub.plan_id,
            to_plan_id=new_plan_id,
            effective_at=effective_at,
            status=status,
            created_at=now,
        )
        self._changes.append(change)
        return change

    def cancel_subscription(self, project_id: str) -> SubscriptionRecord:
        sub = self.get_active_subscription(project_id)
        if sub is None:
            raise KeyError("active subscription not found")
        updated = replace(sub, status="cancelling", cancelled_at=sub.renews_at)
        self._subscriptions[project_id] = updated
        return updated

    def close_billing_cycle(
        self,
        project_id: str,
        period_start: datetime,
        period_end: datetime,
        actor_id: str = "system",
    ) -> InvoiceRecord:
        _ = actor_id
        if period_start >= period_end:
            raise ValueError("period_start must be before period_end")
        sub = self.get_active_subscription(project_id)
        if sub is None:
            raise KeyError("active subscription not found")
        for existing in self._invoices:
            if existing.project_id == project_id and existing.period_start == period_start and existing.period_end == period_end:
                return existing
        plan = self._plans[sub.plan_id]
        usage_units = sum(item.units for item in self._usage if item.event_date and period_start <= item.event_date <= period_end)
        usage_total_cents = usage_units * plan.usage_unit_price_cents
        subtotal = plan.monthly_price_cents + usage_total_cents
        invoice = InvoiceRecord(
            id=str(uuid4()),
            project_id=project_id,
            period_start=period_start,
            period_end=period_end,
            status="open",
            total_cents=subtotal,
            created_at=datetime.now(UTC),
        )
        self._invoices.append(invoice)
        self._invoice_items.append(
            InvoiceItemRecord(str(uuid4()), invoice.id, "subscription_fee", 1, plan.monthly_price_cents, plan.monthly_price_cents, f"Plano {plan.name}")
        )
        if usage_units > 0:
                self._invoice_items.append(
                InvoiceItemRecord(
                    str(uuid4()),
                    invoice.id,
                    "usage_fee",
                    usage_units,
                    plan.usage_unit_price_cents,
                    usage_total_cents,
                    "Consumo de cenários no período",
                )
            )
        self._closures.append(
            BillingCycleClosureRecord(str(uuid4()), project_id, period_start, period_end, invoice.id, usage_units, "system", datetime.now(UTC))
        )

        for idx, change in enumerate(self._changes):
            if change.project_id != project_id or change.status != "scheduled":
                continue
            if change.effective_at <= period_end:
                self._subscriptions[project_id] = replace(sub, plan_id=change.to_plan_id)
                self._changes[idx] = replace(change, status="applied")
        return invoice
