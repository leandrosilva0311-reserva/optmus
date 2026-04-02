from datetime import UTC, datetime

from optimus_backend.domain.entities import PlanDefinitionRecord, SubscriptionRecord


class InMemoryBillingReadModel:
    def __init__(self) -> None:
        self._plans = [
            PlanDefinitionRecord("starter", "Starter", 50, 4900, 100, True),
            PlanDefinitionRecord("growth", "Growth", 250, 19900, 80, True),
            PlanDefinitionRecord("enterprise", "Enterprise", 2000, 99900, 50, True),
        ]
        self._subscriptions: dict[str, SubscriptionRecord] = {
            "default": SubscriptionRecord(
                id="sub-default",
                project_id="default",
                plan_id="starter",
                status="active",
                started_at=datetime.now(UTC),
                renews_at=None,
                cancelled_at=None,
            )
        }

    def list_active_plans(self) -> list[PlanDefinitionRecord]:
        return [plan for plan in self._plans if plan.active]

    def get_active_subscription(self, project_id: str) -> SubscriptionRecord | None:
        sub = self._subscriptions.get(project_id)
        if sub and sub.status == "active":
            return sub
        return None
