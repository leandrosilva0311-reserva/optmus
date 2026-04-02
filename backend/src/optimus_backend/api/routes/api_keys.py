from fastapi import APIRouter, Depends, HTTPException, Query

from optimus_backend.api.dependencies import get_api_key_use_case, get_current_user
from optimus_backend.schemas.api_keys import ApiKeyCreateRequest, ApiKeyCreateResponse, ApiKeyView

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


def ensure_admin_user(user: dict[str, str]) -> None:
    if user.get("auth_type") == "api_key":
        raise HTTPException(status_code=403, detail="api keys cannot manage api keys")
    if user.get("role") not in {"admin", "operator"}:
        raise HTTPException(status_code=403, detail="insufficient role")


@router.post("", response_model=ApiKeyCreateResponse)
def create_api_key(payload: ApiKeyCreateRequest, user: dict[str, str] = Depends(get_current_user)) -> ApiKeyCreateResponse:
    ensure_admin_user(user)
    use_case = get_api_key_use_case()
    result = use_case.create_key(payload.project_id, payload.name, payload.scopes, workspace_id=payload.workspace_id)
    return ApiKeyCreateResponse(
        key=result.plaintext_key,
        item=ApiKeyView(
            id=result.record.id,
            project_id=result.record.project_id,
            workspace_id=result.record.workspace_id,
            name=result.record.name,
            key_prefix=result.record.key_prefix,
            status=result.record.status,
            scopes=result.record.scopes,
            created_at=result.record.created_at,
            last_used_at=result.record.last_used_at,
            revoked_at=result.record.revoked_at,
        ),
    )


@router.get("", response_model=list[ApiKeyView])
def list_api_keys(project_id: str = Query(...), user: dict[str, str] = Depends(get_current_user)) -> list[ApiKeyView]:
    ensure_admin_user(user)
    records = get_api_key_use_case().list_keys(project_id)
    return [
        ApiKeyView(
            id=record.id,
            project_id=record.project_id,
            workspace_id=record.workspace_id,
            name=record.name,
            key_prefix=record.key_prefix,
            status=record.status,
            scopes=record.scopes,
            created_at=record.created_at,
            last_used_at=record.last_used_at,
            revoked_at=record.revoked_at,
        )
        for record in records
    ]


@router.post("/{key_id}/revoke", response_model=ApiKeyView)
def revoke_api_key(key_id: str, user: dict[str, str] = Depends(get_current_user)) -> ApiKeyView:
    ensure_admin_user(user)
    try:
        record = get_api_key_use_case().revoke_key(key_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ApiKeyView(
        id=record.id,
        project_id=record.project_id,
        workspace_id=record.workspace_id,
        name=record.name,
        key_prefix=record.key_prefix,
        status=record.status,
        scopes=record.scopes,
        created_at=record.created_at,
        last_used_at=record.last_used_at,
        revoked_at=record.revoked_at,
    )


@router.post("/{key_id}/rotate", response_model=ApiKeyCreateResponse)
def rotate_api_key(key_id: str, user: dict[str, str] = Depends(get_current_user)) -> ApiKeyCreateResponse:
    ensure_admin_user(user)
    try:
        result = get_api_key_use_case().rotate_key(key_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ApiKeyCreateResponse(
        key=result.plaintext_key,
        item=ApiKeyView(
            id=result.record.id,
            project_id=result.record.project_id,
            workspace_id=result.record.workspace_id,
            name=result.record.name,
            key_prefix=result.record.key_prefix,
            status=result.record.status,
            scopes=result.record.scopes,
            created_at=result.record.created_at,
            last_used_at=result.record.last_used_at,
            revoked_at=result.record.revoked_at,
        ),
    )
