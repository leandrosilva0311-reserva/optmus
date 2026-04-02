from datetime import UTC, datetime, timedelta
from dataclasses import replace

from optimus_backend.application.jobs.billing_cycle_closer import BillingCycleCloser
from optimus_backend.infrastructure.billing.in_memory_billing_store import InMemoryBillingStore


def test_run_due_cycles_closes_due_subscription() -> None:
    store = InMemoryBillingStore()
    sub = store.create_or_activate_subscription("p-due", "starter")
    assert sub.renews_at is not None
    store._subscriptions["p-due"] = replace(sub, renews_at=datetime.now(UTC) - timedelta(minutes=1))  # noqa: SLF001
    closer = BillingCycleCloser(read_model=store, command_model=store)
    invoices = closer.run_due_cycles(datetime.now(UTC))
    assert len(invoices) == 1
    assert invoices[0].project_id == "p-due"
