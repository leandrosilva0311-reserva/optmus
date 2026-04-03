from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from optimus_backend.core.auth_scopes import validate_scopes
from optimus_backend.domain.entities import ApiKeyRecord
from optimus_backend.domain.ports import ApiKeyRepository
from optimus_backend.infrastructure.auth.api_key_hashing import hash_api_key, verify_api_key
from optimus_backend.infrastructure.auth.api_key_security import generate_api_key


@dataclass(slots=True)
class ApiKeyCreationResult:
    record: ApiKeyRecord
    plaintext_key: str


class ApiKeyUseCase:
    def __init__(self, repository: ApiKeyRepository, pepper: str = "") -> None:
        self._repository = repository
        self._pepper = pepper

    def create_key(self, project_id: str, name: str, scopes: list[str], workspace_id: str | None = None) -> ApiKeyCreationResult:
        valid_scopes = validate_scopes(scopes)
        prefix, plaintext = generate_api_key()
        now = datetime.now(UTC)
        record = ApiKeyRecord(
            id=str(uuid4()),
            project_id=project_id,
            workspace_id=workspace_id,
            name=name,
            key_prefix=prefix,
            key_hash=hash_api_key(plaintext, pepper=self._pepper),
            status="active",
            scopes=valid_scopes,
            created_at=now,
            last_used_at=None,
            revoked_at=None,
        )
        self._repository.create(record)
        return ApiKeyCreationResult(record=record, plaintext_key=plaintext)

    def list_keys(self, project_id: str) -> list[ApiKeyRecord]:
        return list(self._repository.list_by_project(project_id))

    def revoke_key(self, key_id: str) -> ApiKeyRecord:
        record = self._repository.revoke(key_id, datetime.now(UTC))
        if record is None:
            raise KeyError("api key not found")
        return record

    def rotate_key(self, key_id: str) -> ApiKeyCreationResult:
        current = self._repository.get(key_id)
        if current is None:
            raise KeyError("api key not found")
        self.revoke_key(key_id)
        return self.create_key(current.project_id, current.name, current.scopes, workspace_id=current.workspace_id)

    def authenticate(self, plaintext_key: str) -> ApiKeyRecord | None:
        prefix = plaintext_key.split(".", 1)[0] if "." in plaintext_key else ""
        if not prefix:
            return None
        record = self._repository.find_active_by_prefix(prefix)
        if record is None:
            return None
        if record.status != "active" or record.revoked_at is not None:
            return None
        if not verify_api_key(plaintext_key, record.key_hash, pepper=self._pepper):
            return None
        self._repository.touch_last_used(record.id, datetime.now(UTC))
        return record
