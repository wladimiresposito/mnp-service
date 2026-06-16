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

from abc import ABC, abstractmethod
from typing import Any

from app.audit.models import AuditFilters
from app.core.models import Phase, Verdict


class AuditRepository(ABC):
    @abstractmethod
    def init_db(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def save_evaluation(
        self,
        tenant_id: str,
        session_id: str | None,
        user_id: str | None,
        phase: Phase,
        request_payload: dict[str, Any],
        verdict: Verdict,
        active_plugins: list[str] | None = None,
        tenant_config: dict[str, Any] | None = None,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_evaluation(self, evaluation_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_evaluations(self, filters: AuditFilters) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def metrics_summary(self, tenant_id: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def metrics_rules(self, tenant_id: str | None = None, limit: int = 20) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def metrics_plugins(self, tenant_id: str | None = None, limit: int = 20) -> dict[str, Any]:
        raise NotImplementedError
