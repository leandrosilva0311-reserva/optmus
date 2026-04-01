from datetime import UTC, datetime

from optimus_backend.core.tooling.models import ToolExecutionEnvelope, ToolExecutionRequest
from optimus_backend.core.tooling.protocols import ToolAdapter, ToolGuard, ToolPolicy
from optimus_backend.core.tooling.sanitizer import sanitize_payload
from optimus_backend.domain.ports import RateLimiter


class ToolExecutor:
    def __init__(
        self,
        tools: dict[str, ToolAdapter],
        policy: ToolPolicy,
        guard: ToolGuard,
        rate_limiter: RateLimiter,
        project_limit: int,
        tool_limit: int,
    ) -> None:
        self._tools = tools
        self._policy = policy
        self._guard = guard
        self._rate_limiter = rate_limiter
        self._project_limit = project_limit
        self._tool_limit = tool_limit

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionEnvelope:
        started = datetime.now(UTC)
        sanitized_input, truncated, payload_hash = sanitize_payload(request.payload)

        if not self._policy.can_execute(request.tool_name):
            duration = int((datetime.now(UTC) - started).total_seconds() * 1000)
            return ToolExecutionEnvelope("blocked", duration, truncated, None, None, "policy_denied", payload_hash, sanitized_input)

        self._guard.pre_check(request.tool_name, request.payload)

        if not self._rate_limiter.allow(
            project_id=request.project_id,
            tool_name=request.tool_name,
            project_limit=self._project_limit,
            tool_limit=self._tool_limit,
        ):
            duration = int((datetime.now(UTC) - started).total_seconds() * 1000)
            return ToolExecutionEnvelope("blocked", duration, truncated, None, None, "rate_limited", payload_hash, sanitized_input)

        adapter = self._tools.get(request.tool_name)
        if not adapter:
            duration = int((datetime.now(UTC) - started).total_seconds() * 1000)
            return ToolExecutionEnvelope("error", duration, truncated, None, "tool not registered", "tool_not_found", payload_hash, sanitized_input)

        try:
            output, tool_truncated = adapter.run(request.payload)
            safe_output = self._guard.post_check(request.tool_name, output)
            duration = int((datetime.now(UTC) - started).total_seconds() * 1000)
            return ToolExecutionEnvelope("ok", duration, truncated or tool_truncated, safe_output, None, None, payload_hash, sanitized_input)
        except Exception as exc:
            duration = int((datetime.now(UTC) - started).total_seconds() * 1000)
            return ToolExecutionEnvelope("error", duration, truncated, None, str(exc), "tool_exception", payload_hash, sanitized_input)
