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
    warnings: list[str]
    retry_delays_applied: list[int]


class BillingScheduler:
    def __init__(self, closer: BillingCycleCloser, retry_delays_seconds: list[int] | None = None) -> None:
        self._closer = closer
        self._retry_delays = retry_delays_seconds or [1, 3, 10]

    def run_with_retry(self, as_of: datetime, actor_id: str = "billing-scheduler") -> BillingSchedulerRunResult:
        attempts = 0
        last_error = "unknown error"
        warnings: list[str] = []
        retry_delays_applied: list[int] = []
        for delay in [0, *self._retry_delays]:
            attempts += 1
            if delay > 0:
                time.sleep(delay)
                retry_delays_applied.append(delay)
            try:
                report = self._closer.run_due_cycles(as_of=as_of, actor_id=actor_id)
                return BillingSchedulerRunResult(True, attempts, False, report, None, warnings, retry_delays_applied)
            except RuntimeError as exc:
                warnings.append("overlap_guard_triggered")
                return BillingSchedulerRunResult(False, attempts, True, None, str(exc), warnings, retry_delays_applied)
            except Exception as exc:
                last_error = str(exc)
                warnings.append("transient_failure_retry")
        return BillingSchedulerRunResult(False, attempts, True, None, last_error, warnings, retry_delays_applied)
