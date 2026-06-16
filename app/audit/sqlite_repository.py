from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.audit.masking import mask_payload
from app.audit.models import AuditFilters
from app.audit.repository import AuditRepository
from app.core.models import Phase, Verdict


class SQLiteAuditRepository(AuditRepository):
    def __init__(self, sqlite_path: str) -> None:
        self.sqlite_path = sqlite_path

    def _connect(self) -> sqlite3.Connection:
        path = Path(self.sqlite_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
        columns = [row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in columns:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")

    def init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mnp_evaluations (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    session_id TEXT,
                    user_id TEXT,
                    phase TEXT NOT NULL,
                    final_decision TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    verdict_json TEXT NOT NULL,
                    active_plugins_json TEXT NOT NULL DEFAULT '[]',
                    tenant_config_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                )
                """
            )

            self._ensure_column(conn, "mnp_evaluations", "active_plugins_json", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column(conn, "mnp_evaluations", "tenant_config_json", "TEXT NOT NULL DEFAULT '{}'")

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mnp_plugin_results (
                    id TEXT PRIMARY KEY,
                    evaluation_id TEXT NOT NULL,
                    plugin_id TEXT NOT NULL,
                    plugin_version TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    violated_rules_json TEXT NOT NULL,
                    required_changes_json TEXT NOT NULL,
                    explanation TEXT,
                    trace_json TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )

            conn.execute("CREATE INDEX IF NOT EXISTS idx_eval_tenant_created ON mnp_evaluations (tenant_id, created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_eval_session ON mnp_evaluations (session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_eval_decision ON mnp_evaluations (final_decision)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_plugin_eval ON mnp_plugin_results (evaluation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_plugin_id ON mnp_plugin_results (plugin_id)")

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
        created_at = datetime.now(timezone.utc).isoformat()

        masked_request = mask_payload(request_payload)
        masked_verdict = mask_payload(verdict.model_dump(mode="json"))

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO mnp_evaluations (
                    id, tenant_id, session_id, user_id, phase,
                    final_decision, risk_level, request_json, verdict_json,
                    active_plugins_json, tenant_config_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

                conn.execute(
                    """
                    INSERT INTO mnp_plugin_results (
                        id, evaluation_id, plugin_id, plugin_version, decision,
                        risk_level, violated_rules_json, required_changes_json,
                        explanation, trace_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            evaluation = conn.execute(
                "SELECT * FROM mnp_evaluations WHERE id = ?",
                (evaluation_id,),
            ).fetchone()

            if evaluation is None:
                return None

            plugin_rows = conn.execute(
                "SELECT * FROM mnp_plugin_results WHERE evaluation_id = ? ORDER BY created_at ASC",
                (evaluation_id,),
            ).fetchall()

        return self._hydrate_evaluation(dict(evaluation), [dict(row) for row in plugin_rows])

    def list_evaluations(self, filters: AuditFilters) -> dict[str, Any]:
        where = []
        params: list[Any] = []

        if filters.tenant_id:
            where.append("tenant_id = ?")
            params.append(filters.tenant_id)
        if filters.session_id:
            where.append("session_id = ?")
            params.append(filters.session_id)
        if filters.user_id:
            where.append("user_id = ?")
            params.append(filters.user_id)
        if filters.decision:
            where.append("final_decision = ?")
            params.append(filters.decision)
        if filters.risk_level:
            where.append("risk_level = ?")
            params.append(filters.risk_level)

        exists_plugin_filter = ""
        if filters.plugin_id:
            exists_plugin_filter += " AND pr.plugin_id = ?"
            params.append(filters.plugin_id)

        if filters.rule_id:
            exists_plugin_filter += " AND pr.violated_rules_json LIKE ?"
            params.append(f"%{filters.rule_id}%")

        if exists_plugin_filter:
            where.append(
                "EXISTS (SELECT 1 FROM mnp_plugin_results pr WHERE pr.evaluation_id = mnp_evaluations.id"
                + exists_plugin_filter
                + ")"
            )

        where_sql = " WHERE " + " AND ".join(where) if where else ""

        with self._connect() as conn:
            total = conn.execute(
                "SELECT COUNT(*) AS c FROM mnp_evaluations" + where_sql,
                params,
            ).fetchone()["c"]

            rows = conn.execute(
                "SELECT * FROM mnp_evaluations"
                + where_sql
                + " ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params + [filters.limit, filters.offset],
            ).fetchall()

        items = []
        for row in rows:
            data = dict(row)
            items.append({
                "id": data["id"],
                "tenant_id": data["tenant_id"],
                "session_id": data["session_id"],
                "user_id": data["user_id"],
                "phase": data["phase"],
                "final_decision": data["final_decision"],
                "risk_level": data["risk_level"],
                "active_plugins": json.loads(data.get("active_plugins_json") or "[]"),
                "created_at": data["created_at"],
            })

        return {
            "total": total,
            "limit": filters.limit,
            "offset": filters.offset,
            "items": items,
        }

    def metrics_summary(self, tenant_id: str | None = None) -> dict[str, Any]:
        where = " WHERE tenant_id = ?" if tenant_id else ""
        params = [tenant_id] if tenant_id else []

        with self._connect() as conn:
            total = conn.execute(
                "SELECT COUNT(*) AS c FROM mnp_evaluations" + where,
                params,
            ).fetchone()["c"]

            by_decision = conn.execute(
                "SELECT final_decision AS k, COUNT(*) AS c FROM mnp_evaluations"
                + where
                + " GROUP BY final_decision ORDER BY c DESC",
                params,
            ).fetchall()

            by_risk = conn.execute(
                "SELECT risk_level AS k, COUNT(*) AS c FROM mnp_evaluations"
                + where
                + " GROUP BY risk_level ORDER BY c DESC",
                params,
            ).fetchall()

            by_tenant = conn.execute(
                "SELECT tenant_id AS k, COUNT(*) AS c FROM mnp_evaluations GROUP BY tenant_id ORDER BY c DESC LIMIT 20"
            ).fetchall()

        return {
            "tenant_id": tenant_id,
            "total_evaluations": total,
            "by_decision": {row["k"]: row["c"] for row in by_decision},
            "by_risk_level": {row["k"]: row["c"] for row in by_risk},
            "by_tenant": {row["k"]: row["c"] for row in by_tenant},
        }

    def metrics_rules(self, tenant_id: str | None = None, limit: int = 20) -> dict[str, Any]:
        where = ""
        params: list[Any] = []
        if tenant_id:
            where = " WHERE e.tenant_id = ?"
            params.append(tenant_id)

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT pr.violated_rules_json
                FROM mnp_plugin_results pr
                JOIN mnp_evaluations e ON e.id = pr.evaluation_id
                """
                + where,
                params,
            ).fetchall()

        counts: dict[str, int] = {}
        for row in rows:
            for rule in json.loads(row["violated_rules_json"] or "[]"):
                counts[rule] = counts.get(rule, 0) + 1

        ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]
        return {
            "tenant_id": tenant_id,
            "rules": [{"rule_id": rule, "count": count} for rule, count in ranked],
        }

    def metrics_plugins(self, tenant_id: str | None = None, limit: int = 20) -> dict[str, Any]:
        where = ""
        params: list[Any] = []
        if tenant_id:
            where = " WHERE e.tenant_id = ?"
            params.append(tenant_id)

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT pr.plugin_id, pr.plugin_version, pr.decision, pr.risk_level, COUNT(*) AS c
                FROM mnp_plugin_results pr
                JOIN mnp_evaluations e ON e.id = pr.evaluation_id
                """
                + where
                + """
                GROUP BY pr.plugin_id, pr.plugin_version, pr.decision, pr.risk_level
                ORDER BY c DESC
                LIMIT ?
                """,
                params + [limit],
            ).fetchall()

        return {
            "tenant_id": tenant_id,
            "plugins": [dict(row) for row in rows],
        }

    def _hydrate_evaluation(self, evaluation: dict[str, Any], plugin_rows: list[dict[str, Any]]) -> dict[str, Any]:
        evaluation["request_json"] = json.loads(evaluation["request_json"])
        evaluation["verdict_json"] = json.loads(evaluation["verdict_json"])
        evaluation["active_plugins_json"] = json.loads(evaluation.get("active_plugins_json") or "[]")
        evaluation["tenant_config_json"] = json.loads(evaluation.get("tenant_config_json") or "{}")
        evaluation["plugin_results"] = plugin_rows

        for row in evaluation["plugin_results"]:
            row["violated_rules_json"] = json.loads(row["violated_rules_json"])
            row["required_changes_json"] = json.loads(row["required_changes_json"])
            row["trace_json"] = json.loads(row["trace_json"])

        return evaluation
