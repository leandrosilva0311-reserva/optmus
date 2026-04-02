from typing import Protocol


class ToolAdapter(Protocol):
    name: str

    def run(self, payload: dict) -> tuple[str, bool]:
        """Returns (output, truncated)."""


class ToolPolicy(Protocol):
    def can_execute(self, tool_name: str) -> bool:
        ...


class ToolGuard(Protocol):
    def pre_check(self, tool_name: str, payload: dict) -> None:
        ...

    def post_check(self, tool_name: str, output: str) -> str:
        ...
