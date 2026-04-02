import pytest

from optimus_backend.application.scenarios.aliases import resolve_scenario_id
from optimus_backend.core.scenarios.catalog import ScenarioCatalog


def _files() -> list[dict[str, str]]:
    return [{"path": "src/app.py", "content": "print('ok')"}]


def test_catalog_requires_mandatory_inputs() -> None:
    catalog = ScenarioCatalog()
    with pytest.raises(ValueError):
        catalog.validate_inputs("code_analysis", {"stack": "python"})


def test_catalog_exposes_partial_terminal_states() -> None:
    catalog = ScenarioCatalog()
    scenario = catalog.get("refactor_suggestion")
    assert "partial_success" in scenario.supported_terminal_states
    assert "external_dependency_unavailable" in scenario.supported_terminal_states
    assert "manual_validation_required" in scenario.supported_terminal_states


def test_legacy_aliases_resolve_outside_core() -> None:
    resolved, deprecated = resolve_scenario_id("kaiso_whatsapp_incident")
    assert deprecated is True
    assert resolved == "code_analysis"


def test_catalog_includes_engineering_scenarios() -> None:
    catalog = ScenarioCatalog()
    assert catalog.get("code_analysis").scenario_id == "code_analysis"
    assert catalog.get("bug_diagnosis").scenario_id == "bug_diagnosis"
    assert catalog.get("refactor_suggestion").scenario_id == "refactor_suggestion"
    assert catalog.get("patch_review").scenario_id == "patch_review"


def test_patch_review_requires_diff_text() -> None:
    catalog = ScenarioCatalog()
    with pytest.raises(ValueError):
        catalog.validate_inputs(
            "patch_review",
            {"objective": "review", "stack": "python", "diff_text": ""},
        )


def test_catalog_validates_files_object_shape() -> None:
    catalog = ScenarioCatalog()
    with pytest.raises(ValueError):
        catalog.validate_inputs(
            "code_analysis",
            {"stack": "python", "objective": "analyze", "files": [{"path": "a.py"}]},
        )

    catalog.validate_inputs(
        "code_analysis",
        {"stack": "python", "objective": "analyze", "files": _files()},
    )
