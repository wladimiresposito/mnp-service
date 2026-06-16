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
