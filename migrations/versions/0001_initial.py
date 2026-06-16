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

"""initial schema: mnp_evaluations and mnp_plugin_results

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-14

Equivale ao app/audit/postgres_schema.sql, agora versionado. A partir
daqui, mudancas de esquema entram como novas revisoes, nao como edicao
do .sql solto.
"""
from __future__ import annotations

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
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
        );
        """
    )
    op.execute(
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
        );
        """
    )
    for stmt in (
        "CREATE INDEX IF NOT EXISTS idx_eval_tenant_created ON mnp_evaluations (tenant_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_eval_session ON mnp_evaluations (session_id)",
        "CREATE INDEX IF NOT EXISTS idx_eval_decision ON mnp_evaluations (final_decision)",
        "CREATE INDEX IF NOT EXISTS idx_eval_risk ON mnp_evaluations (risk_level)",
        "CREATE INDEX IF NOT EXISTS idx_plugin_eval ON mnp_plugin_results (evaluation_id)",
        "CREATE INDEX IF NOT EXISTS idx_plugin_id ON mnp_plugin_results (plugin_id)",
        "CREATE INDEX IF NOT EXISTS idx_plugin_rules_gin ON mnp_plugin_results USING GIN (violated_rules_json)",
    ):
        op.execute(stmt)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS mnp_plugin_results")
    op.execute("DROP TABLE IF EXISTS mnp_evaluations")
