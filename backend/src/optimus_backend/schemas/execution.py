from datetime import datetime

from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    project_id: str = Field(default="default")
    objective: str = Field(min_length=3)
    agent: str = Field(default="dev_architect")


class QueueTaskResponse(BaseModel):
    execution_id: str
    status: str


class ExecutionView(BaseModel):
    id: str
    project_id: str
    objective: str
    agent: str
    status: str
    summary: str | None
    error: str | None
    duration_ms: int | None
    created_at: datetime


class SubtaskView(BaseModel):
    id: str
    execution_id: str
    agent: str
    title: str
    depends_on: list[str]
    status: str
    result_summary: str | None
    handoff_reason: str | None
    attempt: int
    created_at: datetime


class AuditEventView(BaseModel):
    id: str
    execution_id: str
    event_type: str
    message: str
    created_at: datetime
