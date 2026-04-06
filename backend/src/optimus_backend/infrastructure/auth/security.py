import hashlib
import hmac
import secrets
from base64 import urlsafe_b64encode

try:
    import bcrypt as _bcrypt
    _BCRYPT_AVAILABLE = True
except Exception:  # pragma: no cover
    _bcrypt = None  # type: ignore[assignment]
    _BCRYPT_AVAILABLE = False


def hash_password(password: str) -> str:
    if _BCRYPT_AVAILABLE:
        return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt(rounds=12)).decode("utf-8")
    # fallback: sha256 — only used if bcrypt is not installed
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    if _BCRYPT_AVAILABLE and password_hash.startswith("$2"):
        return _bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    # fallback for legacy sha256 hashes
    return hmac.compare_digest(
        hashlib.sha256(password.encode("utf-8")).hexdigest(),
        password_hash,
    )


def generate_session_id() -> str:
    raw = secrets.token_bytes(32)
    return urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
