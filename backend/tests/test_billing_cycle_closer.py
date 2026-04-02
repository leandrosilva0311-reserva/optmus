from datetime import UTC, datetime, timedelta
from dataclasses import replace

from optimus_backend.application.jobs.billing_cycle_closer import BillingCycleCloser
from optimus_backend.infrastructure.billing.in_memory_billing_store import InMemoryBillingStore
from optimus_backend.infrastructure.persistence.in_memory import InMemoryLockManager


def test_run_due_cycles_closes_due_subscription() -> None:
    store = InMemoryBillingStore()
    sub = store.create_or_activate_subscription("p-due", "starter")
    assert sub.renews_at is not None
    store._subscriptions["p-due"] = replace(sub, renews_at=datetime.now(UTC) - timedelta(minutes=1))  # noqa: SLF001
    closer = BillingCycleCloser(read_model=store, command_model=store, lock_manager=InMemoryLockManager())
    report = closer.run_due_cycles(datetime.now(UTC))
    assert report.processed_subscriptions == 1
    assert report.generated_invoices == 1
    assert report.failed_subscriptions == 0
    assert len(report.invoices) == 1
    assert report.invoices[0].project_id == "p-due"


def test_run_due_cycles_conflict_when_lock_not_acquired() -> None:
    store = InMemoryBillingStore()
    lock = InMemoryLockManager()
    as_of = datetime.now(UTC)
    lock.acquire(f"billing:run_due:{as_of.date().isoformat()}", ttl_seconds=300)
    closer = BillingCycleCloser(read_model=store, command_model=store, lock_manager=lock)

    try:
        closer.run_due_cycles(as_of)
    except RuntimeError as exc:
        assert "already in progress" in str(exc)
    else:
        raise AssertionError("RuntimeError expected")
