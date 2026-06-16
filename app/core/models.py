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

from enum import Enum
from typing import Any
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class Decision(str, Enum):
    ALLOW = "allow"
    MODIFY = "modify"
    BLOCK = "block"
    ESCALATE = "escalate"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Phase(str, Enum):
    INPUT = "input"
    PLAN = "plan"
    TOOL_CALL = "tool_call"
    OUTPUT = "output"
    ALL = "all"


class CompositionPolicy(str, Enum):
    CONSERVATIVE = "conservative"
    HIERARCHICAL = "hierarchical"


class PluginMetadata(BaseModel):
    plugin_id: str
    plugin_version: str
    jurisdiction: str | None = None
    domain: str | None = None
    source: str | None = None
    updated_at: str | None = None
    # binding=True: norma vinculante (lei, regulacao, codigo profissional).
    # binding=False: plugin suplementar (politica interna opinativa, teoria
    # etica). Suplementar nunca derruba sozinho uma permissao vinculante.
    binding: bool = True


class TenantPluginConfig(BaseModel):
    tenant_id: str
    composition: CompositionPolicy = CompositionPolicy.CONSERVATIVE
    enabled_plugins: list[str] = Field(default_factory=list)
    disabled_plugins: list[str] = Field(default_factory=list)
    plugin_settings: dict[str, dict[str, Any]] = Field(default_factory=dict)


class TenantPluginView(BaseModel):
    tenant_id: str
    composition: CompositionPolicy
    enabled_plugins: list[PluginMetadata]
    disabled_plugins: list[str]
    unknown_plugins: list[str] = Field(default_factory=list)
    plugin_settings: dict[str, dict[str, Any]] = Field(default_factory=dict)


class Verdict(BaseModel):
    decision: Decision = Decision.ALLOW
    risk_level: RiskLevel = RiskLevel.LOW
    violated_rules: list[str] = Field(default_factory=list)
    required_changes: list[str] = Field(default_factory=list)
    explanation: str = ""
    trace: list[dict[str, Any]] = Field(default_factory=list)
    plugin_id: str = "core"
    plugin_version: str = "1.0.0"
    # Carimbado pelo middleware a partir do metadata do plugin, para que a
    # composicao saiba distinguir norma vinculante de plugin suplementar.
    binding: bool = True

    @classmethod
    def allow(cls, plugin_id: str, plugin_version: str, explanation: str = "Permitido.") -> "Verdict":
        return cls(
            decision=Decision.ALLOW,
            risk_level=RiskLevel.LOW,
            explanation=explanation,
            plugin_id=plugin_id,
            plugin_version=plugin_version,
        )


class Context(BaseModel):
    tenant_id: str = "default"
    session_id: str | None = None
    user_id: str | None = None
    user_text: str
    facts: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ActionPlan(BaseModel):
    goal: str
    actions: list[dict[str, Any]] = Field(default_factory=list)
    facts: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0


class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    facts: dict[str, Any] = Field(default_factory=dict)
    requires_side_effect: bool = False


class DraftAnswer(BaseModel):
    text: str
    facts: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0


class EvaluateContextRequest(BaseModel):
    context: Context
    plugins: list[str] | None = None


class EvaluatePlanRequest(BaseModel):
    tenant_id: str = "default"
    session_id: str | None = None
    user_id: str | None = None
    plan: ActionPlan
    plugins: list[str] | None = None


class EvaluateToolCallRequest(BaseModel):
    tenant_id: str = "default"
    session_id: str | None = None
    user_id: str | None = None
    tool_call: ToolCall
    plugins: list[str] | None = None


class EvaluateOutputRequest(BaseModel):
    tenant_id: str = "default"
    session_id: str | None = None
    user_id: str | None = None
    draft: DraftAnswer
    plugins: list[str] | None = None


class EvaluateAllRequest(BaseModel):
    tenant_id: str = "default"
    session_id: str | None = None
    user_id: str | None = None
    context: Context | None = None
    plan: ActionPlan | None = None
    tool_call: ToolCall | None = None
    draft: DraftAnswer | None = None
    plugins: list[str] | None = None


class EvaluateResponse(BaseModel):
    evaluation_id: str
    verdict: Verdict
    tenant_id: str
    active_plugins: list[str] = Field(default_factory=list)
    composition: CompositionPolicy = CompositionPolicy.CONSERVATIVE
