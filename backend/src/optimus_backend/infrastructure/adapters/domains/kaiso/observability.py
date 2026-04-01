from optimus_backend.core.provider.capabilities import LogCorrelationProvider, QueueInspectionProvider


class KaisoLogCorrelationAdapter(LogCorrelationProvider):
    def correlate(
        self,
        *,
        request_id: str,
        execution_id: str,
        order_id: str,
        restaurant_id: str,
        time_window_start: str,
        time_window_end: str,
    ) -> str:
        return (
            "correlation_ok "
            f"request_id={request_id} execution_id={execution_id} order_id={order_id} "
            f"restaurant_id={restaurant_id} time_window={time_window_start}..{time_window_end}"
        )


class KaisoQueueInspectionAdapter(QueueInspectionProvider):
    def inspect(self, *, restaurant_id: str, time_window_start: str, time_window_end: str) -> dict[str, float | int]:
        _ = (time_window_start, time_window_end)
        return {
            "restaurant_id": restaurant_id,
            "backlog_size": 12,
            "oldest_job_age_seconds": 244,
            "failed_jobs_count": 1,
            "estimated_processing_latency_ms": 1800,
        }
