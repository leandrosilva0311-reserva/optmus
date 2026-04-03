from enum import Enum


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
