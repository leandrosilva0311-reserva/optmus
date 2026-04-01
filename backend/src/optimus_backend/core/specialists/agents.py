from dataclasses import dataclass

from optimus_backend.core.provider.base import LLMProvider


@dataclass(slots=True)
class SpecialistResult:
    agent: str
    output: str


class BaseSpecialist:
    name = "base"
    role_prompt = ""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def run(self, objective: str) -> SpecialistResult:
        prompt = f"[{self.name}] {self.role_prompt} | objective={objective}"
        output = self.provider.complete(prompt)
        return SpecialistResult(agent=self.name, output=output)


class DevArchitectAgent(BaseSpecialist):
    name = "dev_architect"
    role_prompt = "Focus on architecture, coupling, and refactoring plan"


class BugHunterAgent(BaseSpecialist):
    name = "bug_hunter"
    role_prompt = "Focus on likely root causes, logs, and patch suggestion"


class QAAgent(BaseSpecialist):
    name = "qa"
    role_prompt = "Focus on smoke tests, regression risks, and validation report"


class OpsSentinelAgent(BaseSpecialist):
    name = "ops_sentinel"
    role_prompt = "Focus on health checks, config risks, and runtime diagnosis"


class AnalystAgent(BaseSpecialist):
    name = "analyst"
    role_prompt = "Produce executive and technical summary with bottlenecks"
