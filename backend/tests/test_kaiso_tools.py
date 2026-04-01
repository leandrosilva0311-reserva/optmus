import pytest

from optimus_backend.infrastructure.tools.kaiso_log_correlation_tool import (
    InMemoryKaisoLogCorrelationProvider,
    KaisoLogCorrelationTool,
)
from optimus_backend.infrastructure.tools.kaiso_queue_inspection_tool import (
    InMemoryKaisoQueueInspectionProvider,
    KaisoQueueInspectionTool,
)


def test_kaiso_log_correlation_requires_formal_keys() -> None:
    tool = KaisoLogCorrelationTool(InMemoryKaisoLogCorrelationProvider())
    with pytest.raises(ValueError):
        tool.run({"request_id": "req-1"})


def test_kaiso_queue_inspection_returns_mandatory_metrics() -> None:
    tool = KaisoQueueInspectionTool(InMemoryKaisoQueueInspectionProvider())
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
