from dataclasses import dataclass


PLAN_LIMITS_PER_DAY: dict[str, int] = {
    "starter": 50,
    "growth": 250,
    "enterprise": 2000,
}


@dataclass(frozen=True, slots=True)
class UsageSnapshot:
    plan_id: str
    daily_limit: int
    consumed_today: int
    remaining_today: int
    warning_level: str


def limit_for_plan(plan_id: str) -> int:
    return PLAN_LIMITS_PER_DAY.get(plan_id, PLAN_LIMITS_PER_DAY["starter"])


def warning_for_ratio(consumed: int, limit: int) -> str:
    if limit <= 0:
        return "blocked"
    ratio = consumed / limit
    if ratio >= 0.95:
        return "95"
    if ratio >= 0.80:
        return "80"
    return "none"
