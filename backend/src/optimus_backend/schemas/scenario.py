from datetime import datetime

from pydantic import BaseModel


class ScenarioRunRequest(BaseModel):
    project_id: str
    scenario_id: str
    objective: str
    inputs: dict[str, str]
    plan_id: str = "starter"


class UsageSnapshotResponse(BaseModel):
    plan_id: str
    daily_limit: int
    consumed_today: int
    remaining_today: int
    warning_level: str


class ScenarioRunResponse(BaseModel):
    execution_id: str
    status: str
    reused: bool
    usage: UsageSnapshotResponse


class ScenarioDefinitionOfDoneResponse(BaseModel):
    success_criteria: list[str]
    failure_criteria: list[str]


class ScenarioCatalogItemResponse(BaseModel):
    scenario_id: str
    name: str
    required_inputs: list[str]
    definition_of_done: ScenarioDefinitionOfDoneResponse
    supported_terminal_states: list[str]
    business_value: str
    recommended_for: list[str]
    estimated_runtime_minutes: int
    onboarding_steps: list[str]


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
