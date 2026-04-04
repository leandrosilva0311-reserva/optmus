import logging

from fastapi import APIRouter, Depends, Header, HTTPException

from optimus_backend.api.dependencies import get_auth_use_case, get_logout_use_case
from optimus_backend.application.use_cases.authenticate import AuthenticateUserUseCase, LogoutUseCase
from optimus_backend.schemas.auth import LoginRequest, LoginResponse, LogoutResponse
from optimus_backend.settings.config import config

router = APIRouter(prefix="/auth", tags=["auth"])
LOGGER = logging.getLogger("optimus.auth.route")


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, auth: AuthenticateUserUseCase = Depends(get_auth_use_case)) -> LoginResponse:
    try:
        result = auth.execute(payload.email, payload.password, ttl_seconds=config.auth_session_ttl_seconds)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="authentication unavailable") from exc
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
