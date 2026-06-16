# Copyright 2026 Wladimir Esposito (OmniAI / Omni Tech Consulting)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
