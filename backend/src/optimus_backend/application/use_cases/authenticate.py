from dataclasses import dataclass
import logging

from optimus_backend.domain.ports import SessionRepository, UserRepository
from optimus_backend.infrastructure.auth.security import generate_session_id, verify_password

LOGGER = logging.getLogger("optimus.auth")


@dataclass(slots=True)
class AuthResult:
    session_id: str
    user_id: str
    role: str


class AuthenticateUserUseCase:
    def __init__(self, users: UserRepository, sessions: SessionRepository) -> None:
        self._users = users
        self._sessions = sessions

    def execute(self, email: str, password: str, ttl_seconds: int = 3600) -> AuthResult:
        LOGGER.info("auth.execute.start")
        user = self._users.find_by_email(email)
        LOGGER.info("auth.execute.user_lookup found=%s", user is not None)
        if user is None:
            raise PermissionError("invalid credentials")
        password_match = verify_password(password, user.password_hash)
        if not password_match:
            raise PermissionError("invalid credentials")

        session_id = generate_session_id()
        LOGGER.info("auth.execute.session_save.start user_id=%s", user.id)
        try:
            self._sessions.save(session_id=session_id, user_id=user.id, ttl_seconds=ttl_seconds)
        except Exception:
            LOGGER.exception("auth.execute.session_save.error user_id=%s", user.id)
            raise
        LOGGER.info("auth.execute.session_save.success user_id=%s", user.id)
        return AuthResult(session_id=session_id, user_id=user.id, role=user.role)


class LogoutUseCase:
    def __init__(self, sessions: SessionRepository) -> None:
        self._sessions = sessions

    def execute(self, session_id: str) -> None:
        self._sessions.delete(session_id)
