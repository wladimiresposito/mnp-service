from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class HumanReviewRecord(BaseModel):
    review_id: str
    status: Literal["pending", "resolved"] = "pending"
    reason: str
    payload: dict[str, Any] = Field(default_factory=dict)
    resolution: dict[str, Any] | None = None
    created_at: str
    resolved_at: str | None = None


class ResolveHumanReviewRequest(BaseModel):
    resolution: dict[str, Any] = Field(default_factory=dict)
