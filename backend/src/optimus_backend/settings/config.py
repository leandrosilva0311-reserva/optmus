import os
from pydantic import BaseModel


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
    rate_limit_tenant_per_minute: int = int(os.getenv("RATE_LIMIT_TENANT_PER_MINUTE", "120"))
    default_tenant_api_key: str = os.getenv("DEFAULT_TENANT_API_KEY", "optmus-dev-key")


config = AppConfig()
