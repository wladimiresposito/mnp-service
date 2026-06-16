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
from pydantic import BaseModel, Field, ConfigDict


class NormativeFacts(BaseModel):
    """
    Canonical JSON Schema for v0.5 fact extraction.

    The extractor should not decide allow/modify/block/escalate. It only extracts
    facts that the MNP plugins can evaluate.
    """

    model_config = ConfigDict(extra="allow")

    domain: Literal["healthcare", "legal", "finance", "hr", "general", "unknown"] = "unknown"

    contains_personal_data: bool = False
    contains_sensitive_data: bool = False
    contains_health_data: bool = False
    contains_sensitive_health_data: bool = False
    contains_third_party_data: bool = False

    request_type: Literal[
        "general_information",
        "professional_advice",
        "clinical_recommendation",
        "legal_advice",
        "financial_advice",
        "automated_decision",
        "tool_action",
        "unknown",
    ] = "unknown"

    mentions_medication: bool = False
    requires_professional_evaluation: bool = False
    has_urgent_symptoms: bool = False

    legal_basis_confirmed: bool = False
    purpose_confirmed: bool = False
    user_is_minor: bool = False

    external_communication: bool = False
    requires_side_effect: bool = False

    fact_extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    uncertainty_reasons: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class FactExtractionRequest(BaseModel):
    tenant_id: str = "default"
    session_id: str | None = None
    user_id: str | None = None
    user_text: str
    mode: Literal["heuristic", "llm_mock", "openai_compatible"] | None = None
    low_confidence_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    enqueue_human_review_on_fallback: bool = True


class FactExtractionResponse(BaseModel):
    tenant_id: str
    session_id: str | None = None
    user_id: str | None = None

    mode: str
    schema_version: str = "1.0.0"
    facts: NormativeFacts

    valid: bool = True
    confidence: float
    low_confidence_threshold: float

    requires_human_review: bool = False
    fallback_reason: str | None = None
    review_id: str | None = None

    raw_model_output: str | None = None
    validation_errors: list[str] = Field(default_factory=list)


class FactSchemaResponse(BaseModel):
    schema_version: str = "1.0.0"
    json_schema: dict[str, Any]
    instruction: str
