import hashlib
import hmac
import secrets
from base64 import urlsafe_b64encode


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password), password_hash)


def generate_session_id() -> str:
    raw = secrets.token_bytes(32)
    return urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
