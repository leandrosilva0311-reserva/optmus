from dataclasses import dataclass
from optimus_backend.core.provider.base import LLMProvider


@dataclass(slots=True)
class SpecialistResult:
    agent: str
    output: str


class BaseSpecialist:
    name = "base"

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def run(self, objective: str) -> SpecialistResult:
        output = self.provider.complete(f"[{self.name}] {objective}")
        return SpecialistResult(agent=self.name, output=output)


class DevAgent(BaseSpecialist):
    name = "dev"


class QAAgent(BaseSpecialist):
    name = "qa"


class OpsAgent(BaseSpecialist):
    name = "ops"


class AnalystAgent(BaseSpecialist):
    name = "analyst"
