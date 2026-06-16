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

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import require_api_key
from app.audit.factory import get_audit_repository
from app.audit.models import AuditFilters

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def list_audit(
    tenant_id: str | None = None,
    session_id: str | None = None,
    user_id: str | None = None,
    decision: str | None = None,
    risk_level: str | None = None,
    plugin_id: str | None = None,
    rule_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: None = Depends(require_api_key),
) -> dict:
    return get_audit_repository().list_evaluations(
        AuditFilters(
            tenant_id=tenant_id,
            session_id=session_id,
            user_id=user_id,
            decision=decision,
            risk_level=risk_level,
            plugin_id=plugin_id,
            rule_id=rule_id,
            limit=limit,
            offset=offset,
        )
    )


@router.get("/by-session/{session_id}")
def read_audit_by_session(
    session_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: None = Depends(require_api_key),
) -> dict:
    return get_audit_repository().list_evaluations(
        AuditFilters(session_id=session_id, limit=limit, offset=offset)
    )


@router.get("/by-tenant/{tenant_id}")
def read_audit_by_tenant(
    tenant_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: None = Depends(require_api_key),
) -> dict:
    return get_audit_repository().list_evaluations(
        AuditFilters(tenant_id=tenant_id, limit=limit, offset=offset)
    )


@router.get("/{evaluation_id}")
def read_audit(evaluation_id: str, _: None = Depends(require_api_key)) -> dict:
    record = get_audit_repository().get_evaluation(evaluation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Evaluation not found.")
    return record
