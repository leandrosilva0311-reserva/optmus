import pytest

from optimus_backend.core.scenarios.catalog import ScenarioCatalog


def test_catalog_requires_mandatory_inputs() -> None:
    catalog = ScenarioCatalog()
    with pytest.raises(ValueError):
        catalog.validate_inputs("public_api_health", {"request_id": "r1"})


def test_catalog_exposes_partial_terminal_states() -> None:
    catalog = ScenarioCatalog()
    scenario = catalog.get("checkout_flow_validation")
    assert "partial_success" in scenario.supported_terminal_states
    assert "external_dependency_unavailable" in scenario.supported_terminal_states
    assert "manual_validation_required" in scenario.supported_terminal_states


def test_catalog_supports_legacy_aliases_for_compatibility() -> None:
    catalog = ScenarioCatalog()
    legacy = catalog.get("kaiso_whatsapp_incident")
    assert legacy.scenario_id == "public_api_health"


def test_catalog_includes_queue_health() -> None:
    catalog = ScenarioCatalog()
    scenario = catalog.get("queue_health")
    assert scenario.scenario_id == "queue_health"


def test_catalog_includes_incident_timeline_reconstruction() -> None:
    catalog = ScenarioCatalog()
    scenario = catalog.get("incident_timeline_reconstruction")
    assert scenario.scenario_id == "incident_timeline_reconstruction"


def test_catalog_exposes_commercial_metadata() -> None:
    catalog = ScenarioCatalog()
    scenario = catalog.get("public_api_health")
    assert scenario.business_value
    assert scenario.recommended_for
    assert scenario.estimated_runtime_minutes > 0
    assert scenario.onboarding_steps
