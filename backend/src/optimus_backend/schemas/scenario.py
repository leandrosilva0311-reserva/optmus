from datetime import datetime

from pydantic import BaseModel


class ScenarioRunRequest(BaseModel):
    project_id: str
    scenario_id: str
    objective: str


class ScenarioRunResponse(BaseModel):
    execution_id: str
    status: str
    reused: bool


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
