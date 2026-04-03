from datetime import UTC, datetime

from optimus_backend.application.jobs.billing_scheduler import BillingScheduler


class _FailingCloser:
    def __init__(self) -> None:
        self.calls = 0

    def run_due_cycles(self, as_of: datetime, actor_id: str = "billing-scheduler"):  # type: ignore[no-untyped-def]
        self.calls += 1
        if self.calls < 2:
            raise ValueError("temporary failure")
        return type(
            "Report",
            (),
            {
                "started_at": as_of,
                "finished_at": as_of,
                "processed_subscriptions": 1,
                "generated_invoices": 1,
                "failed_subscriptions": 0,
                "duration_ms": 1,
                "failures": [],
                "invoices": [],
            },
        )()


def test_scheduler_retries_and_succeeds() -> None:
    scheduler = BillingScheduler(_FailingCloser(), retry_delays_seconds=[0])  # type: ignore[arg-type]
    result = scheduler.run_with_retry(datetime.now(UTC))
    assert result.success is True
    assert result.attempts == 2
    assert result.alert_required is False
