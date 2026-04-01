import os
from pydantic import BaseModel


class AppConfig(BaseModel):
    app_name: str = os.getenv("APP_NAME", "optimus")
    app_version: str = "0.2.1"
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "postgresql://optimus:optimus@localhost:5432/optimus")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    auth_session_ttl_seconds: int = int(os.getenv("AUTH_SESSION_TTL_SECONDS", "3600"))
    lock_ttl_seconds: int = int(os.getenv("EXECUTION_LOCK_TTL_SECONDS", "300"))


config = AppConfig()
