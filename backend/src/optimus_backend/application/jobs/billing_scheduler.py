from dataclasses import dataclass
from datetime import datetime
import time

from optimus_backend.application.jobs.billing_cycle_closer import BillingCycleCloser, BillingCycleRunReport


@dataclass(slots=True)
class BillingSchedulerRunResult:
    success: bool
    attempts: int
    alert_required: bool
    report: BillingCycleRunReport | None
    error: str | None


class BillingScheduler:
    def __init__(self, closer: BillingCycleCloser, retry_delays_seconds: list[int] | None = None) -> None:
        self._closer = closer
        self._retry_delays = retry_delays_seconds or [1, 3, 10]

    def run_with_retry(self, as_of: datetime, actor_id: str = "billing-scheduler") -> BillingSchedulerRunResult:
        attempts = 0
        last_error = "unknown error"
        for delay in [0, *self._retry_delays]:
            attempts += 1
            if delay > 0:
                time.sleep(delay)
            try:
                report = self._closer.run_due_cycles(as_of=as_of, actor_id=actor_id)
                return BillingSchedulerRunResult(True, attempts, False, report, None)
            except RuntimeError as exc:
                return BillingSchedulerRunResult(False, attempts, True, None, str(exc))
            except Exception as exc:
                last_error = str(exc)
        return BillingSchedulerRunResult(False, attempts, True, None, last_error)
