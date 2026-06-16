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

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import require_api_key
from app.audit.factory import get_audit_repository
from app.core.middleware import NormativeMiddleware
from app.core.models import (
    EvaluateAllRequest,
    EvaluateContextRequest,
    EvaluatePlanRequest,
    EvaluateToolCallRequest,
    EvaluateOutputRequest,
    EvaluateResponse,
    Phase,
)
from app.core.registry import PluginResolutionError, default_registry

router = APIRouter(prefix="/evaluate", tags=["evaluate"])


def _resolve(tenant_id: str, plugin_ids: list[str] | None):
    try:
        return default_registry.resolve_for_tenant(tenant_id, plugin_ids)
    except PluginResolutionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _middleware(tenant_id: str, plugin_ids: list[str] | None):
    plugins, cfg, active_ids = _resolve(tenant_id, plugin_ids)
    return NormativeMiddleware(plugins=plugins, composition=cfg.composition), cfg, active_ids


def _save(*, tenant_id, session_id, user_id, phase, request_payload, verdict, active_plugins, tenant_config):
    return get_audit_repository().save_evaluation(
        tenant_id=tenant_id,
        session_id=session_id,
        user_id=user_id,
        phase=phase,
        request_payload=request_payload,
        verdict=verdict,
        active_plugins=active_plugins,
        tenant_config=tenant_config,
    )


@router.post("/input", response_model=EvaluateResponse)
def evaluate_input(payload: EvaluateContextRequest, _: None = Depends(require_api_key)) -> EvaluateResponse:
    tenant_id = payload.context.tenant_id
    mnp, cfg, active_ids = _middleware(tenant_id, payload.plugins)
    verdict = mnp.evaluate_input(payload.context)
    evaluation_id = _save(
        tenant_id=tenant_id,
        session_id=payload.context.session_id,
        user_id=payload.context.user_id,
        phase=Phase.INPUT,
        request_payload=payload.model_dump(mode="json"),
        verdict=verdict,
        active_plugins=active_ids,
        tenant_config=cfg.model_dump(mode="json"),
    )
    return EvaluateResponse(
        evaluation_id=evaluation_id,
        verdict=verdict,
        tenant_id=cfg.tenant_id,
        active_plugins=active_ids,
        composition=cfg.composition,
    )


@router.post("/plan", response_model=EvaluateResponse)
def evaluate_plan(payload: EvaluatePlanRequest, _: None = Depends(require_api_key)) -> EvaluateResponse:
    mnp, cfg, active_ids = _middleware(payload.tenant_id, payload.plugins)
    verdict = mnp.evaluate_plan(payload.plan)
    evaluation_id = _save(
        tenant_id=payload.tenant_id,
        session_id=payload.session_id,
        user_id=payload.user_id,
        phase=Phase.PLAN,
        request_payload=payload.model_dump(mode="json"),
        verdict=verdict,
        active_plugins=active_ids,
        tenant_config=cfg.model_dump(mode="json"),
    )
    return EvaluateResponse(
        evaluation_id=evaluation_id,
        verdict=verdict,
        tenant_id=cfg.tenant_id,
        active_plugins=active_ids,
        composition=cfg.composition,
    )


@router.post("/tool-call", response_model=EvaluateResponse)
def evaluate_tool_call(payload: EvaluateToolCallRequest, _: None = Depends(require_api_key)) -> EvaluateResponse:
    mnp, cfg, active_ids = _middleware(payload.tenant_id, payload.plugins)
    verdict = mnp.evaluate_tool_call(payload.tool_call)
    evaluation_id = _save(
        tenant_id=payload.tenant_id,
        session_id=payload.session_id,
        user_id=payload.user_id,
        phase=Phase.TOOL_CALL,
        request_payload=payload.model_dump(mode="json"),
        verdict=verdict,
        active_plugins=active_ids,
        tenant_config=cfg.model_dump(mode="json"),
    )
    return EvaluateResponse(
        evaluation_id=evaluation_id,
        verdict=verdict,
        tenant_id=cfg.tenant_id,
        active_plugins=active_ids,
        composition=cfg.composition,
    )


@router.post("/output", response_model=EvaluateResponse)
def evaluate_output(payload: EvaluateOutputRequest, _: None = Depends(require_api_key)) -> EvaluateResponse:
    mnp, cfg, active_ids = _middleware(payload.tenant_id, payload.plugins)
    verdict = mnp.evaluate_output(payload.draft)
    evaluation_id = _save(
        tenant_id=payload.tenant_id,
        session_id=payload.session_id,
        user_id=payload.user_id,
        phase=Phase.OUTPUT,
        request_payload=payload.model_dump(mode="json"),
        verdict=verdict,
        active_plugins=active_ids,
        tenant_config=cfg.model_dump(mode="json"),
    )
    return EvaluateResponse(
        evaluation_id=evaluation_id,
        verdict=verdict,
        tenant_id=cfg.tenant_id,
        active_plugins=active_ids,
        composition=cfg.composition,
    )


@router.post("/all", response_model=EvaluateResponse)
def evaluate_all(payload: EvaluateAllRequest, _: None = Depends(require_api_key)) -> EvaluateResponse:
    tenant_id = payload.context.tenant_id if payload.context else payload.tenant_id
    mnp, cfg, active_ids = _middleware(tenant_id, payload.plugins)

    verdict = mnp.evaluate_all(
        context=payload.context,
        plan=payload.plan,
        tool_call=payload.tool_call,
        draft=payload.draft,
    )

    session_id = payload.context.session_id if payload.context else payload.session_id
    user_id = payload.context.user_id if payload.context else payload.user_id

    evaluation_id = _save(
        tenant_id=tenant_id,
        session_id=session_id,
        user_id=user_id,
        phase=Phase.ALL,
        request_payload=payload.model_dump(mode="json"),
        verdict=verdict,
        active_plugins=active_ids,
        tenant_config=cfg.model_dump(mode="json"),
    )
    return EvaluateResponse(
        evaluation_id=evaluation_id,
        verdict=verdict,
        tenant_id=cfg.tenant_id,
        active_plugins=active_ids,
        composition=cfg.composition,
    )
