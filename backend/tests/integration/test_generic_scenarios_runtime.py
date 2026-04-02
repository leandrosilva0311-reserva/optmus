import pytest

pytest.importorskip("fastapi")

import json

from optimus_backend.api.dependencies import (
    get_engine,
    get_repositories,
    get_scenario_catalog,
    get_start_execution_use_case,
    get_tool_executor,
    get_usage_meter,
    get_billing_read_model,
)
from optimus_backend.application.use_cases.run_scenario import RunScenarioUseCase
from optimus_backend.infrastructure.queue.worker import run_execution_job
from optimus_backend.settings.config import config


def _reset_test_env() -> tuple[object, object, object]:
    config.app_env = "test"
    get_repositories.cache_clear()
    get_tool_executor.cache_clear()
    get_engine.cache_clear()
    repositories = get_repositories()
    executions, _, audit, _, _, _, _, _, _ = repositories
    return executions, audit, repositories


def test_public_api_health_generates_business_block() -> None:
    executions, audit, _ = _reset_test_env()
    use_case = RunScenarioUseCase(get_start_execution_use_case(), executions, get_scenario_catalog(), audit, get_usage_meter(), get_billing_read_model())
    result = use_case.execute(
        project_id="proj-1",
        scenario_id="public_api_health",
        objective="Validate API uptime and queue pressure",
        inputs={
            "request_id": "req-1",
            "execution_id": "exec-input-1",
            "order_id": "ord-1",
            "restaurant_id": "tenant-1",
            "time_window_start": "2026-04-01T10:00:00Z",
            "time_window_end": "2026-04-01T11:00:00Z",
        },
    )

    run_execution_job({}, result.execution_id)
    events = audit.list_by_execution(result.execution_id)
    business = [e for e in events if e.event_type == "business_block"]
    assert business
    payload = json.loads(business[-1].message)
    assert payload["operational_impact"]
    assert payload["commercial_impact"]
    assert payload["severity"] in {"low", "medium", "high", "critical"}
    assert payload["immediate_action"]
    assert payload["suggested_owner"]


def test_queue_health_executes_with_required_inputs() -> None:
    executions, audit, _ = _reset_test_env()
    use_case = RunScenarioUseCase(get_start_execution_use_case(), executions, get_scenario_catalog(), audit, get_usage_meter(), get_billing_read_model())
    result = use_case.execute(
        project_id="proj-2",
        scenario_id="queue_health",
        objective="Inspect queue backlog and latency",
        inputs={
            "request_id": "req-2",
            "execution_id": "exec-input-2",
            "restaurant_id": "tenant-2",
            "time_window_start": "2026-04-01T08:00:00Z",
            "time_window_end": "2026-04-01T09:00:00Z",
        },
    )

    run_execution_job({}, result.execution_id)
    updated = executions.get(result.execution_id)
    assert updated is not None
    assert updated.status in {"completed", "bounded_completion"}

    tool_events = [e for e in audit.list_by_execution(result.execution_id) if e.event_type == "tool_envelope"]
    assert tool_events


def test_checkout_flow_validation_generates_business_block() -> None:
    executions, audit, _ = _reset_test_env()
    use_case = RunScenarioUseCase(get_start_execution_use_case(), executions, get_scenario_catalog(), audit, get_usage_meter(), get_billing_read_model())
    result = use_case.execute(
        project_id="proj-3",
        scenario_id="checkout_flow_validation",
        objective="Validate checkout consistency",
        inputs={
            "request_id": "req-3",
            "execution_id": "exec-input-3",
            "order_id": "ord-3",
            "restaurant_id": "tenant-3",
            "time_window_start": "2026-04-01T12:00:00Z",
            "time_window_end": "2026-04-01T13:00:00Z",
        },
    )

    run_execution_job({}, result.execution_id)
    business = [e for e in audit.list_by_execution(result.execution_id) if e.event_type == "business_block"]
    assert business
    payload = json.loads(business[-1].message)
    assert payload["suggested_owner"] in {"QAAgent", "OpsAgent"}


def test_incident_timeline_reconstruction_generates_business_block() -> None:
    executions, audit, _ = _reset_test_env()
    use_case = RunScenarioUseCase(get_start_execution_use_case(), executions, get_scenario_catalog(), audit, get_usage_meter(), get_billing_read_model())
    result = use_case.execute(
        project_id="proj-4",
        scenario_id="incident_timeline_reconstruction",
        objective="Reconstruct incident timeline",
        inputs={
            "request_id": "req-4",
            "execution_id": "exec-input-4",
            "restaurant_id": "tenant-4",
            "time_window_start": "2026-04-01T14:00:00Z",
            "time_window_end": "2026-04-01T15:00:00Z",
        },
    )

    run_execution_job({}, result.execution_id)
    business = [e for e in audit.list_by_execution(result.execution_id) if e.event_type == "business_block"]
    assert business
    payload = json.loads(business[-1].message)
    assert payload["suggested_owner"] in {"AnalystAgent", "OpsAgent"}
