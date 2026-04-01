from typing import Protocol


class LLMProvider(Protocol):
    def complete(self, prompt: str) -> str:
        ...


class MockProvider:
    def complete(self, prompt: str) -> str:
        return f"mock-response:{prompt[:80]}"
