from collections.abc import Callable


class ToolRouter:
    def __init__(self) -> None:
        self._registry: dict[str, Callable[[str], str]] = {}

    def register(self, capability: str, handler: Callable[[str], str]) -> None:
        self._registry[capability] = handler

    def call(self, capability: str, payload: str) -> str:
        if capability not in self._registry:
            raise KeyError(f"capability '{capability}' not registered")
        return self._registry[capability](payload)
