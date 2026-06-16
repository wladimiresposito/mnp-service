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
