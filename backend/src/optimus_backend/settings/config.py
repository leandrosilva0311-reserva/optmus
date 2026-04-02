import os
from pydantic import BaseModel


def _csv_env(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


class AppConfig(BaseModel):
    app_name: str = os.getenv("APP_NAME", "optimus")
    app_version: str = "0.4.0"
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "postgresql://optimus:optimus@localhost:5432/optimus")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    auth_session_ttl_seconds: int = int(os.getenv("AUTH_SESSION_TTL_SECONDS", "3600"))
    lock_ttl_seconds: int = int(os.getenv("EXECUTION_LOCK_TTL_SECONDS", "300"))
    project_root: str = os.getenv("PROJECT_ROOT", "/workspace/optmus")
    idempotency_window_minutes: int = int(os.getenv("IDEMPOTENCY_WINDOW_MINUTES", "30"))
    rate_limit_tool_per_minute: int = int(os.getenv("RATE_LIMIT_TOOL_PER_MINUTE", "20"))
    rate_limit_project_per_minute: int = int(os.getenv("RATE_LIMIT_PROJECT_PER_MINUTE", "80"))
    secret_key: str = os.getenv("SECRET_KEY", "optimus-dev-secret")
    local_connector_allowed_extensions: list[str] = _csv_env(
        "LOCAL_CONNECTOR_ALLOWED_EXTENSIONS",
        ".py,.ts,.tsx,.js,.jsx,.json,.yaml,.yml,.md,.toml,.ini,.cfg,.sql,.sh,.txt",
    )
    local_connector_ignored_dirs: list[str] = _csv_env(
        "LOCAL_CONNECTOR_IGNORED_DIRS",
        ".git,.venv,venv,node_modules,.idea,.vscode,dist,build,__pycache__,.mypy_cache,.pytest_cache",
    )
    local_connector_max_file_bytes: int = int(os.getenv("LOCAL_CONNECTOR_MAX_FILE_BYTES", "150000"))
    local_connector_search_max_results: int = int(os.getenv("LOCAL_CONNECTOR_SEARCH_MAX_RESULTS", "300"))
    repo_enrichment_max_files: int = int(os.getenv("REPO_ENRICHMENT_MAX_FILES", "40"))
    repo_enrichment_max_total_bytes: int = int(os.getenv("REPO_ENRICHMENT_MAX_TOTAL_BYTES", "1500000"))


config = AppConfig()
