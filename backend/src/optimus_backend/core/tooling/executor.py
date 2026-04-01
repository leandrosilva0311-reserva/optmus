from datetime import UTC, datetime

from optimus_backend.core.tooling.models import ToolExecutionEnvelope, ToolExecutionRequest
from optimus_backend.core.tooling.protocols import ToolAdapter, ToolGuard, ToolPolicy


class ToolExecutor:
    def __init__(self, tools: dict[str, ToolAdapter], policy: ToolPolicy, guard: ToolGuard) -> None:
        self._tools = tools
        self._policy = policy
        self._guard = guard

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionEnvelope:
        started = datetime.now(UTC)
        sanitized_input = self._sanitize_payload(request.payload)

        if not self._policy.can_execute(request.tool_name):
            duration = int((datetime.now(UTC) - started).total_seconds() * 1000)
            return ToolExecutionEnvelope("denied", duration, False, None, "tool not allowed by policy", sanitized_input)

        self._guard.pre_check(request.tool_name, request.payload)

        adapter = self._tools.get(request.tool_name)
        if not adapter:
            duration = int((datetime.now(UTC) - started).total_seconds() * 1000)
            return ToolExecutionEnvelope("error", duration, False, None, "tool not registered", sanitized_input)

        try:
            output, truncated = adapter.run(request.payload)
            safe_output = self._guard.post_check(request.tool_name, output)
            duration = int((datetime.now(UTC) - started).total_seconds() * 1000)
            return ToolExecutionEnvelope("ok", duration, truncated, safe_output, None, sanitized_input)
        except Exception as exc:
            duration = int((datetime.now(UTC) - started).total_seconds() * 1000)
            return ToolExecutionEnvelope("error", duration, False, None, str(exc), sanitized_input)

    @staticmethod
    def _sanitize_payload(payload: dict) -> dict:
        sanitized: dict = {}
        for key, value in payload.items():
            text = str(value)
            sanitized[key] = text[:120] + "..." if len(text) > 120 else text
        return sanitized
