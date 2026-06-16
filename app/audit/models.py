from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AuditFilters:
    tenant_id: str | None = None
    session_id: str | None = None
    user_id: str | None = None
    decision: str | None = None
    risk_level: str | None = None
    plugin_id: str | None = None
    rule_id: str | None = None
    limit: int = 50
    offset: int = 0


@dataclass
class EvaluationRecord:
    id: str
    tenant_id: str
    session_id: str | None
    user_id: str | None
    phase: str
    final_decision: str
    risk_level: str
    request_json: dict[str, Any]
    verdict_json: dict[str, Any]
    active_plugins_json: list[str]
    tenant_config_json: dict[str, Any]
    created_at: str
