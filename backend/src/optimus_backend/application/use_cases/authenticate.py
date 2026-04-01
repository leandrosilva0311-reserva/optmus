from dataclasses import dataclass

from optimus_backend.domain.ports import SessionRepository, UserRepository
from optimus_backend.infrastructure.auth.security import generate_session_id, verify_password


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
        user = self._users.find_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise PermissionError("invalid credentials")

        session_id = generate_session_id()
        self._sessions.save(session_id=session_id, user_id=user.id, ttl_seconds=ttl_seconds)
        return AuthResult(session_id=session_id, user_id=user.id, role=user.role)


class LogoutUseCase:
    def __init__(self, sessions: SessionRepository) -> None:
        self._sessions = sessions

    def execute(self, session_id: str) -> None:
        self._sessions.delete(session_id)
