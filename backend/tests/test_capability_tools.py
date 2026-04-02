import pytest

from optimus_backend.infrastructure.adapters.domains.kaiso.observability import (
    KaisoLogCorrelationAdapter,
    KaisoQueueInspectionAdapter,
)
from optimus_backend.infrastructure.tools.log_correlation_tool import LogCorrelationTool
from optimus_backend.infrastructure.tools.queue_inspection_tool import QueueInspectionTool


def test_log_correlation_requires_formal_keys() -> None:
    tool = LogCorrelationTool(KaisoLogCorrelationAdapter())
    with pytest.raises(ValueError):
        tool.run({"request_id": "req-1"})


def test_queue_inspection_returns_mandatory_metrics() -> None:
    tool = QueueInspectionTool(KaisoQueueInspectionAdapter())
    output, truncated = tool.run(
        {
            "restaurant_id": "rest-9",
            "time_window_start": "2026-03-30T10:00:00Z",
            "time_window_end": "2026-03-30T11:00:00Z",
        }
    )
    assert truncated is False
    assert "backlog_size" in output
    assert "oldest_job_age_seconds" in output
    assert "failed_jobs_count" in output
    assert "estimated_processing_latency_ms" in output
