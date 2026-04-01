from dataclasses import dataclass

from optimus_backend.core.provider.base import LLMProvider
from optimus_backend.domain.enums import Severity


@dataclass(slots=True)
class SpecialistResult:
    agent: str
    diagnosis: str
    evidence: list[str]
    recommendations: list[str]
    risk_level: Severity
    urgency: Severity
    execution_plan: list[str]


class BaseSpecialist:
    name = "base"
    role_prompt = ""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def run(self, objective: str) -> SpecialistResult:
        content = self.provider.complete(f"[{self.name}] {self.role_prompt} | objective={objective}")
        return SpecialistResult(
            agent=self.name,
            diagnosis=content[:140],
            evidence=[f"provider_signal:{content[:80]}"],
            recommendations=[f"Execute focused action for {self.name}"],
            risk_level=Severity.medium,
            urgency=Severity.medium,
            execution_plan=[f"Assess objective: {objective}", "Apply recommendation", "Validate outcome"],
        )


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

    def run(self, objective: str) -> SpecialistResult:
        base = super().run(objective)
        plan = [
            "Prioritize critical blockers",
            "Assign owner and timeline",
            "Execute and verify resolution",
        ]
        return SpecialistResult(
            agent=base.agent,
            diagnosis=base.diagnosis,
            evidence=base.evidence,
            recommendations=base.recommendations,
            risk_level=Severity.high,
            urgency=Severity.high,
            execution_plan=plan,
        )
