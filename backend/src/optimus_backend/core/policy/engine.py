from dataclasses import dataclass


@dataclass(slots=True)
class PolicyDecision:
    allowed: bool
    reason: str


class PolicyEngine:
    def authorize_action(self, action: str, requires_approval: bool) -> PolicyDecision:
        if requires_approval:
            return PolicyDecision(False, f"action '{action}' requires approval")
        return PolicyDecision(True, "allowed")
