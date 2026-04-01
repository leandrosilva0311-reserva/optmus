from datetime import UTC, datetime, timedelta

from optimus_backend.infrastructure.billing.in_memory_billing_store import InMemoryBillingStore


def test_subscription_lifecycle_and_cycle_close() -> None:
    store = InMemoryBillingStore()

    sub = store.create_or_activate_subscription("p-billing", "starter")
    assert sub.status == "active"

    change = store.change_plan("p-billing", "growth")
    assert change.status == "applied"

    cancel = store.cancel_subscription("p-billing")
    assert cancel.status == "cancelling"

    invoice = store.close_billing_cycle(
        "p-billing",
        period_start=datetime.now(UTC) - timedelta(days=30),
        period_end=datetime.now(UTC),
    )
    assert invoice.total_cents > 0
    assert store.list_invoices("p-billing")


def test_downgrade_is_scheduled_and_applied_on_cycle_close() -> None:
    store = InMemoryBillingStore()
    store.create_or_activate_subscription("p-downgrade", "growth")

    change = store.change_plan("p-downgrade", "starter")
    assert change.status == "scheduled"

    sub_before = store.get_active_subscription("p-downgrade")
    assert sub_before is not None
    assert sub_before.plan_id == "growth"

    store.close_billing_cycle(
        "p-downgrade",
        period_start=datetime.now(UTC) - timedelta(days=30),
        period_end=datetime.now(UTC) + timedelta(days=31),
    )
    sub_after = store.get_active_subscription("p-downgrade")
    assert sub_after is not None
    assert sub_after.plan_id == "starter"


def test_cycle_close_is_idempotent_for_same_period() -> None:
    store = InMemoryBillingStore()
    store.create_or_activate_subscription("p-idem", "starter")
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)

    first = store.close_billing_cycle("p-idem", start, end)
    second = store.close_billing_cycle("p-idem", start, end)
    assert first.id == second.id
    assert len(store.list_invoices("p-idem")) == 1
