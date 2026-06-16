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

from typing import Any, Literal
from pydantic import BaseModel, Field


class ECEvent(BaseModel):
    t: int
    kind: Literal[
        "grant_consent",
        "revoke_consent",
        "change_purpose",
        "start_processing",
        "stop_processing",
        "data_breach",
        "human_review_approved",
        "human_review_rejected",
    ]
    subject: str
    purpose: str = "process_health_data_for_pre_anamnesis"
    data_category: str | None = None
    actor: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ECScenario(BaseModel):
    subject: str
    purpose: str = "process_health_data_for_pre_anamnesis"
    current_time: int = 100
    data_category: Literal["health", "personal", "sensitive", "general"] = "health"
    processing_action: str = "process_health_data"
    events: list[ECEvent] = Field(default_factory=list)

    # Domain flags
    requires_legal_basis: bool = True
    requires_purpose_confirmation: bool = True
    emergency_exception: bool = False
    human_review_override: bool = False


class ECFluentState(BaseModel):
    fluent: str
    holds: bool
    initiated_by: ECEvent | None = None
    terminated_by: ECEvent | None = None
    clipped_by: list[ECEvent] = Field(default_factory=list)


class ECObligation(BaseModel):
    obligation_id: str
    description: str
    due_time: int | None = None
    triggered_by: str
    satisfied: bool = False


class ECConsequence(BaseModel):
    consequence_id: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    description: str
    triggered_by: str


class ECDecision(BaseModel):
    allowed: bool
    forbidden: bool
    requires_escalation: bool = False
    risk_level: Literal["low", "medium", "high", "critical"] = "low"
    violated_rules: list[str] = Field(default_factory=list)
    required_changes: list[str] = Field(default_factory=list)
    obligations: list[ECObligation] = Field(default_factory=list)
    consequences: list[ECConsequence] = Field(default_factory=list)


class ECResult(BaseModel):
    engine: str
    clingo_available: bool
    scenario: ECScenario
    fluents: list[ECFluentState] = Field(default_factory=list)
    decision: ECDecision
    answer_set: list[str] = Field(default_factory=list)
    trace: dict[str, Any] = Field(default_factory=dict)
