from fastapi import APIRouter, Depends

from app.api.dependencies import require_api_key
from app.audit.factory import get_audit_repository
from app.core.registry import default_registry
from app.core.version import version_info

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/version")
def system_version(_: None = Depends(require_api_key)) -> dict:
    return version_info()


@router.get("/live")
def live() -> dict:
    return {
        "status": "live",
        **version_info(),
    }


@router.get("/ready")
def ready(_: None = Depends(require_api_key)) -> dict:
    checks = {
        "audit_repository": "ok",
        "tenant_registry": "ok",
        "plugins_registered": len(default_registry.all_plugins()),
        "tenants_configured": len(default_registry.list_tenants()),
    }

    try:
        get_audit_repository().metrics_summary()
    except Exception as exc:
        checks["audit_repository"] = f"error: {type(exc).__name__}"

    status = "ready" if all(not str(v).startswith("error") for v in checks.values()) else "degraded"
    return {
        "status": status,
        "checks": checks,
        **version_info(),
    }
