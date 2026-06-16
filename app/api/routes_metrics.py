from fastapi import APIRouter, Depends, Query

from app.api.dependencies import require_api_key
from app.audit.factory import get_audit_repository

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/summary")
def metrics_summary(
    tenant_id: str | None = None,
    _: None = Depends(require_api_key),
) -> dict:
    return get_audit_repository().metrics_summary(tenant_id=tenant_id)


@router.get("/rules")
def metrics_rules(
    tenant_id: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
    _: None = Depends(require_api_key),
) -> dict:
    return get_audit_repository().metrics_rules(tenant_id=tenant_id, limit=limit)


@router.get("/plugins")
def metrics_plugins(
    tenant_id: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
    _: None = Depends(require_api_key),
) -> dict:
    return get_audit_repository().metrics_plugins(tenant_id=tenant_id, limit=limit)
