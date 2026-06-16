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

from __future__ import annotations

from typing import Any

from app.audit.factory import get_audit_repository
from app.core.models import Phase, Verdict


def init_db(_: str | None = None) -> None:
    get_audit_repository().init_db()


def save_evaluation(
    _: str | None,
    tenant_id: str,
    session_id: str | None,
    user_id: str | None,
    phase: Phase,
    request_payload: dict[str, Any],
    verdict: Verdict,
    active_plugins: list[str] | None = None,
    tenant_config: dict[str, Any] | None = None,
) -> str:
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


def get_evaluation(_: str | None, evaluation_id: str) -> dict[str, Any] | None:
    return get_audit_repository().get_evaluation(evaluation_id)
