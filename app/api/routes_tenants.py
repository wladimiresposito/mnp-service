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
