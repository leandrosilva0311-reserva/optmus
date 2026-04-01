from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScenarioInputField:
    name: str
    description: str


@dataclass(frozen=True, slots=True)
class ScenarioDefinitionOfDone:
    success_criteria: tuple[str, ...]
    failure_criteria: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ScenarioFinalBusinessBlock:
    operational_impact: str
    commercial_impact: str
    severity: str
    immediate_action: str
    suggested_owner: str


@dataclass(frozen=True, slots=True)
class ScenarioDefinition:
    scenario_id: str
    name: str
    required_inputs: tuple[ScenarioInputField, ...]
    done: ScenarioDefinitionOfDone
    supported_terminal_states: tuple[str, ...]
