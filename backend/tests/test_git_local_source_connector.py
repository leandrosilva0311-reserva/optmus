from pathlib import Path

import pytest

from optimus_backend.application.use_cases.run_scenario import RunScenarioUseCase
from optimus_backend.core.scenarios.catalog import ScenarioCatalog
from optimus_backend.infrastructure.source_connectors.git_local_connector import GitLocalSourceConnector
from optimus_backend.settings.config import config


class _StartExecutionStub:
    class _Execution:
        id = "exec-1"
        status = "queued"

    def execute(self, **_: object) -> "_StartExecutionStub._Execution":
        return self._Execution()


class _ExecutionsStub:
    def list_recent(self, _: int) -> list[object]:
        return []


class _AuditStub:
    def __init__(self) -> None:
        self.events: list[object] = []

    def append(self, event: object) -> None:
        self.events.append(event)


class _UsageStub:
    def consume(self, **_: object) -> tuple[bool, int, int]:
        return True, 1, 100


class _Subscription:
    plan_id = "starter"


class _BillingStub:
    def get_active_subscription(self, _: str) -> _Subscription | None:
        return None


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "src").mkdir()
    (repo / "src" / "a.py").write_text("def alpha():\n    return 'ok'\n", encoding="utf-8")
    (repo / "src" / "b.py").write_text("def beta():\n    return 'find-me'\n", encoding="utf-8")
    return repo


def _make_nested_repo(tmp_path: Path) -> Path:
    repo = _make_repo(tmp_path)
    (repo / "node_modules").mkdir()
    (repo / "node_modules" / "ignored.js").write_text("console.log('ignore')", encoding="utf-8")
    (repo / "services").mkdir()
    (repo / "services" / "api").mkdir(parents=True, exist_ok=True)
    (repo / "services" / "api" / "handler.ts").write_text("export const handler = () => 'ok'", encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs" / "architecture.md").write_text("find-me in docs", encoding="utf-8")
    return repo


def test_git_local_connector_fetch_list_and_search(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    connector = GitLocalSourceConnector(str(repo))

    listed = connector.list_files("**/*.py")
    assert listed == ["src/a.py", "src/b.py"]
    assert "alpha" in connector.fetch_file("src/a.py")
    matches = connector.search("find-me")
    assert len(matches) == 1
    assert matches[0]["path"] == "src/b.py"
    assert matches[0]["line_number"] == 2
    assert "find-me" in str(matches[0]["snippet"])


def test_git_local_connector_blocks_path_traversal(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    connector = GitLocalSourceConnector(str(repo))

    with pytest.raises(ValueError, match="path traversal"):
        connector.fetch_file("../etc/passwd")


def test_git_local_connector_ignores_sensitive_directories(tmp_path: Path) -> None:
    repo = _make_nested_repo(tmp_path)
    connector = GitLocalSourceConnector(str(repo))
    files = connector.list_files("**/*")

    assert "node_modules/ignored.js" not in files
    assert "services/api/handler.ts" in files


def test_git_local_connector_rejects_invalid_pattern(tmp_path: Path) -> None:
    repo = _make_nested_repo(tmp_path)
    connector = GitLocalSourceConnector(str(repo))

    with pytest.raises(ValueError, match="invalid file pattern"):
        connector.list_files("**/[")


def test_git_local_connector_blocks_large_file_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _make_nested_repo(tmp_path)
    huge = repo / "src" / "huge.py"
    huge.write_text("x" * 200_000, encoding="utf-8")
    monkeypatch.setattr(config, "local_connector_max_file_bytes", 1000)
    connector = GitLocalSourceConnector(str(repo))

    with pytest.raises(ValueError, match="exceeds max allowed size"):
        connector.fetch_file("src/huge.py")


def test_refactor_suggestion_can_enrich_files_from_local_repo_when_opted_in(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    audit = _AuditStub()
    use_case = RunScenarioUseCase(
        _StartExecutionStub(),
        _ExecutionsStub(),
        ScenarioCatalog(),
        audit,
        _UsageStub(),
        _BillingStub(),
        GitLocalSourceConnector,
    )

    result = use_case.execute(
        project_id="proj-local",
        scenario_id="refactor_suggestion",
        objective="analisar",
        inputs={
            "stack": "python",
            "objective": "analisar",
            "additional_instructions": "modularizar",
            "repo_path": str(repo),
            "file_pattern": "**/*.py",
            "repo_enrichment": {"enabled": True},
        },
    )

    assert result.execution_id == "exec-1"
    assert audit.events
    assert "src/a.py" in audit.events[-1].message
    assert "src/b.py" in audit.events[-1].message


def test_repo_enrichment_respects_file_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _make_repo(tmp_path)
    monkeypatch.setattr(config, "repo_enrichment_max_files", 1)
    use_case = RunScenarioUseCase(
        _StartExecutionStub(),
        _ExecutionsStub(),
        ScenarioCatalog(),
        _AuditStub(),
        _UsageStub(),
        _BillingStub(),
        GitLocalSourceConnector,
    )

    with pytest.raises(ValueError, match="max files"):
        use_case.execute(
            project_id="proj-local",
            scenario_id="refactor_suggestion",
            objective="analisar",
            inputs={
                "stack": "python",
                "objective": "analisar",
                "additional_instructions": "modularizar",
                "repo_path": str(repo),
                "file_pattern": "**/*.py",
                "repo_enrichment": {"enabled": True},
            },
        )
