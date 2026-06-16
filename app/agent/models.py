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

from app.core.models import ActionPlan, DraftAnswer, ToolCall, Verdict
from app.extraction.models import FactExtractionResponse
from app.rag.models import RAGSearchResult


class AgentChatRequest(BaseModel):
    tenant_id: str = "default"
    session_id: str | None = None
    user_id: str | None = None
    user_text: str

    extract_mode: Literal["heuristic", "llm_mock", "openai_compatible"] | None = None
    plugins: list[str] | None = None
    top_k: int | None = None

    allow_tool_calls: bool = True
    enqueue_human_review_on_fallback: bool = True


class AgentStep(BaseModel):
    name: str
    status: str
    detail: dict[str, Any] = Field(default_factory=dict)


class AgentChatResponse(BaseModel):
    tenant_id: str
    session_id: str | None = None
    user_id: str | None = None

    user_text: str
    extraction: FactExtractionResponse
    retrieved_context: list[RAGSearchResult] = Field(default_factory=list)
    plan: ActionPlan
    tool_call: ToolCall | None = None
    draft: DraftAnswer
    verdict: Verdict

    final_answer: str
    action_taken: Literal["answered", "modified", "blocked", "escalated"]
    evaluation_id: str | None = None
    review_id: str | None = None
    active_plugins: list[str] = Field(default_factory=list)
    steps: list[AgentStep] = Field(default_factory=list)
