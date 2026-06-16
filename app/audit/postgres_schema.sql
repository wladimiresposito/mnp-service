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

CREATE INDEX IF NOT EXISTS idx_eval_tenant_created ON mnp_evaluations (tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_eval_session ON mnp_evaluations (session_id);
CREATE INDEX IF NOT EXISTS idx_eval_decision ON mnp_evaluations (final_decision);
CREATE INDEX IF NOT EXISTS idx_eval_risk ON mnp_evaluations (risk_level);
CREATE INDEX IF NOT EXISTS idx_plugin_eval ON mnp_plugin_results (evaluation_id);
CREATE INDEX IF NOT EXISTS idx_plugin_id ON mnp_plugin_results (plugin_id);
CREATE INDEX IF NOT EXISTS idx_plugin_rules_gin ON mnp_plugin_results USING GIN (violated_rules_json);
