from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class TemporalEvent(BaseModel):
    t: int
    kind: str
    subject: str
    purpose: str


class TemporalAspInput(BaseModel):
    subject: str
    purpose: str = "process_health_data_for_pre_anamnesis"
    current_time: int = 100
    sensitive_health_data: bool = True
    events: list[TemporalEvent] = Field(default_factory=list)


class TemporalAspResult(BaseModel):
    engine: str
    clingo_available: bool
    allowed: bool
    active_consent: bool
    forbidden: bool
    required_changes: list[str] = Field(default_factory=list)
    answer_set: list[str] = Field(default_factory=list)
    trace: dict[str, Any] = Field(default_factory=dict)
