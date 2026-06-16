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
