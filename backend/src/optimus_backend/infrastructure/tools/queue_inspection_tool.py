from optimus_backend.core.provider.capabilities import QueueInspectionProvider


class QueueInspectionTool:
    name = "queue_inspection"

    def __init__(self, provider: QueueInspectionProvider) -> None:
        self._provider = provider

    def run(self, payload: dict) -> tuple[str, bool]:
        required = ("restaurant_id", "time_window_start", "time_window_end")
        missing = [key for key in required if not payload.get(key)]
        if missing:
            raise ValueError(f"missing required queue inspection fields: {', '.join(missing)}")
        metrics = self._provider.inspect(
            restaurant_id=str(payload["restaurant_id"]),
            time_window_start=str(payload["time_window_start"]),
            time_window_end=str(payload["time_window_end"]),
        )
        expected = (
            "backlog_size",
            "oldest_job_age_seconds",
            "failed_jobs_count",
            "estimated_processing_latency_ms",
        )
        for metric in expected:
            if metric not in metrics:
                raise RuntimeError(f"missing mandatory metric: {metric}")
        return str(metrics), False
