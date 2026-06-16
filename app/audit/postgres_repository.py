from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.audit.masking import mask_payload
from app.audit.models import AuditFilters
from app.audit.repository import AuditRepository
from app.core.models import Phase, Verdict


class PostgresAuditRepository(AuditRepository):
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def _connect(self):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError(
                "psycopg is required for MNP_AUDIT_BACKEND=postgres. Install with: pip install 'psycopg[binary]'"
            ) from exc

        return psycopg.connect(self.dsn, row_factory=dict_row)

    def init_db(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS mnp_evaluations (
                        id TEXT PRIMARY KEY,
                        tenant_id TEXT NOT NULL,
                        session_id TEXT,
                        user_id TEXT,
                        phase TEXT NOT NULL,
                        final_decision TEXT NOT NULL,
                        risk_level TEXT NOT NULL,
                        request_json JSONB NOT NULL,
                        verdict_json JSONB NOT NULL,
                        active_plugins_json JSONB NOT NULL DEFAULT '[]'::jsonb,
                        tenant_config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                        created_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )

                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS mnp_plugin_results (
                        id TEXT PRIMARY KEY,
                        evaluation_id TEXT NOT NULL REFERENCES mnp_evaluations(id) ON DELETE CASCADE,
                        plugin_id TEXT NOT NULL,
                        plugin_version TEXT NOT NULL,
                        decision TEXT NOT NULL,
                        risk_level TEXT NOT NULL,
                        violated_rules_json JSONB NOT NULL,
                        required_changes_json JSONB NOT NULL,
                        explanation TEXT,
                        trace_json JSONB,
                        created_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )

                cur.execute("CREATE INDEX IF NOT EXISTS idx_eval_tenant_created ON mnp_evaluations (tenant_id, created_at DESC)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_eval_session ON mnp_evaluations (session_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_eval_decision ON mnp_evaluations (final_decision)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_eval_risk ON mnp_evaluations (risk_level)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_plugin_eval ON mnp_plugin_results (evaluation_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_plugin_id ON mnp_plugin_results (plugin_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_plugin_rules_gin ON mnp_plugin_results USING GIN (violated_rules_json)")
            conn.commit()

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
        evaluation_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)

        masked_request = mask_payload(request_payload)
        masked_verdict = mask_payload(verdict.model_dump(mode="json"))

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO mnp_evaluations (
                        id, tenant_id, session_id, user_id, phase,
                        final_decision, risk_level, request_json, verdict_json,
                        active_plugins_json, tenant_config_json, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s)
                    """,
                    (
                        evaluation_id,
                        tenant_id,
                        session_id,
                        user_id,
                        phase.value,
                        verdict.decision.value,
                        verdict.risk_level.value,
                        json.dumps(masked_request, ensure_ascii=False),
                        json.dumps(masked_verdict, ensure_ascii=False),
                        json.dumps(active_plugins or [], ensure_ascii=False),
                        json.dumps(tenant_config or {}, ensure_ascii=False),
                        created_at,
                    ),
                )

                for item in verdict.trace:
                    if not isinstance(item, dict):
                        continue

                    cur.execute(
                        """
                        INSERT INTO mnp_plugin_results (
                            id, evaluation_id, plugin_id, plugin_version, decision,
                            risk_level, violated_rules_json, required_changes_json,
                            explanation, trace_json, created_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s::jsonb, %s)
                        """,
                        (
                            str(uuid.uuid4()),
                            evaluation_id,
                            item.get("plugin_id", "unknown"),
                            item.get("plugin_version", "unknown"),
                            item.get("decision", "allow"),
                            item.get("risk_level", "low"),
                            json.dumps(item.get("violated_rules", []), ensure_ascii=False),
                            json.dumps(item.get("required_changes", []), ensure_ascii=False),
                            item.get("explanation", ""),
                            json.dumps(mask_payload(item.get("trace", [])), ensure_ascii=False),
                            created_at,
                        ),
                    )
            conn.commit()

        return evaluation_id

    def get_evaluation(self, evaluation_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM mnp_evaluations WHERE id = %s", (evaluation_id,))
                evaluation = cur.fetchone()
                if evaluation is None:
                    return None

                cur.execute(
                    "SELECT * FROM mnp_plugin_results WHERE evaluation_id = %s ORDER BY created_at ASC",
                    (evaluation_id,),
                )
                plugin_rows = cur.fetchall()

        evaluation["plugin_results"] = plugin_rows
        return evaluation

    def list_evaluations(self, filters: AuditFilters) -> dict[str, Any]:
        where = []
        params: list[Any] = []

        if filters.tenant_id:
            where.append("tenant_id = %s")
            params.append(filters.tenant_id)
        if filters.session_id:
            where.append("session_id = %s")
            params.append(filters.session_id)
        if filters.user_id:
            where.append("user_id = %s")
            params.append(filters.user_id)
        if filters.decision:
            where.append("final_decision = %s")
            params.append(filters.decision)
        if filters.risk_level:
            where.append("risk_level = %s")
            params.append(filters.risk_level)

        exists_plugin_filter = ""
        if filters.plugin_id:
            exists_plugin_filter += " AND pr.plugin_id = %s"
            params.append(filters.plugin_id)

        if filters.rule_id:
            exists_plugin_filter += " AND pr.violated_rules_json ? %s"
            params.append(filters.rule_id)

        if exists_plugin_filter:
            where.append(
                "EXISTS (SELECT 1 FROM mnp_plugin_results pr WHERE pr.evaluation_id = mnp_evaluations.id"
                + exists_plugin_filter
                + ")"
            )

        where_sql = " WHERE " + " AND ".join(where) if where else ""

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS c FROM mnp_evaluations" + where_sql, params)
                total = cur.fetchone()["c"]

                cur.execute(
                    "SELECT id, tenant_id, session_id, user_id, phase, final_decision, risk_level, active_plugins_json, created_at "
                    "FROM mnp_evaluations"
                    + where_sql
                    + " ORDER BY created_at DESC LIMIT %s OFFSET %s",
                    params + [filters.limit, filters.offset],
                )
                rows = cur.fetchall()

        return {
            "total": total,
            "limit": filters.limit,
            "offset": filters.offset,
            "items": [
                {
                    "id": row["id"],
                    "tenant_id": row["tenant_id"],
                    "session_id": row["session_id"],
                    "user_id": row["user_id"],
                    "phase": row["phase"],
                    "final_decision": row["final_decision"],
                    "risk_level": row["risk_level"],
                    "active_plugins": row["active_plugins_json"],
                    "created_at": row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") else row["created_at"],
                }
                for row in rows
            ],
        }

    def metrics_summary(self, tenant_id: str | None = None) -> dict[str, Any]:
        where = " WHERE tenant_id = %s" if tenant_id else ""
        params = [tenant_id] if tenant_id else []

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS c FROM mnp_evaluations" + where, params)
                total = cur.fetchone()["c"]

                cur.execute(
                    "SELECT final_decision AS k, COUNT(*) AS c FROM mnp_evaluations"
                    + where
                    + " GROUP BY final_decision ORDER BY c DESC",
                    params,
                )
                by_decision = cur.fetchall()

                cur.execute(
                    "SELECT risk_level AS k, COUNT(*) AS c FROM mnp_evaluations"
                    + where
                    + " GROUP BY risk_level ORDER BY c DESC",
                    params,
                )
                by_risk = cur.fetchall()

                cur.execute(
                    "SELECT tenant_id AS k, COUNT(*) AS c FROM mnp_evaluations GROUP BY tenant_id ORDER BY c DESC LIMIT 20"
                )
                by_tenant = cur.fetchall()

        return {
            "tenant_id": tenant_id,
            "total_evaluations": total,
            "by_decision": {row["k"]: row["c"] for row in by_decision},
            "by_risk_level": {row["k"]: row["c"] for row in by_risk},
            "by_tenant": {row["k"]: row["c"] for row in by_tenant},
        }

    def metrics_rules(self, tenant_id: str | None = None, limit: int = 20) -> dict[str, Any]:
        where = " WHERE e.tenant_id = %s" if tenant_id else ""
        params = [tenant_id] if tenant_id else []

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT rule_id, COUNT(*) AS count
                    FROM (
                      SELECT jsonb_array_elements_text(pr.violated_rules_json) AS rule_id
                      FROM mnp_plugin_results pr
                      JOIN mnp_evaluations e ON e.id = pr.evaluation_id
                    """
                    + where
                    + """
                    ) x
                    GROUP BY rule_id
                    ORDER BY count DESC
                    LIMIT %s
                    """,
                    params + [limit],
                )
                rows = cur.fetchall()

        return {
            "tenant_id": tenant_id,
            "rules": [{"rule_id": row["rule_id"], "count": row["count"]} for row in rows],
        }

    def metrics_plugins(self, tenant_id: str | None = None, limit: int = 20) -> dict[str, Any]:
        where = " WHERE e.tenant_id = %s" if tenant_id else ""
        params = [tenant_id] if tenant_id else []

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT pr.plugin_id, pr.plugin_version, pr.decision, pr.risk_level, COUNT(*) AS c
                    FROM mnp_plugin_results pr
                    JOIN mnp_evaluations e ON e.id = pr.evaluation_id
                    """
                    + where
                    + """
                    GROUP BY pr.plugin_id, pr.plugin_version, pr.decision, pr.risk_level
                    ORDER BY c DESC
                    LIMIT %s
                    """,
                    params + [limit],
                )
                rows = cur.fetchall()

        return {
            "tenant_id": tenant_id,
            "plugins": [dict(row) for row in rows],
        }
