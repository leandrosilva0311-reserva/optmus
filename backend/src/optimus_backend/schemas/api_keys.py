from datetime import datetime

from pydantic import BaseModel, Field


class ApiKeyCreateRequest(BaseModel):
    project_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=120)
    scopes: list[str] = Field(min_length=1)
    workspace_id: str | None = None


class ApiKeyRotateRequest(BaseModel):
    key_id: str


class ApiKeyView(BaseModel):
    id: str
    project_id: str
    workspace_id: str | None
    name: str
    key_prefix: str
    status: str
    scopes: list[str]
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None


class ApiKeyCreateResponse(BaseModel):
    key: str
    item: ApiKeyView
