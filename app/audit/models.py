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

from dataclasses import dataclass
from typing import Any


@dataclass
class AuditFilters:
    tenant_id: str | None = None
    session_id: str | None = None
    user_id: str | None = None
    decision: str | None = None
    risk_level: str | None = None
    plugin_id: str | None = None
    rule_id: str | None = None
    limit: int = 50
    offset: int = 0


@dataclass
class EvaluationRecord:
    id: str
    tenant_id: str
    session_id: str | None
    user_id: str | None
    phase: str
    final_decision: str
    risk_level: str
    request_json: dict[str, Any]
    verdict_json: dict[str, Any]
    active_plugins_json: list[str]
    tenant_config_json: dict[str, Any]
    created_at: str
