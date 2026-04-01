from optimus_backend.application.use_cases.authenticate import AuthenticateUserUseCase
from optimus_backend.domain.entities import UserRecord
from optimus_backend.infrastructure.auth.security import hash_password
from optimus_backend.infrastructure.persistence.in_memory import InMemorySessionRepository, InMemoryUserRepository


def test_authenticate_success() -> None:
    users = InMemoryUserRepository([
        UserRecord(id="u1", email="admin@optimus.local", password_hash=hash_password("admin12345"), role="admin")
    ])
    sessions = InMemorySessionRepository()

    use_case = AuthenticateUserUseCase(users=users, sessions=sessions)
    result = use_case.execute("admin@optimus.local", "admin12345")

    assert result.role == "admin"
    assert sessions.get_user_id(result.session_id) == "u1"


def test_authenticate_invalid_password() -> None:
    users = InMemoryUserRepository([
        UserRecord(id="u1", email="admin@optimus.local", password_hash=hash_password("admin12345"), role="admin")
    ])
    sessions = InMemorySessionRepository()
    use_case = AuthenticateUserUseCase(users=users, sessions=sessions)

    try:
        use_case.execute("admin@optimus.local", "wrong-pass")
    except PermissionError as exc:
        assert "invalid credentials" in str(exc)
    else:
        raise AssertionError("PermissionError expected")
