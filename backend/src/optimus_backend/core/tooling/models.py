from dataclasses import dataclass


@dataclass(slots=True)
class ToolExecutionRequest:
    execution_id: str
    tool_name: str
    payload: dict


@dataclass(slots=True)
class ToolExecutionEnvelope:
    status: str
    duration_ms: int
    truncated: bool
    output: str | None
    error: str | None
    sanitized_input: dict
