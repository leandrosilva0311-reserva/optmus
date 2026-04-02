from optimus_backend.application.use_cases.api_keys import ApiKeyUseCase
from optimus_backend.infrastructure.persistence.in_memory import InMemoryApiKeyRepository


def test_create_authenticate_revoke_rotate_api_key() -> None:
    repo = InMemoryApiKeyRepository()
    use_case = ApiKeyUseCase(repo, pepper="test-pepper")

    created = use_case.create_key("p-1", "integration", ["scenarios:run", "billing:read"])
    assert created.record.key_hash != created.plaintext_key
    assert created.record.key_prefix in created.plaintext_key

    authenticated = use_case.authenticate(created.plaintext_key)
    assert authenticated is not None
    assert authenticated.id == created.record.id
    assert repo.get(created.record.id).last_used_at is not None

    revoked = use_case.revoke_key(created.record.id)
    assert revoked.status == "revoked"
    assert use_case.authenticate(created.plaintext_key) is None

    rotated = use_case.rotate_key(revoked.id)
    assert rotated.record.id != revoked.id
    assert rotated.record.project_id == revoked.project_id
    assert use_case.authenticate(rotated.plaintext_key) is not None
