from datetime import UTC, datetime, timedelta
from dataclasses import dataclass
import logging

from optimus_backend.domain.entities import InvoiceRecord
from optimus_backend.domain.ports import BillingCommandModel, BillingReadModel, LockManager


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BillingCycleRunReport:
    started_at: datetime
    finished_at: datetime
    processed_subscriptions: int
    generated_invoices: int
    failed_subscriptions: int
    duration_ms: int
    invoices: list[InvoiceRecord]
    failures: list[str]


class BillingCycleCloser:
    def __init__(self, read_model: BillingReadModel, command_model: BillingCommandModel, lock_manager: LockManager) -> None:
        self._read_model = read_model
        self._command_model = command_model
        self._lock_manager = lock_manager

    def run_due_cycles(self, as_of: datetime, actor_id: str = "billing-job") -> BillingCycleRunReport:
        started = datetime.now(UTC)
        as_of_utc = as_of.astimezone(UTC)
        lock_key = f"billing:run_due:{as_of_utc.date().isoformat()}"
        if not self._lock_manager.acquire(lock_key, ttl_seconds=300):
            raise RuntimeError("billing due-cycle run already in progress for this window")
        invoices: list[InvoiceRecord] = []
        failures: list[str] = []
        subscriptions = self._read_model.list_active_subscriptions_due(as_of_utc)
        logger.info(
            "billing_cycle_due_run_started",
            extra={
                "execution_id": f"billing-cycle-{as_of_utc.date().isoformat()}",
                "agent_id": actor_id,
                "event_type": "billing_cycle_due_run_started",
                "subscriptions_due": str(len(subscriptions)),
            },
        )
        try:
            for sub in subscriptions:
                if sub.renews_at is None:
                    continue
                period_end = sub.renews_at
                period_start = period_end - timedelta(days=30)
                try:
                    invoice = self._command_model.close_billing_cycle(
                        project_id=sub.project_id,
                        period_start=period_start,
                        period_end=period_end,
                        actor_id=actor_id,
                    )
                    invoices.append(invoice)
                except Exception:
                    failures.append(sub.project_id)
            finished = datetime.now(UTC)
            duration_ms = int((finished - started).total_seconds() * 1000)
            logger.info(
                "billing_cycle_due_run_finished",
                extra={
                    "execution_id": f"billing-cycle-{as_of_utc.date().isoformat()}",
                    "agent_id": actor_id,
                    "event_type": "billing_cycle_due_run_finished",
                    "processed_subscriptions": str(len(subscriptions)),
                    "generated_invoices": str(len(invoices)),
                    "failed_subscriptions": str(len(failures)),
                    "duration_ms": str(duration_ms),
                },
            )
            return BillingCycleRunReport(
                started_at=started,
                finished_at=finished,
                processed_subscriptions=len(subscriptions),
                generated_invoices=len(invoices),
                failed_subscriptions=len(failures),
                duration_ms=duration_ms,
                invoices=invoices,
                failures=failures,
            )
        finally:
            self._lock_manager.release(lock_key)
