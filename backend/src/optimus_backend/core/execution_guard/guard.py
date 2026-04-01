from dataclasses import dataclass


@dataclass(slots=True)
class GuardConfig:
    max_iterations: int = 5
    max_output_chars: int = 2000


class ExecutionGuard:
    def __init__(self, config: GuardConfig | None = None) -> None:
        self._config = config or GuardConfig()

    def assert_iteration(self, iteration: int) -> None:
        if iteration > self._config.max_iterations:
            raise RuntimeError("max iterations exceeded")

    def assert_non_destructive(self, action: str) -> None:
        blocked = ("delete", "drop", "destroy")
        if any(keyword in action.lower() for keyword in blocked):
            raise PermissionError("destructive action blocked")

    def pre_check(self, tool_name: str, payload: dict) -> None:
        if tool_name == "terminal" and payload.get("shell"):
            raise PermissionError("shell mode is not allowed")

    def post_check(self, tool_name: str, output: str) -> str:
        _ = tool_name
        if len(output) > self._config.max_output_chars:
            return output[: self._config.max_output_chars]
        return output
