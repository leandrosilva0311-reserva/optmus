from dataclasses import dataclass


@dataclass(slots=True)
class ToolExecutionRequest:
    execution_id: str
    project_id: str
    tool_name: str
    payload: dict


@dataclass(slots=True)
class ToolExecutionEnvelope:
    status: str
    duration_ms: int
    truncated: bool
    output: str | None
    error: str | None
    blocked_reason: str | None
    payload_hash: str | None
    sanitized_input: dict
