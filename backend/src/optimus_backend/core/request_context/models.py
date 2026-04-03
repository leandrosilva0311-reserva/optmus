from dataclasses import dataclass


@dataclass(slots=True)
class RequestContext:
    execution_id: str
    tenant_id: str
    api_key_id: str
    plan: str
    agent_id: str
