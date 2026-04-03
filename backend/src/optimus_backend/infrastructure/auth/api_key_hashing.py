import base64
import hashlib
import hmac
import secrets

try:
    from argon2.exceptions import VerifyMismatchError
    from argon2.low_level import Type, hash_secret, verify_secret
except Exception:  # pragma: no cover - optional dependency
    VerifyMismatchError = Exception
    Type = None
    hash_secret = None
    verify_secret = None


PBKDF2_ITERATIONS = 210_000
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65_536
ARGON2_PARALLELISM = 2
ARGON2_HASH_LEN = 32


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _unb64(value: str) -> bytes:
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("utf-8"))


def hash_api_key(secret: str, pepper: str = "") -> str:
    raw = f"{pepper}{secret}".encode("utf-8")
    if hash_secret and Type:
        salt = secrets.token_bytes(16)
        digest = hash_secret(
            secret=raw,
            salt=salt,
            time_cost=ARGON2_TIME_COST,
            memory_cost=ARGON2_MEMORY_COST,
            parallelism=ARGON2_PARALLELISM,
            hash_len=ARGON2_HASH_LEN,
            type=Type.ID,
        )
        return f"argon2id${digest.decode('utf-8')}"

    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", raw, salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${_b64(salt)}${_b64(digest)}"


def verify_api_key(secret: str, stored_hash: str, pepper: str = "") -> bool:
    raw = f"{pepper}{secret}".encode("utf-8")
    if stored_hash.startswith("argon2id$") and verify_secret:
        payload = stored_hash.split("$", 1)[1]
        try:
            return bool(verify_secret(payload.encode("utf-8"), raw, Type.ID))
        except VerifyMismatchError:
            return False
        except Exception:
            return False

    if not stored_hash.startswith("pbkdf2_sha256$"):
        return False
    try:
        _, iterations_raw, salt_raw, digest_raw = stored_hash.split("$", 3)
        iterations = int(iterations_raw)
        salt = _unb64(salt_raw)
        expected = _unb64(digest_raw)
    except Exception:
        return False

    computed = hashlib.pbkdf2_hmac("sha256", raw, salt, iterations)
    return hmac.compare_digest(expected, computed)
