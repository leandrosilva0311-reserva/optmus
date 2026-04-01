from dataclasses import dataclass


@dataclass(slots=True)
class BudgetState:
    steps_used: int
    tool_calls_used: int
    duration_ms: int


class BudgetEnforcer:
    PRIORITY = ["max_duration_ms", "max_tool_calls", "max_steps"]

    def check(self, state: BudgetState, max_steps: int, max_tool_calls: int, max_duration_ms: int) -> tuple[bool, str | None]:
        exceeded = []
        if state.duration_ms > max_duration_ms:
            exceeded.append("max_duration_ms")
        if state.tool_calls_used > max_tool_calls:
            exceeded.append("max_tool_calls")
        if state.steps_used > max_steps:
            exceeded.append("max_steps")

        if not exceeded:
            return True, None

        for key in self.PRIORITY:
            if key in exceeded:
                return False, key
        return False, exceeded[0]
