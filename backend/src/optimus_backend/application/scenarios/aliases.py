LEGACY_SCENARIO_ALIASES: dict[str, str] = {
    "kaiso_whatsapp_incident": "code_analysis",
    "kaiso_kds_pos_sync": "bug_diagnosis",
}


def resolve_scenario_id(scenario_id: str) -> tuple[str, bool]:
    resolved = LEGACY_SCENARIO_ALIASES.get(scenario_id, scenario_id)
    return resolved, resolved != scenario_id
