from typing import Protocol


class LLMProvider(Protocol):
    async def complete(self, prompt: str) -> str:
        ...


class MockProvider:
    async def complete(self, prompt: str) -> str:
        return f"mock-response:{prompt[:80]}"
