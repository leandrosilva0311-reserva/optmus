import logging
import time
from collections import defaultdict
from threading import Lock

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from optimus_backend.api.dependencies import get_auth_use_case, get_logout_use_case
from optimus_backend.application.use_cases.authenticate import AuthenticateUserUseCase, LogoutUseCase
from optimus_backend.schemas.auth import LoginRequest, LoginResponse, LogoutResponse
from optimus_backend.settings.config import config

router = APIRouter(prefix="/auth", tags=["auth"])
LOGGER = logging.getLogger("optimus.auth.route")

# In-process login rate limiter — keyed by client IP
_login_attempts: dict[str, list[float]] = defaultdict(list)
_login_lock = Lock()


def _check_login_rate_limit(client_ip: str) -> None:
    now = time.monotonic()
    window = 60.0
    with _login_lock:
        attempts = [t for t in _login_attempts[client_ip] if now - t < window]
        attempts.append(now)
        _login_attempts[client_ip] = attempts
        if len(attempts) > config.rate_limit_login_per_minute:
            raise HTTPException(status_code=429, detail="too many login attempts")


@router.post("/login", response_model=LoginResponse)
def login(
    request: Request,
    payload: LoginRequest,
    auth: AuthenticateUserUseCase = Depends(get_auth_use_case),
) -> LoginResponse:
    cf_ip = request.headers.get("CF-Connecting-IP", "")
    forwarded = request.headers.get("X-Forwarded-For", "")
    client_ip = cf_ip or (forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown"))

    _check_login_rate_limit(client_ip)
    LOGGER.info("auth.login.attempt ip=%s", client_ip)
    try:
        result = auth.execute(payload.email, payload.password, ttl_seconds=config.auth_session_ttl_seconds)
    except PermissionError:
        LOGGER.warning("auth.login.failed ip=%s", client_ip)
        raise HTTPException(status_code=401, detail="invalid credentials") from None
    except Exception as exc:
        LOGGER.exception("auth.login.error ip=%s", client_ip)
        raise HTTPException(status_code=503, detail="authentication unavailable") from exc
    LOGGER.info("auth.login.success ip=%s role=%s", client_ip, result.role)
    return LoginResponse(session_id=result.session_id, role=result.role)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    logout_use_case: LogoutUseCase = Depends(get_logout_use_case),
    session_id: str = Header(default="", alias="X-Session-Id"),
) -> LogoutResponse:
    if not session_id:
        raise HTTPException(status_code=401, detail="missing session")
    logout_use_case.execute(session_id)
    return LogoutResponse(status="ok")
