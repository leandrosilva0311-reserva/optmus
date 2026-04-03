import secrets


def generate_api_key() -> tuple[str, str]:
    prefix = f"opk_{secrets.token_hex(4)}"
    secret = secrets.token_urlsafe(32)
    return prefix, f"{prefix}.{secret}"
