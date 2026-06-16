from fastapi import APIRouter, Depends

from app.api.dependencies import require_api_key
from app.core.registry import default_registry

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("")
def list_tenants(_: None = Depends(require_api_key)) -> dict:
    return {
        "tenants": default_registry.list_tenants()
    }


@router.get("/{tenant_id}/plugins")
def get_tenant_plugins(tenant_id: str, _: None = Depends(require_api_key)) -> dict:
    return default_registry.tenant_view(tenant_id).model_dump(mode="json")


@router.post("/reload")
def reload_tenant_config(_: None = Depends(require_api_key)) -> dict:
    default_registry.reload_tenant_config()
    return {
        "status": "reloaded",
        "tenants": default_registry.list_tenants()
    }
