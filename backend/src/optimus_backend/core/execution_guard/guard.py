from dataclasses import dataclass


@dataclass(slots=True)
class GuardConfig:
    max_iterations: int = 5


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
