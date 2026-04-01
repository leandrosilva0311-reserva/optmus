import hashlib


SECRET_KEYS = {"password", "token", "secret", "api_key", "authorization"}


def sanitize_payload(payload: dict, hard_limit: int = 120) -> tuple[dict, bool, str]:
    truncated = False
    sanitized: dict[str, str] = {}

    for key, value in payload.items():
        key_lower = key.lower()
        if key_lower in SECRET_KEYS:
            sanitized[key] = "[REDACTED]"
            continue

        text = str(value)
        if len(text) > hard_limit:
            text = text[:hard_limit] + "..."
            truncated = True
        sanitized[key] = text

    payload_hash = hashlib.sha256(str(sorted(payload.items())).encode("utf-8")).hexdigest()
    return sanitized, truncated, payload_hash
