from datetime import datetime

from pydantic import BaseModel


class ScenarioRunRequest(BaseModel):
    project_id: str
    scenario_id: str
    objective: str
    inputs: dict[str, str]


class ScenarioRunResponse(BaseModel):
    execution_id: str
    status: str
    reused: bool


class ScenarioDefinitionOfDoneResponse(BaseModel):
    success_criteria: list[str]
    failure_criteria: list[str]


class ScenarioFinalBusinessBlockResponse(BaseModel):
    operational_impact: str
    commercial_impact: str
    severity: str
    immediate_action: str
    suggested_owner: str


class ScenarioDetailResponse(BaseModel):
    execution_id: str
    project_id: str
    scenario_id: str
    status: str
    summary: str | None
    max_steps: int
    max_tool_calls: int
    max_duration_ms: int
    created_at: datetime
    required_inputs: list[str]
    definition_of_done: ScenarioDefinitionOfDoneResponse
    supported_terminal_states: list[str]
    final_business_block: ScenarioFinalBusinessBlockResponse | None
