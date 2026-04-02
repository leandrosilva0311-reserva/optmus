import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def ensure_access(principal: dict[str, str], allowed_roles: set[str], required_scopes: set[str], route_path: str) -> None:
    auth_type = principal.get("auth_type") or ("user" if principal.get("role") else "unknown")
    if auth_type == "user":
        allowed = principal.get("role", "") in allowed_roles
        logger.info(
            "auth_scope_check",
            extra={
                "execution_id": "authz",
                "agent_id": principal.get("user_id", "unknown"),
                "event_type": "auth_scope_check",
                "auth_type": auth_type,
                "route_path": route_path,
                "scope_check_result": "allowed" if allowed else "forbidden",
            },
        )
        if not allowed:
            raise HTTPException(status_code=403, detail="insufficient role")
        return

    if auth_type == "api_key":
        scopes = set(principal.get("scopes", "").split(",")) if principal.get("scopes") else set()
        missing = required_scopes - scopes
        allowed = not missing
        logger.info(
            "auth_scope_check",
            extra={
                "execution_id": "authz",
                "agent_id": principal.get("api_key_id", "unknown"),
                "event_type": "auth_scope_check",
                "auth_type": auth_type,
                "route_path": route_path,
                "scope_check_result": "allowed" if allowed else f"missing:{','.join(sorted(missing))}",
            },
        )
        if missing:
            raise HTTPException(status_code=403, detail=f"missing scopes: {', '.join(sorted(missing))}")
        return

    raise HTTPException(status_code=401, detail="unauthenticated")
