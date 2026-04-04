from optimus_backend.api.dependencies import get_auth_use_case, get_dev_seed_user_repository, get_repositories
from optimus_backend.settings.config import config


def test_get_auth_use_case_uses_seed_user_when_enabled() -> None:
    original_env = config.app_env
    original_seed_flag = config.enable_dev_seed_user
    get_repositories.cache_clear()
    config.app_env = "test"
    config.enable_dev_seed_user = True

    try:
        auth = get_auth_use_case()
        result = auth.execute(config.dev_seed_user_email, config.dev_seed_user_password)
        assert result.role == config.dev_seed_user_role
    finally:
        config.app_env = original_env
        config.enable_dev_seed_user = original_seed_flag
        get_repositories.cache_clear()


def test_get_auth_use_case_without_seed_user_rejects_seed_credentials_in_test_env() -> None:
    original_env = config.app_env
    original_seed_flag = config.enable_dev_seed_user
    get_repositories.cache_clear()
    config.app_env = "test"
    config.enable_dev_seed_user = False

    try:
        auth = get_auth_use_case()
        try:
            auth.execute(config.dev_seed_user_email, config.dev_seed_user_password)
        except PermissionError as exc:
            assert str(exc) == "invalid credentials"
        else:
            raise AssertionError("PermissionError expected")
    finally:
        config.app_env = original_env
        config.enable_dev_seed_user = original_seed_flag
        get_repositories.cache_clear()


def test_get_dev_seed_user_repository_respects_flag() -> None:
    original_seed_flag = config.enable_dev_seed_user
    config.enable_dev_seed_user = False
    assert get_dev_seed_user_repository() is None
    config.enable_dev_seed_user = True
    assert get_dev_seed_user_repository() is not None
    config.enable_dev_seed_user = original_seed_flag
