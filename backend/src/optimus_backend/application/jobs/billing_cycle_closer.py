from datetime import UTC, datetime, timedelta

from optimus_backend.domain.entities import InvoiceRecord
from optimus_backend.domain.ports import BillingCommandModel, BillingReadModel


class BillingCycleCloser:
    def __init__(self, read_model: BillingReadModel, command_model: BillingCommandModel) -> None:
        self._read_model = read_model
        self._command_model = command_model

    def run_due_cycles(self, as_of: datetime, actor_id: str = "billing-job") -> list[InvoiceRecord]:
        as_of_utc = as_of.astimezone(UTC)
        invoices: list[InvoiceRecord] = []
        for sub in self._read_model.list_active_subscriptions_due(as_of_utc):
            if sub.renews_at is None:
                continue
            period_end = sub.renews_at
            period_start = period_end - timedelta(days=30)
            invoice = self._command_model.close_billing_cycle(
                project_id=sub.project_id,
                period_start=period_start,
                period_end=period_end,
                actor_id=actor_id,
            )
            invoices.append(invoice)
        return invoices
