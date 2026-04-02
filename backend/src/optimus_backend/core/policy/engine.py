from dataclasses import dataclass


@dataclass(slots=True)
class PolicyDecision:
    allowed: bool
    reason: str


class PolicyEngine:
    def __init__(self, allowed_tools: set[str] | None = None) -> None:
        self._allowed_tools = allowed_tools or {"filesystem", "terminal", "http", "log_correlation", "queue_inspection", "code_search", "diff_analysis", "log_analysis", "config_inspection"}

    def authorize_action(self, action: str, requires_approval: bool) -> PolicyDecision:
        if requires_approval:
            return PolicyDecision(False, f"action '{action}' requires approval")
        return PolicyDecision(True, "allowed")

    def can_execute(self, tool_name: str) -> bool:
        return tool_name in self._allowed_tools
