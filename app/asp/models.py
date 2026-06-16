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
