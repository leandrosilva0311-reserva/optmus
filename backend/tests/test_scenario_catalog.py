import pytest

from optimus_backend.core.scenarios.catalog import ScenarioCatalog


def test_catalog_requires_mandatory_inputs() -> None:
    catalog = ScenarioCatalog()
    with pytest.raises(ValueError):
        catalog.validate_inputs("kaiso_whatsapp_incident", {"request_id": "r1"})


def test_catalog_exposes_partial_terminal_states() -> None:
    catalog = ScenarioCatalog()
    scenario = catalog.get("kaiso_kds_pos_sync")
    assert "partial_success" in scenario.supported_terminal_states
    assert "external_dependency_unavailable" in scenario.supported_terminal_states
    assert "manual_validation_required" in scenario.supported_terminal_states
