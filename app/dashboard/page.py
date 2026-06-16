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


DASHBOARD_HTML = """
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>MNP Operational Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    :root {
      --bg: #0f172a;
      --panel: #111827;
      --panel2: #1f2937;
      --text: #e5e7eb;
      --muted: #9ca3af;
      --border: #374151;
      --accent: #60a5fa;
      --ok: #34d399;
      --warn: #fbbf24;
      --bad: #f87171;
      --purple: #c084fc;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: linear-gradient(180deg, #020617 0%, var(--bg) 100%);
      color: var(--text);
    }
    header {
      padding: 24px 32px;
      border-bottom: 1px solid var(--border);
      background: rgba(15, 23, 42, 0.92);
      position: sticky;
      top: 0;
      z-index: 5;
      backdrop-filter: blur(10px);
    }
    header h1 {
      margin: 0;
      font-size: 24px;
      letter-spacing: -0.02em;
    }
    header p {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 14px;
    }
    main {
      padding: 24px 32px 40px;
      max-width: 1500px;
      margin: 0 auto;
    }
    .toolbar {
      display: grid;
      grid-template-columns: repeat(6, minmax(120px, 1fr));
      gap: 12px;
      padding: 16px;
      border: 1px solid var(--border);
      border-radius: 16px;
      background: rgba(17, 24, 39, 0.76);
      margin-bottom: 20px;
    }
    label {
      display: block;
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 6px;
    }
    input, select, button {
      width: 100%;
      border: 1px solid var(--border);
      background: #020617;
      color: var(--text);
      padding: 10px 12px;
      border-radius: 10px;
      font-size: 14px;
    }
    button {
      cursor: pointer;
      background: var(--accent);
      color: #00111f;
      border: none;
      font-weight: 700;
    }
    button.secondary {
      background: #334155;
      color: var(--text);
    }
    .grid {
      display: grid;
      gap: 16px;
    }
    .cards {
      grid-template-columns: repeat(5, minmax(140px, 1fr));
      margin-bottom: 16px;
    }
    .two {
      grid-template-columns: 1fr 1fr;
      margin-bottom: 16px;
    }
    .panel {
      border: 1px solid var(--border);
      border-radius: 16px;
      background: rgba(17, 24, 39, 0.82);
      overflow: hidden;
    }
    .panel h2 {
      margin: 0;
      padding: 14px 16px;
      font-size: 15px;
      border-bottom: 1px solid var(--border);
      background: rgba(31, 41, 55, 0.72);
    }
    .card {
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 16px;
      background: rgba(17, 24, 39, 0.82);
    }
    .card .label {
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 8px;
    }
    .card .value {
      font-size: 28px;
      font-weight: 800;
      letter-spacing: -0.04em;
    }
    .card small {
      color: var(--muted);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th, td {
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }
    th {
      color: var(--muted);
      text-align: left;
      font-weight: 600;
      background: rgba(2, 6, 23, 0.35);
    }
    tr:hover td {
      background: rgba(96, 165, 250, 0.05);
    }
    .badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }
    .allow { background: rgba(52, 211, 153, 0.15); color: var(--ok); }
    .modify { background: rgba(251, 191, 36, 0.15); color: var(--warn); }
    .escalate { background: rgba(192, 132, 252, 0.15); color: var(--purple); }
    .block { background: rgba(248, 113, 113, 0.15); color: var(--bad); }
    .low { color: var(--ok); }
    .medium { color: var(--warn); }
    .high, .critical { color: var(--bad); }
    .muted { color: var(--muted); }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
    .error {
      display: none;
      margin-bottom: 16px;
      padding: 12px 14px;
      border-radius: 12px;
      background: rgba(248, 113, 113, 0.12);
      border: 1px solid rgba(248, 113, 113, 0.35);
      color: #fecaca;
    }
    .empty {
      padding: 16px;
      color: var(--muted);
    }
    @media (max-width: 1100px) {
      .toolbar { grid-template-columns: 1fr 1fr; }
      .cards { grid-template-columns: 1fr 1fr; }
      .two { grid-template-columns: 1fr; }
    }
    @media (max-width: 640px) {
      header, main { padding-left: 16px; padding-right: 16px; }
      .toolbar, .cards { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
<header>
  <h1>MNP Operational Dashboard</h1>
  <p>Auditoria, métricas, regras violadas, plugins e fila de revisão humana do Middleware Normativo Pluggable.</p>
</header>

<main>
  <div id="error" class="error"></div>

  <section class="toolbar">
    <div>
      <label>Tenant</label>
      <input id="tenant" placeholder="clinic-demo" value="clinic-demo" />
    </div>
    <div>
      <label>Decisão</label>
      <select id="decision">
        <option value="">Todas</option>
        <option value="allow">allow</option>
        <option value="modify">modify</option>
        <option value="escalate">escalate</option>
        <option value="block">block</option>
      </select>
    </div>
    <div>
      <label>Risco</label>
      <select id="risk">
        <option value="">Todos</option>
        <option value="low">low</option>
        <option value="medium">medium</option>
        <option value="high">high</option>
        <option value="critical">critical</option>
      </select>
    </div>
    <div>
      <label>Sessão</label>
      <input id="session" placeholder="session_id" />
    </div>
    <div>
      <label>Regra</label>
      <input id="rule" placeholder="rule_id" />
    </div>
    <div style="display:flex; gap:8px; align-items:end;">
      <button onclick="loadDashboard()">Atualizar</button>
    </div>
  </section>

  <section class="grid cards">
    <div class="card">
      <div class="label">Avaliações</div>
      <div id="total" class="value">—</div>
      <small>Total filtrado por tenant</small>
    </div>
    <div class="card">
      <div class="label">Allow</div>
      <div id="allow" class="value low">—</div>
      <small>Permitidas</small>
    </div>
    <div class="card">
      <div class="label">Modify</div>
      <div id="modify" class="value medium">—</div>
      <small>Exigem alteração</small>
    </div>
    <div class="card">
      <div class="label">Escalate</div>
      <div id="escalate" class="value">—</div>
      <small>Revisão humana</small>
    </div>
    <div class="card">
      <div class="label">Block</div>
      <div id="block" class="value high">—</div>
      <small>Bloqueadas</small>
    </div>
  </section>

  <section class="grid two">
    <div class="panel">
      <h2>Regras mais acionadas</h2>
      <div id="rules"></div>
    </div>
    <div class="panel">
      <h2>Plugins mais acionados</h2>
      <div id="plugins"></div>
    </div>
  </section>

  <section class="panel" style="margin-bottom:16px;">
    <h2>Avaliações recentes</h2>
    <div id="audit"></div>
  </section>

  <section class="panel">
    <h2>Fila de revisão humana</h2>
    <div id="reviews"></div>
  </section>
</main>

<script>
function qs(params) {
  const out = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && String(v).trim() !== "") out.set(k, v);
  });
  return out.toString();
}

function badgeDecision(v) {
  return `<span class="badge ${v}">${v || "—"}</span>`;
}

function risk(v) {
  return `<span class="${v}">${v || "—"}</span>`;
}

function setError(message) {
  const el = document.getElementById("error");
  if (!message) {
    el.style.display = "none";
    el.textContent = "";
  } else {
    el.style.display = "block";
    el.textContent = message;
  }
}

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url} -> HTTP ${response.status}`);
  return await response.json();
}

function renderTable(targetId, columns, rows, emptyMessage = "Sem dados.") {
  const target = document.getElementById(targetId);
  if (!rows || rows.length === 0) {
    target.innerHTML = `<div class="empty">${emptyMessage}</div>`;
    return;
  }
  const head = columns.map(c => `<th>${c.label}</th>`).join("");
  const body = rows.map(row => {
    const cells = columns.map(c => `<td>${c.render ? c.render(row) : (row[c.key] ?? "—")}</td>`).join("");
    return `<tr>${cells}</tr>`;
  }).join("");
  target.innerHTML = `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

async function loadDashboard() {
  setError(null);
  const tenant = document.getElementById("tenant").value.trim();
  const decision = document.getElementById("decision").value;
  const riskValue = document.getElementById("risk").value;
  const session = document.getElementById("session").value.trim();
  const rule = document.getElementById("rule").value.trim();

  try {
    const summaryParams = qs({ tenant_id: tenant });
    const auditParams = qs({
      tenant_id: tenant,
      decision: decision,
      risk_level: riskValue,
      session_id: session,
      rule_id: rule,
      limit: 25
    });

    const [summary, rules, plugins, audit, reviews] = await Promise.all([
      getJson(`/metrics/summary?${summaryParams}`),
      getJson(`/metrics/rules?${qs({ tenant_id: tenant, limit: 10 })}`),
      getJson(`/metrics/plugins?${qs({ tenant_id: tenant, limit: 10 })}`),
      getJson(`/audit?${auditParams}`),
      getJson(`/human-review/pending?limit=10`)
    ]);

    const byDecision = summary.by_decision || {};
    document.getElementById("total").textContent = summary.total_evaluations ?? 0;
    document.getElementById("allow").textContent = byDecision.allow ?? 0;
    document.getElementById("modify").textContent = byDecision.modify ?? 0;
    document.getElementById("escalate").textContent = byDecision.escalate ?? 0;
    document.getElementById("block").textContent = byDecision.block ?? 0;

    renderTable("rules", [
      { label: "Regra", key: "rule_id", render: r => `<span class="mono">${r.rule_id}</span>` },
      { label: "Ocorrências", key: "count" }
    ], rules.rules || [], "Nenhuma regra acionada.");

    renderTable("plugins", [
      { label: "Plugin", key: "plugin_id", render: r => `<span class="mono">${r.plugin_id}</span>` },
      { label: "Versão", key: "plugin_version", render: r => `<span class="mono">${r.plugin_version}</span>` },
      { label: "Decisão", key: "decision", render: r => badgeDecision(r.decision) },
      { label: "Risco", key: "risk_level", render: r => risk(r.risk_level) },
      { label: "Qtd.", key: "c" }
    ], plugins.plugins || [], "Nenhum plugin acionado.");

    renderTable("audit", [
      { label: "Quando", key: "created_at", render: r => `<span class="mono">${String(r.created_at).replace("T", " ").slice(0, 19)}</span>` },
      { label: "Tenant", key: "tenant_id", render: r => `<span class="mono">${r.tenant_id}</span>` },
      { label: "Sessão", key: "session_id", render: r => `<span class="mono">${r.session_id || "—"}</span>` },
      { label: "Fase", key: "phase" },
      { label: "Decisão", key: "final_decision", render: r => badgeDecision(r.final_decision) },
      { label: "Risco", key: "risk_level", render: r => risk(r.risk_level) },
      { label: "Plugins", key: "active_plugins", render: r => `<span class="mono">${(r.active_plugins || []).join(", ")}</span>` },
      { label: "ID", key: "id", render: r => `<a class="mono muted" href="/audit/${r.id}" target="_blank">${String(r.id).slice(0, 8)}…</a>` }
    ], audit.items || [], "Nenhuma avaliação encontrada.");

    renderTable("reviews", [
      { label: "Criado em", key: "created_at", render: r => `<span class="mono">${String(r.created_at).replace("T", " ").slice(0, 19)}</span>` },
      { label: "Motivo", key: "reason", render: r => `<span class="mono">${r.reason}</span>` },
      { label: "Tenant", key: "payload", render: r => `<span class="mono">${r.payload?.tenant_id || "—"}</span>` },
      { label: "Sessão", key: "payload", render: r => `<span class="mono">${r.payload?.session_id || "—"}</span>` },
      { label: "Confiança", key: "payload", render: r => r.payload?.confidence ?? "—" },
      { label: "ID", key: "review_id", render: r => `<a class="mono muted" href="/human-review/${r.review_id}" target="_blank">${String(r.review_id).slice(0, 8)}…</a>` }
    ], reviews.items || [], "Nenhum item pendente.");
  } catch (err) {
    console.error(err);
    setError(err.message || String(err));
  }
}

loadDashboard();
</script>
</body>
</html>
"""
