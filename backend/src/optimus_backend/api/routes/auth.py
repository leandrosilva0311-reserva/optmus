from fastapi import APIRouter, Depends, HTTPException

from optimus_backend.api.dependencies import get_auth_use_case
from optimus_backend.application.use_cases.authenticate import AuthenticateUserUseCase
from optimus_backend.schemas.auth import LoginRequest, LoginResponse
from optimus_backend.settings.config import config

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, auth: AuthenticateUserUseCase = Depends(get_auth_use_case)) -> LoginResponse:
    try:
        result = auth.execute(payload.email, payload.password, ttl_seconds=config.auth_session_ttl_seconds)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return LoginResponse(session_id=result.session_id, role=result.role)
