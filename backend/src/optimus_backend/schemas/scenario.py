from datetime import datetime

from pydantic import BaseModel


class ScenarioFileInput(BaseModel):
    path: str
    content: str


class ScenarioRunRequest(BaseModel):
    project_id: str
    scenario_id: str
    objective: str
    inputs: dict[str, object]
    plan_id: str | None = None


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
    request_id: str | None = None
    scenario_id: str | None = None
    deprecated_alias_used: bool = False


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


class EngineeringExecutionStepResponse(BaseModel):
    step_id: str
    title: str
    description: str
    expected_outcome: str


class EngineeringScenarioOutputResponse(BaseModel):
    diagnosis: str
    evidence: list[str]
    recommendations: list[str]
    risk_level: str
    urgency: str
    execution_plan: list[EngineeringExecutionStepResponse]


class ScenarioFinalBusinessBlockResponse(BaseModel):
    operational_impact: str | None = None
    commercial_impact: str | None = None
    severity: str | None = None
    immediate_action: str | None = None
    suggested_owner: str | None = None


class ScenarioEngineeringReportResponse(BaseModel):
    execution_id: str
    scenario_id: str
    diagnosis: str
    evidence: list[str]
    recommendations: list[str]
    risk_level: str
    urgency: str
    execution_plan: list[EngineeringExecutionStepResponse]
    generated_at: datetime


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
