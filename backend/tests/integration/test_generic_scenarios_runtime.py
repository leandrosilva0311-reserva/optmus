import pytest

pytest.importorskip("fastapi")

import json
from pathlib import Path

from optimus_backend.api.dependencies import (
    get_billing_read_model,
    get_engine,
    get_repositories,
    get_scenario_catalog,
    get_start_execution_use_case,
    get_tool_executor,
    get_usage_meter,
)
from optimus_backend.application.use_cases.run_scenario import RunScenarioUseCase
from optimus_backend.infrastructure.queue.worker import run_execution_job
from optimus_backend.infrastructure.source_connectors.git_local_connector import GitLocalSourceConnector
from optimus_backend.settings.config import config


def _reset_test_env() -> tuple[object, object, object]:
    config.app_env = "test"
    get_repositories.cache_clear()
    get_tool_executor.cache_clear()
    get_engine.cache_clear()
    repositories = get_repositories()
    executions, _, audit, _, _, _, _, _, _ = repositories
    return executions, audit, repositories


def _assert_engineering_report(payload: dict[str, object]) -> None:
    assert payload["execution_id"]
    assert payload["scenario_id"]
    assert payload["diagnosis"]
    assert payload["evidence"]
    assert payload["recommendations"]
    assert payload["risk_level"] in {"low", "medium", "high", "critical"}
    assert payload["urgency"] in {"low", "medium", "high", "immediate"}
    assert payload["execution_plan"]
    assert payload["generated_at"]


def test_code_analysis_generates_engineering_report_event() -> None:
    executions, audit, _ = _reset_test_env()
    use_case = RunScenarioUseCase(get_start_execution_use_case(), executions, get_scenario_catalog(), audit, get_usage_meter(), get_billing_read_model())
    result = use_case.execute(
        project_id="proj-1",
        scenario_id="code_analysis",
        objective="analisar acoplamento",
        inputs={
            "stack": "python",
            "objective": "reduzir acoplamento",
            "files": [{"path": "src/a.py", "content": "def run():\n    return 1"}],
        },
    )

    run_execution_job({}, result.execution_id)
    events = audit.list_by_execution(result.execution_id)
    reports = [e for e in events if e.event_type == "engineering_report"]
    assert reports
    payload = json.loads(reports[-1].message)
    _assert_engineering_report(payload)


def test_bug_diagnosis_executes_with_required_inputs() -> None:
    executions, audit, _ = _reset_test_env()
    use_case = RunScenarioUseCase(get_start_execution_use_case(), executions, get_scenario_catalog(), audit, get_usage_meter(), get_billing_read_model())
    result = use_case.execute(
        project_id="proj-2",
        scenario_id="bug_diagnosis",
        objective="identificar causa raiz",
        inputs={
            "observed_error": "Traceback: ValueError invalid id",
            "stack": "python-fastapi",
            "objective": "corrigir bug de validação",
            "source_text": "def validate(user_id):\n    int(user_id)",
        },
    )

    run_execution_job({}, result.execution_id)
    updated = executions.get(result.execution_id)
    assert updated is not None
    assert updated.status in {"completed", "bounded_completion"}

    tool_events = [e for e in audit.list_by_execution(result.execution_id) if e.event_type == "tool_envelope"]
    assert tool_events


def test_patch_review_requires_diff_and_generates_high_urgency() -> None:
    executions, audit, _ = _reset_test_env()
    use_case = RunScenarioUseCase(get_start_execution_use_case(), executions, get_scenario_catalog(), audit, get_usage_meter(), get_billing_read_model())
    result = use_case.execute(
        project_id="proj-3",
        scenario_id="patch_review",
        objective="revisar patch crítico",
        inputs={
            "diff_text": "--- a/app.py\n+++ b/app.py\n@@\n-print('x')\n+print('y')",
            "objective": "validar segurança e risco",
            "stack": "python",
            "observed_error": "ERROR: unexpected state",
        },
    )

    run_execution_job({}, result.execution_id)
    reports = [e for e in audit.list_by_execution(result.execution_id) if e.event_type == "engineering_report"]
    assert reports
    payload = json.loads(reports[-1].message)
    _assert_engineering_report(payload)
    assert payload["urgency"] in {"high", "immediate"}


def test_legacy_alias_is_accepted_with_deprecation_event() -> None:
    executions, audit, _ = _reset_test_env()
    use_case = RunScenarioUseCase(get_start_execution_use_case(), executions, get_scenario_catalog(), audit, get_usage_meter(), get_billing_read_model())
    result = use_case.execute(
        project_id="proj-4",
        scenario_id="kaiso_whatsapp_incident",
        objective="legacy compatibility",
        inputs={
            "stack": "python",
            "objective": "avaliar base",
            "files": [{"path": "src/main.py", "content": "print('legacy')"}],
        },
    )

    assert result.scenario_id == "code_analysis"
    assert result.deprecated_alias_used is True
    events = audit.list_by_execution(result.execution_id)
    assert any(e.event_type == "scenario_alias_deprecated" for e in events)


def test_bug_diagnosis_repo_enrichment_is_opt_in_and_audited(tmp_path: Path) -> None:
    executions, audit, _ = _reset_test_env()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "src").mkdir()
    (repo / "src" / "errors.py").write_text("raise ValueError('invalid id')\n", encoding="utf-8")
    use_case = RunScenarioUseCase(
        get_start_execution_use_case(),
        executions,
        get_scenario_catalog(),
        audit,
        get_usage_meter(),
        get_billing_read_model(),
        GitLocalSourceConnector,
    )
    result = use_case.execute(
        project_id="proj-5",
        scenario_id="bug_diagnosis",
        objective="diagnosticar erro",
        inputs={
            "observed_error": "ValueError invalid id",
            "stack": "python",
            "objective": "corrigir bug",
            "source_text": "def run(): pass",
            "repo_path": str(repo),
            "repo_enrichment": {"enabled": True},
        },
    )

    events = audit.list_by_execution(result.execution_id)
    enrichment_events = [e for e in events if e.event_type == "scenario_repo_enrichment"]
    assert enrichment_events
    payload = json.loads(enrichment_events[-1].message)
    assert payload["attempted"] is True
    assert payload["applied"] is True
    assert payload["selected_files"] >= 1
